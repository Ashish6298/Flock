"""Integration tests for TCP transport and asynchronous messaging loop."""

import pytest
import asyncio
from flock.types import NodeInfo
from flock.transport.tcp import TcpTransport
from flock.protocol.packet import Packet, MessageType

@pytest.mark.asyncio
async def test_tcp_transport_loopback() -> None:
    """Verify that TcpTransport can listen locally and route packages correctly."""
    server_transport = TcpTransport("127.0.0.1", 18888)
    client_transport = TcpTransport("127.0.0.1", 18889)

    received_payloads = []
    future_received: asyncio.Future[bool] = asyncio.Future()

    async def mock_handler(sender: NodeInfo, payload: bytes) -> None:
        received_payloads.append(payload)
        future_received.set_result(True)

    server_transport.register_handler(mock_handler)
    await server_transport.start()

    try:
        # Create packet to send
        pkt = Packet(message_type=MessageType.GENERIC, payload=b"test tcp delivery payload")
        target_node = NodeInfo(node_id="server-node", host="127.0.0.1", port=18888)
        
        # Send using client transport
        await client_transport.send(target_node, pkt.pack())

        # Wait for delivery
        await asyncio.wait_for(future_received, timeout=2.0)
        assert len(received_payloads) == 1
        # Extract payload from raw frame
        from flock.protocol.packet import HEADER_SIZE
        assert received_payloads[0][HEADER_SIZE:] == b"test tcp delivery payload"
    finally:
        await server_transport.stop()
        await client_transport.stop()
