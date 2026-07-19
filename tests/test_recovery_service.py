"""Integration tests validating RecoveryService submit loops and event boundaries."""

import pytest
import asyncio
from typing import Dict, Any
from flock.types import NodeInfo
from flock.transport.tcp import TcpTransport
from flock.serialization.json import JsonSerializer
from flock.messaging.bus import MessageBus
from flock.events.bus import EventBus
from flock.discovery.service import DiscoveryService
from flock.cluster.service import ClusterMembershipService
from flock.heartbeat.service import HeartbeatService
from flock.scheduler.service import TaskSchedulerService
from flock.placement.engine import PlacementEngine
from flock.recovery.engine import RecoveryEngine
from flock.recovery.service import RecoveryService

@pytest.mark.asyncio
async def test_recovery_service_queries() -> None:
    server_transport = TcpTransport("127.0.0.1", 30001)
    client_transport = TcpTransport("127.0.0.1", 30002)
    serializer = JsonSerializer()

    server_bus = MessageBus(server_transport, serializer)
    client_bus = MessageBus(client_transport, serializer)

    server_events = EventBus()
    client_events = EventBus()

    server_discovery = DiscoveryService("server-node", "127.0.0.1", 30001, server_bus)
    client_discovery = DiscoveryService("client-node", "127.0.0.1", 30002, client_bus)

    server_cluster = ClusterMembershipService("server-node", server_discovery, server_bus, server_events)
    client_cluster = ClusterMembershipService("client-node", client_discovery, client_bus, client_events)

    server_heartbeat = HeartbeatService("server-node", server_cluster, server_bus, server_events)
    client_heartbeat = HeartbeatService("client-node", client_cluster, client_bus, client_events)

    server_scheduler = TaskSchedulerService("server-node", server_bus, server_events)
    client_scheduler = TaskSchedulerService("client-node", client_bus, client_events)

    server_placement = PlacementEngine(
        node_id="server-node",
        membership_service=server_cluster,
        heartbeat_service=server_heartbeat,
        scheduler_service=server_scheduler,
        message_bus=server_bus,
        event_bus=server_events
    )

    server_engine = RecoveryEngine(
        node_id="server-node",
        scheduler_service=server_scheduler,
        placement_engine=server_placement,
        membership_service=server_cluster,
        heartbeat_service=server_heartbeat,
        message_bus=server_bus,
        event_bus=server_events
    )

    coordinator = RecoveryService(server_engine)

    client_placement = PlacementEngine(
        node_id="client-node",
        membership_service=client_cluster,
        heartbeat_service=client_heartbeat,
        scheduler_service=client_scheduler,
        message_bus=client_bus,
        event_bus=client_events
    )

    client_engine = RecoveryEngine(
        node_id="client-node",
        scheduler_service=client_scheduler,
        placement_engine=client_placement,
        membership_service=client_cluster,
        heartbeat_service=client_heartbeat,
        message_bus=client_bus,
        event_bus=client_events
    )

    worker = RecoveryService(client_engine)

    # Subscribed alerts
    recovery_started_future = asyncio.get_running_loop().create_future()
    async def on_recovery_start(event_data: Dict[str, Any]) -> None:
        if event_data["task_id"] == "task-10":
            recovery_started_future.set_result(True)
    server_events.subscribe("task.recovery.started", on_recovery_start)

    await server_transport.start()
    await client_transport.start()

    try:
        target = NodeInfo("server-node", "127.0.0.1", 30001)
        
        # Submit query
        await worker.recover_task(target, "task-10")

        # Wait for handshake propagation
        await asyncio.wait_for(recovery_started_future, timeout=3.0)

    finally:
        coordinator.shutdown()
        worker.shutdown()
        await server_transport.stop()
        await client_transport.stop()
