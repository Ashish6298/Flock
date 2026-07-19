"""Integration tests validating HeartbeatService ping-pong and failure detection."""

import pytest
import asyncio
import time
from typing import Dict, Any
from flock.types import NodeInfo
from flock.transport.tcp import TcpTransport
from flock.serialization.json import JsonSerializer
from flock.messaging.bus import MessageBus
from flock.events.bus import EventBus
from flock.discovery.service import DiscoveryService
from flock.cluster.service import ClusterMembershipService
from flock.cluster.models import ClusterMemberStatus, ClusterMember
from flock.heartbeat.service import HeartbeatService
from flock.heartbeat.models import HealthState

@pytest.mark.asyncio
async def test_heartbeat_ping_pong_flow() -> None:
    server_transport = TcpTransport("127.0.0.1", 23001)
    client_transport = TcpTransport("127.0.0.1", 23002)
    serializer = JsonSerializer()

    server_bus = MessageBus(server_transport, serializer)
    client_bus = MessageBus(client_transport, serializer)

    server_events = EventBus()
    client_events = EventBus()

    server_discovery = DiscoveryService("server-node", "127.0.0.1", 23001, server_bus)
    client_discovery = DiscoveryService("client-node", "127.0.0.1", 23002, client_bus)

    server_cluster = ClusterMembershipService("server-node", server_discovery, server_bus, server_events)
    client_cluster = ClusterMembershipService("client-node", client_discovery, client_bus, client_events)

    # Setup heartbeat services with fast ping intervals for testing
    server_heartbeat = HeartbeatService(
        node_id="server-node",
        membership_service=server_cluster,
        message_bus=server_bus,
        event_bus=server_events,
        ping_interval_sec=0.1,
        ping_timeout_sec=0.05,
        max_missed_count=2
    )

    client_heartbeat = HeartbeatService(
        node_id="client-node",
        membership_service=client_cluster,
        message_bus=client_bus,
        event_bus=client_events,
        ping_interval_sec=0.1,
        ping_timeout_sec=0.05,
        max_missed_count=2
    )

    # Register client-node as ACTIVE manually on server cluster registry, and vice-versa
    server_cluster.registry.add_member(
        ClusterMember(
            node_id="client-node",
            description=client_discovery.get_self_description(),
            status=ClusterMemberStatus.ACTIVE,
            join_timestamp=time.time()
        )
    )
    client_cluster.registry.add_member(
        ClusterMember(
            node_id="server-node",
            description=server_discovery.get_self_description(),
            status=ClusterMemberStatus.ACTIVE,
            join_timestamp=time.time()
        )
    )

    healthy_future = asyncio.get_running_loop().create_future()

    async def on_healthy(event_data: Dict[str, Any]) -> None:
        if event_data["node_id"] == "client-node":
            healthy_future.set_result(True)

    server_events.subscribe("heartbeat.node_healthy", on_healthy)

    await server_transport.start()
    await client_transport.start()
    await server_heartbeat.start()
    await client_heartbeat.start()

    try:
        # Wait for periodic ping-pong loopback to trigger
        await asyncio.wait_for(healthy_future, timeout=3.0)
        
        record = server_heartbeat.registry.get_record("client-node")
        assert record is not None
        assert record.state == HealthState.HEALTHY
        assert record.round_trip_time_ms >= 0.0

        # Simulate timeout failure transition
        await client_transport.stop()
        await client_heartbeat.stop()

        # Monitor event bus for suspect/unreachable state changes
        unreachable_future = asyncio.get_running_loop().create_future()
        async def on_unreachable(event_data: Dict[str, Any]) -> None:
            if event_data["node_id"] == "client-node":
                unreachable_future.set_result(True)
        server_events.subscribe("heartbeat.node_unreachable", on_unreachable)

        await asyncio.wait_for(unreachable_future, timeout=3.0)
        record = server_heartbeat.registry.get_record("client-node")
        assert record is not None
        assert record.state == HealthState.UNREACHABLE

    finally:
        await server_heartbeat.stop()
        await client_heartbeat.stop()
        await server_transport.stop()
        await client_transport.stop()
