"""Coordinating Peer Discovery Service logic using transport-independent MessageBus RPC loops."""

import asyncio
import structlog
from typing import Optional, Callable, Awaitable, List, Dict, Any
from flock.types import NodeInfo
from flock.messaging.bus import MessageBus
from flock.messaging.models import MessageContext, MessageMetadata
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.discovery.models import NodeDescription
from flock.discovery.registry import PeerRegistry
from flock.discovery.exceptions import InvalidDiscoveryMessageError

logger = structlog.get_logger()

class DiscoveryState:
    """State constants for the discovery service."""
    UNKNOWN = "UNKNOWN"
    DISCOVERING = "DISCOVERING"
    DISCOVERED = "DISCOVERED"
    LEAVING = "LEAVING"

class DiscoveryService:
    """Orchestrates starting broadcasts, receiving queries, and cataloging peer descriptions."""

    def __init__(
        self,
        node_id: str,
        advertised_host: str,
        advertised_port: int,
        message_bus: MessageBus,
        broadcast_interval_seconds: float = 5.0,
        expiration_seconds: float = 15.0
    ) -> None:
        self.node_id = node_id
        self.host = advertised_host
        self.port = advertised_port
        self.bus = message_bus
        self.broadcast_interval = broadcast_interval_seconds
        
        self.registry = PeerRegistry(expiration_seconds=expiration_seconds)
        self.state = DiscoveryState.UNKNOWN
        self._broadcast_task: Optional[asyncio.Task[None]] = None
        self._running = False
        
        self._peer_discovered_callbacks: List[Callable[[NodeDescription], Awaitable[None]]] = []
        self._peer_expired_callbacks: List[Callable[[str], Awaitable[None]]] = []

        # Wire incoming handlers to MessageBus router
        self.bus.router.register(MessageType.DISCOVERY_REQUEST, _DiscoveryRequestHandler(self))
        self.bus.router.register(MessageType.DISCOVERY_RESPONSE, _DiscoveryResponseHandler(self))
        self.bus.router.register(MessageType.NODE_ANNOUNCE, _NodeAnnounceHandler(self))
        self.bus.router.register(MessageType.NODE_LEAVE, _NodeLeaveHandler(self))

    def register_discovered_callback(self, cb: Callable[[NodeDescription], Awaitable[None]]) -> None:
        """Register callback hook for newly discovered peers."""
        self._peer_discovered_callbacks.append(cb)

    def register_expired_callback(self, cb: Callable[[str], Awaitable[None]]) -> None:
        """Register callback hook for expired/removed nodes."""
        self._peer_expired_callbacks.append(cb)

    async def start(self) -> None:
        """Startup discovery loops, sending announcement to network."""
        if self._running:
            return
        
        self._running = True
        self.state = DiscoveryState.DISCOVERING
        self._broadcast_task = asyncio.create_task(self._broadcast_loop())
        logger.info("Discovery service activated", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop broadcast loop and announce exit departure."""
        self._running = False
        self.state = DiscoveryState.LEAVING
        
        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass

        # Send graceful leave announcement to active peers
        leave_payload = {"node_id": self.node_id}
        for peer in self.registry.list_peers():
            try:
                target = NodeInfo(node_id=peer.node_id, host=peer.host, port=peer.port)
                await self.bus.send(target, MessageType.NODE_LEAVE, leave_payload)
            except Exception as err:
                logger.debug("Failed sending departure signal to peer", peer=peer.node_id, error=err)

        self.state = DiscoveryState.UNKNOWN
        logger.info("Discovery service stopped")

    async def query_target(self, target: NodeInfo) -> None:
        """Manually query a target peer directly for discovery metadata."""
        desc = self.get_self_description()
        payload = {
            "node_id": desc.node_id,
            "host": desc.host,
            "port": desc.port,
            "protocol_version": desc.protocol_version,
            "framework_version": desc.framework_version,
            "startup_timestamp": desc.startup_timestamp,
            "capabilities": desc.capabilities,
            "tags": desc.tags,
            "metadata": desc.metadata
        }
        await self.bus.send(target, MessageType.DISCOVERY_REQUEST, payload)

    def get_self_description(self) -> NodeDescription:
        """Retrieve local self description."""
        return NodeDescription(
            node_id=self.node_id,
            host=self.host,
            port=self.port
        )

    async def _broadcast_loop(self) -> None:
        """Periodically broadcast NODE_ANNOUNCE updates to known peers."""
        while self._running:
            desc = self.get_self_description()
            payload = {
                "node_id": desc.node_id,
                "host": desc.host,
                "port": desc.port,
                "protocol_version": desc.protocol_version,
                "framework_version": desc.framework_version,
                "startup_timestamp": desc.startup_timestamp,
                "capabilities": desc.capabilities,
                "tags": desc.tags,
                "metadata": desc.metadata
            }
            
            # Send node announcements to all registered peers
            for peer in self.registry.list_peers():
                try:
                    target = NodeInfo(node_id=peer.node_id, host=peer.host, port=peer.port)
                    await self.bus.send(target, MessageType.NODE_ANNOUNCE, payload)
                except Exception as err:
                    logger.debug("Announce broadcast error", target=peer.node_id, error=err)

            # Cleanup expired records and invoke trigger callbacks
            expired_ids = self.registry.cleanup_expired()
            for exp_id in expired_ids:
                for cb in self._peer_expired_callbacks:
                    try:
                        await cb(exp_id)
                    except Exception as cb_err:
                        logger.error("Error executing expire callback", error=cb_err)

            await asyncio.sleep(self.broadcast_interval)

    async def _process_inbound_description(self, data: Dict[str, Any]) -> None:
        """Assemble NodeDescription and trigger registration callbacks."""
        try:
            node_id = data["node_id"]
            if node_id == self.node_id:
                # Do not register ourselves
                return
            
            desc = NodeDescription(
                node_id=node_id,
                host=data["host"],
                port=data["port"],
                protocol_version=data.get("protocol_version", 1),
                framework_version=data.get("framework_version", "0.1.0"),
                startup_timestamp=data.get("startup_timestamp", 0.0),
                capabilities=data.get("capabilities", []),
                tags=data.get("tags", {}),
                metadata=data.get("metadata", {})
            )
            
            is_new = self.registry.register(desc)
            if is_new:
                self.state = DiscoveryState.DISCOVERED
                for cb in self._peer_discovered_callbacks:
                    try:
                        await cb(desc)
                    except Exception as cb_err:
                        logger.error("Error executing discover callback", error=cb_err)
        except KeyError as err:
            raise InvalidDiscoveryMessageError(f"Missing mandatory payload key: {err}")


class _DiscoveryRequestHandler(MessageHandler):
    """Answers inbound discovery queries by sending DISCOVERY_RESPONSE."""

    def __init__(self, service: DiscoveryService) -> None:
        self.service = service

    async def handle(self, context: MessageContext) -> None:
        # Register requester details
        await self.service._process_inbound_description(context.payload)
        
        # Respond back with local details
        desc = self.service.get_self_description()
        response_payload = {
            "node_id": desc.node_id,
            "host": desc.host,
            "port": desc.port,
            "protocol_version": desc.protocol_version,
            "framework_version": desc.framework_version,
            "startup_timestamp": desc.startup_timestamp,
            "capabilities": desc.capabilities,
            "tags": desc.tags,
            "metadata": desc.metadata
        }
        
        reply_meta = MessageMetadata(correlation_id=context.metadata.request_id)
        # Senders from other nodes need exact ports mapped if testing locally
        reply_port = context.metadata.custom.get("reply_port", context.sender.port)
        reply_target = NodeInfo(node_id=context.sender.node_id, host=context.sender.host, port=reply_port)
        await self.service.bus.send(reply_target, MessageType.DISCOVERY_RESPONSE, response_payload, reply_meta)


class _DiscoveryResponseHandler(MessageHandler):
    """Processes incoming responses for direct discovery queries."""

    def __init__(self, service: DiscoveryService) -> None:
        self.service = service

    async def handle(self, context: MessageContext) -> None:
        await self.service._process_inbound_description(context.payload)


class _NodeAnnounceHandler(MessageHandler):
    """Handles incoming periodic announcements from remote nodes."""

    def __init__(self, service: DiscoveryService) -> None:
        self.service = service

    async def handle(self, context: MessageContext) -> None:
        await self.service._process_inbound_description(context.payload)


class _NodeLeaveHandler(MessageHandler):
    """Handles graceful exit signals from departing nodes."""

    def __init__(self, service: DiscoveryService) -> None:
        self.service = service

    async def handle(self, context: MessageContext) -> None:
        node_id = context.payload.get("node_id")
        if node_id:
            removed = self.service.registry.unregister(node_id)
            if removed:
                for cb in self.service._peer_expired_callbacks:
                    try:
                        await cb(node_id)
                    except Exception as cb_err:
                        logger.error("Error executing node leave callback", error=cb_err)
