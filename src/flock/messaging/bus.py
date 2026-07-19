"""Messaging Core Bus coordinating serialization, middleware pipelines, and request-response tracking."""

import asyncio
import structlog
from typing import Dict, Any, List, Optional, Callable, Awaitable
from flock.types import NodeInfo
from flock.interfaces.transport import Transport
from flock.interfaces.serializer import Serializer
from flock.protocol.packet import Packet
from flock.messaging.models import MessageContext, MessageMetadata
from flock.messaging.router import MessageRouter
from flock.messaging.middleware import Middleware
from flock.messaging.exceptions import MessagingError, TimeoutError

logger = structlog.get_logger()

class MessageBus:
    """Core pipeline coordinating network routing, middleware stack execution, and RPC calls."""

    def __init__(self, transport: Transport, serializer: Serializer) -> None:
        self.transport = transport
        self.serializer = serializer
        self.router = MessageRouter()
        self._middleware: List[Middleware] = []
        self._pending_requests: Dict[str, asyncio.Future[Any]] = {}
        
        # Wire callback to transport
        self.transport.register_handler(self._on_packet_received)

    def add_middleware(self, middleware: Middleware) -> None:
        """Append a middleware interceptor into the execution pipeline."""
        self._middleware.append(middleware)

    async def send(self, target: NodeInfo, message_type: int, payload: Any, metadata: Optional[MessageMetadata] = None) -> None:
        """One-way fire-and-forget message dispatch to peer."""
        if metadata is None:
            metadata = MessageMetadata()

        serialized_payload = self.serializer.serialize(payload)
        packet = Packet(message_type=message_type, payload=serialized_payload)
        
        # Serialize overall envelope with standard packet wrapping metadata
        # To avoid double-serializer, envelope packing converts to bytes directly
        envelope = {
            "metadata": {
                "message_id": metadata.message_id,
                "correlation_id": metadata.correlation_id,
                "request_id": metadata.request_id,
                "timestamp": metadata.timestamp,
                "custom": metadata.custom
            },
            "body": payload
        }
        raw_payload = self.serializer.serialize(envelope)
        packet = Packet(message_type=message_type, payload=raw_payload)
        await self.transport.send(target, packet.pack())

    async def request(
        self,
        target: NodeInfo,
        message_type: int,
        payload: Any,
        timeout: float = 5.0,
        metadata: Optional[MessageMetadata] = None
    ) -> Any:
        """Synchronous request-response RPC over asynchronous messaging streams."""
        request_id = f"req-{asyncio.get_running_loop().time()}-{id(payload)}"
        if metadata is None:
            metadata = MessageMetadata(request_id=request_id)
        else:
            # Reconstruct with target request_id
            metadata = MessageMetadata(
                message_id=metadata.message_id,
                protocol_version=metadata.protocol_version,
                correlation_id=metadata.correlation_id,
                request_id=request_id,
                timestamp=metadata.timestamp,
                ttl_seconds=metadata.ttl_seconds,
                priority=metadata.priority,
                custom=metadata.custom
            )
        
        future: asyncio.Future[Any] = asyncio.get_running_loop().create_future()
        self._pending_requests[request_id] = future
        
        try:
            await self.send(target, message_type, payload, metadata)
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError as err:
            raise TimeoutError(f"RPC Request timed out after {timeout} seconds") from err
        finally:
            self._pending_requests.pop(request_id, None)

    async def _on_packet_received(self, sender: NodeInfo, data: bytes) -> None:
        """Main inbound callback pipeline triggered by the transport listener."""
        try:
            # The transport returns raw packet bytes containing header + payload
            header_size = 10 # From Packet.HEADER_SIZE
            if len(data) < header_size:
                logger.error("Inbound packet data too short")
                return
            
            header_bytes = data[:header_size]
            payload_bytes = data[header_size:]
            
            message_type, _ = Packet.unpack_header(header_bytes)
            
            envelope = self.serializer.deserialize(payload_bytes)
            meta_dict = envelope.get("metadata", {})
            body = envelope.get("body")
            
            metadata = MessageMetadata(
                message_id=meta_dict.get("message_id"),
                correlation_id=meta_dict.get("correlation_id"),
                request_id=meta_dict.get("request_id"),
                timestamp=meta_dict.get("timestamp", 0.0),
                custom=meta_dict.get("custom", {})
            )
            
            # Check if this resolves a pending RPC request
            if metadata.correlation_id and metadata.correlation_id in self._pending_requests:
                fut = self._pending_requests.get(metadata.correlation_id)
                if fut and not fut.done():
                    fut.set_result(body)
                return

            # Assemble execution context
            context = MessageContext(
                message_type=message_type,
                payload=body,
                metadata=metadata,
                sender=sender
            )

            # Execution chain wrapping registered handler
            async def target_handler(ctx: MessageContext) -> None:
                handler = self.router.get_handler(ctx.message_type)
                await handler.handle(ctx)

            # Build middleware runner pipeline
            async def run_pipeline(idx: int, ctx: MessageContext) -> None:
                if idx < len(self._middleware):
                    async def next_call(c: MessageContext) -> None:
                        await run_pipeline(idx + 1, c)
                    await self._middleware[idx](ctx, next_call)
                else:
                    await target_handler(ctx)

            await run_pipeline(0, context)

            # If message is RPC request, reply back with return values
            if metadata.request_id:
                reply_meta = MessageMetadata(correlation_id=metadata.request_id)
                # Senders of RPC requests are registered with ephemeral ports by the transport.
                # To reply, we target the original node's configuration port which we can extract from metadata or fall back to sender context.
                reply_target = NodeInfo(
                    node_id=sender.node_id,
                    host=sender.host,
                    port=metadata.custom.get("reply_port", sender.port)
                )
                await self.send(reply_target, message_type, context.response_payload, reply_meta)

        except Exception as err:
            logger.error("Error processing inbound message bus pipeline", error=err)
