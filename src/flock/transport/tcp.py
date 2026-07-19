"""TCP Transport implementation for Flock using asyncio streams."""

import asyncio
import structlog
from typing import Any, Callable, Awaitable, Dict, Optional, List
from flock.types import NodeInfo
from flock.interfaces.transport import Transport
from flock.exceptions import TransportError
from flock.protocol.packet import Packet, HEADER_SIZE

logger = structlog.get_logger()

class TcpTransport(Transport):
    """Asynchronous TCP transport layer implementing core connection handling and routing."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._server: Optional[asyncio.Server] = None
        self._handlers: List[Callable[[NodeInfo, Any], Awaitable[None]]] = []
        self._active_connections: Dict[str, asyncio.StreamWriter] = {}
        self._running = False

    async def start(self) -> None:
        """Start listening for TCP connections on the configured address."""
        if self._running:
            return
        
        try:
            self._server = await asyncio.start_server(
                self._handle_client,
                self.host,
                self.port
            )
            self._running = True
            logger.info("TCP Transport started", host=self.host, port=self.port)
        except Exception as err:
            raise TransportError(f"Failed to start TCP server on {self.host}:{self.port}: {err}") from err

    async def stop(self) -> None:
        """Stop server and clean up connections."""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        
        for writer in list(self._active_connections.values()):
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
        self._active_connections.clear()
        logger.info("TCP Transport stopped")

    async def send(self, target: NodeInfo, message: Any) -> None:
        """Send raw data to a target NodeInfo. Expects message to be binary (packed Packet)."""
        if not isinstance(message, bytes):
            raise TransportError("TcpTransport requires message payloads to be pre-serialized to bytes.")
        
        reader = None
        writer = None
        try:
            reader, writer = await asyncio.open_connection(target.host, target.port)
            writer.write(message)
            await writer.drain()
        except Exception as err:
            raise TransportError(f"Failed to send data to {target.host}:{target.port}: {err}") from err
        finally:
            if writer:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass

    def register_handler(self, handler: Callable[[NodeInfo, Any], Awaitable[None]]) -> None:
        """Register dynamic incoming network packet handler."""
        self._handlers.append(handler)

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Asynchronously read client streams, process network frames, and pass payload to handlers."""
        peer_addr = writer.get_extra_info("peername")
        logger.debug("Received new client connection", peer=peer_addr)

        try:
            while self._running:
                header_data = await reader.readexactly(HEADER_SIZE)
                msg_type, payload_size = Packet.unpack_header(header_data)
                
                payload_data = await reader.readexactly(payload_size)
                
                # Mock NodeInfo from peer address context
                sender = NodeInfo(
                    node_id=f"peer-{peer_addr[0]}:{peer_addr[1]}",
                    host=peer_addr[0],
                    port=peer_addr[1]
                )

                # Route to handlers
                raw_frame = header_data + payload_data
                for handler in self._handlers:
                    try:
                        await handler(sender, raw_frame)
                    except Exception as handler_err:
                        logger.error("Handler error processing payload", error=handler_err)
        except asyncio.IncompleteReadError:
            # Clean connection termination by peer
            pass
        except Exception as err:
            logger.error("TCP Transport connection handler error", error=err)
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
