"""Integration tests for DiscoveryService coordinator using TCP Transport loopback."""

import pytest
import asyncio
from flock.types import NodeInfo
from flock.transport.tcp import TcpTransport
from flock.serialization.json import JsonSerializer
from flock.messaging.bus import MessageBus
from flock.messaging.models import MessageMetadata
from flock.discovery.models import NodeDescription
from flock.discovery.service import DiscoveryService, DiscoveryState

@pytest.mark.asyncio
async def test_discovery_service_query_loop() -> None:
    # Set up client and server nodes
    server_transport = TcpTransport("127.0.0.1", 21001)
    client_transport = TcpTransport("127.0.0.1", 21002)
    serializer = JsonSerializer()

    server_bus = MessageBus(server_transport, serializer)
    client_bus = MessageBus(client_transport, serializer)

    server_service = DiscoveryService(
        node_id="server-node",
        advertised_host="127.0.0.1",
        advertised_port=21001,
        message_bus=server_bus,
        broadcast_interval_seconds=1.0,
        expiration_seconds=5.0
    )
    client_service = DiscoveryService(
        node_id="client-node",
        advertised_host="127.0.0.1",
        advertised_port=21002,
        message_bus=client_bus,
        broadcast_interval_seconds=1.0,
        expiration_seconds=5.0
    )

    discovered_future = asyncio.get_running_loop().create_future()

    async def on_peer_discovered(desc: NodeDescription) -> None:
        if desc.node_id == "server-node":
            discovered_future.set_result(True)

    client_service.register_discovered_callback(on_peer_discovered)

    await server_transport.start()
    await client_transport.start()
    await server_service.start()
    await client_service.start()

    try:
        # Client queries server directly
        target_info = NodeInfo(node_id="server-node", host="127.0.0.1", port=21001)
        
        # Override reply port configuration using metadata
        metadata = MessageMetadata(custom={"reply_port": 21002})
        
        # Inject the query directly. Service internally sends custom request
        # We manually call query_target and wire custom metadata overrides
        payload = {
            "node_id": client_service.node_id,
            "host": client_service.host,
            "port": client_service.port,
            "protocol_version": 1,
            "framework_version": "0.1.0"
        }
        from flock.protocol.packet import MessageType
        # Direct MessageBus send to propagate reply_port overrides
        await client_bus.send(target_info, MessageType.DISCOVERY_REQUEST, payload, metadata)

        # Wait for discovery callbacks to register response
        await asyncio.wait_for(discovered_future, timeout=3.0)
        assert client_service.state == DiscoveryState.DISCOVERED
        assert len(client_service.registry.list_peers()) == 1
    finally:
        await server_service.stop()
        await client_service.stop()
        await server_transport.stop()
        await client_transport.stop()
