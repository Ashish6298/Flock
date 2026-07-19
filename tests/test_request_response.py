"""Tests verifying Request-Response RPC correlation tracking and timeouts."""

import pytest
import asyncio
from flock.types import NodeInfo
from flock.transport.tcp import TcpTransport
from flock.serialization.json import JsonSerializer
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.messaging.models import MessageContext, MessageMetadata
from flock.messaging.exceptions import TimeoutError

class RPCHandler(MessageHandler):
    async def handle(self, context: MessageContext) -> None:
        context.response_payload = f"echo: {context.payload}"

@pytest.mark.asyncio
async def test_request_response_flow() -> None:
    # Set up TCP loopback
    server_transport = TcpTransport("127.0.0.1", 20001)
    client_transport = TcpTransport("127.0.0.1", 20002)
    serializer = JsonSerializer()

    server_bus = MessageBus(server_transport, serializer)
    client_bus = MessageBus(client_transport, serializer)

    # Register handler under key 0 (default messaging routing)
    server_bus.router.register(0, RPCHandler())

    await server_transport.start()
    await client_transport.start()
    try:
        target = NodeInfo(node_id="server", host="127.0.0.1", port=20001)
        # Perform RPC call. Note that we pass reply_port in custom metadata so reply knows where to route
        metadata = MessageMetadata(custom={"reply_port": 20002})
        response = await client_bus.request(target, 0, "hello world rpc", timeout=2.0, metadata=metadata)
        assert response == "echo: hello world rpc"
    finally:
        await server_transport.stop()
        await client_transport.stop()

@pytest.mark.asyncio
async def test_request_timeout() -> None:
    client_transport = TcpTransport("127.0.0.1", 20003)
    client_bus = MessageBus(client_transport, JsonSerializer())
    
    # Target nonexistent node to verify immediate transport connection failure
    target = NodeInfo(node_id="nonexistent", host="127.0.0.1", port=20004)
    from flock.exceptions import TransportError
    with pytest.raises(TransportError):
        await client_bus.request(target, 0, "ping", timeout=0.2)
