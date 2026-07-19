"""Integration tests validating PlacementEngine constraints matching and assignment handshakes."""

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
from flock.heartbeat.models import HealthState, HealthRecord
from flock.scheduler.service import TaskSchedulerService
from flock.scheduler.models import Task, TaskMetadata, TaskStatus, TaskConstraints
from flock.placement.engine import PlacementEngine
from flock.placement.models import NodeCapability, PlacementPolicy
from flock.placement.exceptions import NoEligibleNodesError

@pytest.mark.asyncio
async def test_placement_constraints_and_handshake() -> None:
    server_transport = TcpTransport("127.0.0.1", 25001)
    client_transport = TcpTransport("127.0.0.1", 25002)
    serializer = JsonSerializer()

    server_bus = MessageBus(server_transport, serializer)
    client_bus = MessageBus(client_transport, serializer)

    server_events = EventBus()
    client_events = EventBus()

    server_discovery = DiscoveryService("server-node", "127.0.0.1", 25001, server_bus)
    client_discovery = DiscoveryService("client-node", "127.0.0.1", 25002, client_bus)

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

    client_placement = PlacementEngine(
        node_id="client-node",
        membership_service=client_cluster,
        heartbeat_service=client_heartbeat,
        scheduler_service=client_scheduler,
        message_bus=client_bus,
        event_bus=client_events
    )

    # Register capabilities
    server_placement.register_node_capability(
        NodeCapability(node_id="client-node", supported_tags=["gpu", "linux"])
    )

    # Add client as ACTIVE and healthy in registries
    server_cluster.registry.add_member(
        ClusterMember(
            node_id="client-node",
            description=client_discovery.get_self_description(),
            status=ClusterMemberStatus.ACTIVE,
            join_timestamp=time.time()
        )
    )
    server_heartbeat.registry.set_record(
        HealthRecord(node_id="client-node", state=HealthState.HEALTHY, last_heartbeat_timestamp=time.time())
    )

    # Subscribe to EventBus assignment alerts on both sides
    server_ack_future = asyncio.get_running_loop().create_future()
    async def on_server_ack(event_data: Dict[str, Any]) -> None:
        if event_data["task_id"] == task.task_id:
            server_ack_future.set_result(True)
    server_events.subscribe("placement.assign_acknowledged", on_server_ack)

    client_assign_future = asyncio.get_running_loop().create_future()
    async def on_client_assign(event_data: Dict[str, Any]) -> None:
        if event_data["task_id"] == task.task_id:
            client_assign_future.set_result(True)
    client_events.subscribe("placement.assign_received", on_client_assign)

    await server_transport.start()
    await client_transport.start()

    try:
        # Submit task with GPU constraint
        constraints = TaskConstraints(required_capabilities=["gpu"])
        meta = TaskMetadata(constraints=constraints)
        task = await server_scheduler.submit_task({"run": "train_model"}, meta)

        # Place task
        decision = await server_placement.place_task(task)
        assert decision.selected_node_id == "client-node"
        assert decision.policy_used == PlacementPolicy.FIRST_HEALTHY

        # Wait for handshake propagation dispatches
        await asyncio.wait_for(client_assign_future, timeout=3.0)
        await asyncio.wait_for(server_ack_future, timeout=3.0)

        # Verify assignment record details
        record = server_placement.registry.get_assignment(task.task_id)
        assert record is not None
        assert record.acknowledged is True

        # Test unmatched constraints failure
        unmatched_constraints = TaskConstraints(required_capabilities=["tpu"])
        unmatched_meta = TaskMetadata(constraints=unmatched_constraints)
        unmatched_task = await server_scheduler.submit_task({"run": "train_model"}, unmatched_meta)

        with pytest.raises(NoEligibleNodesError):
            await server_placement.place_task(unmatched_task)

    finally:
        await server_transport.stop()
        await client_transport.stop()
