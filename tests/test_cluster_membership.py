"""Integration tests for ClusterMembershipService using loopback transports."""

import pytest
import asyncio
from flock.types import NodeInfo
from flock.transport.tcp import TcpTransport
from flock.serialization.json import JsonSerializer
from flock.messaging.bus import MessageBus
from flock.events.bus import EventBus
from flock.discovery.service import DiscoveryService
from flock.cluster.service import ClusterMembershipService
from flock.cluster.models import ClusterMemberStatus

@pytest.mark.asyncio
async def test_cluster_membership_join_handshake() -> None:
    # Set up client and server nodes
    server_transport = TcpTransport("127.0.0.1", 22001)
    client_transport = TcpTransport("127.0.0.1", 22002)
    serializer = JsonSerializer()

    server_bus = MessageBus(server_transport, serializer)
    client_bus = MessageBus(client_transport, serializer)

    server_events = EventBus()
    client_events = EventBus()

    server_discovery = DiscoveryService(
        node_id="server-node",
        advertised_host="127.0.0.1",
        advertised_port=22001,
        message_bus=server_bus
    )
    client_discovery = DiscoveryService(
        node_id="client-node",
        advertised_host="127.0.0.1",
        advertised_port=22002,
        message_bus=client_bus
    )

    server_cluster = ClusterMembershipService(
        node_id="server-node",
        discovery_service=server_discovery,
        message_bus=server_bus,
        event_bus=server_events
    )
    client_cluster = ClusterMembershipService(
        node_id="client-node",
        discovery_service=client_discovery,
        message_bus=client_bus,
        event_bus=client_events
    )

    joined_future = asyncio.get_running_loop().create_future()

    from typing import Dict, Any
    async def on_member_joined(event_data: Dict[str, Any]) -> None:
        if event_data["node_id"] == "client-node":
            joined_future.set_result(True)

    server_events.subscribe("cluster.member_joined", on_member_joined)
    # Listen to client-node's member addition of the server node to block until handshake completes
    client_joined_future = asyncio.get_running_loop().create_future()
    async def on_client_member_added(event_data: Dict[str, Any]) -> None:
        if event_data["node_id"] == "server-node":
            client_joined_future.set_result(True)
    client_events.subscribe("cluster.member_joined", on_client_member_added)

    await server_transport.start()
    await client_transport.start()
    # Do not call server/client discovery start() to avoid dynamic discovery loops interfering with the test assertions

    try:
        # Perform dynamic join RPC call
        target = NodeInfo(node_id="server-node", host="127.0.0.1", port=22001)
        # Register server's node details in client's discovery registry to support join ack metadata extraction
        client_discovery.registry.register(server_discovery.get_self_description())
        await client_cluster.join_cluster(target)

        # Wait for handshake acknowledgements and EventBus notify on both sides
        await asyncio.wait_for(joined_future, timeout=3.0)
        await asyncio.wait_for(client_joined_future, timeout=3.0)
        
        assert server_cluster.registry.get_member("client-node").status == ClusterMemberStatus.ACTIVE # type: ignore
        assert len(server_cluster.registry.list_members()) == 2
        assert len(client_cluster.registry.list_members()) == 2
    finally:
        await server_discovery.stop()
        await client_discovery.stop()
        await server_transport.stop()
        await client_transport.stop()
