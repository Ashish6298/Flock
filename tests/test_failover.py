"""Integration tests validating PlacementEngine worker exclusion and failovers."""

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
from flock.placement.models import NodeCapability
from flock.recovery.engine import RecoveryEngine

@pytest.mark.asyncio
async def test_failover_excludes_worker() -> None:
    server_transport = TcpTransport("127.0.0.1", 31001)
    serializer = JsonSerializer()
    server_bus = MessageBus(server_transport, serializer)
    server_events = EventBus()

    discovery = DiscoveryService("server-node", "127.0.0.1", 31001, server_bus)
    cluster = ClusterMembershipService("server-node", discovery, server_bus, server_events)
    heartbeat = HeartbeatService("server-node", cluster, server_bus, server_events)
    scheduler = TaskSchedulerService("server-node", server_bus, server_events)

    placement = PlacementEngine(
        node_id="server-node",
        membership_service=cluster,
        heartbeat_service=heartbeat,
        scheduler_service=scheduler,
        message_bus=server_bus,
        event_bus=server_events
    )

    engine = RecoveryEngine(
        node_id="server-node",
        scheduler_service=scheduler,
        placement_engine=placement,
        membership_service=cluster,
        heartbeat_service=heartbeat,
        message_bus=server_bus,
        event_bus=server_events
    )

    # Register capabilities
    placement.register_node_capability(NodeCapability(node_id="server-node", supported_tags=["gpu"]))
    placement.register_node_capability(NodeCapability(node_id="worker-node-2", supported_tags=["gpu"]))

    # Populate cluster active nodes registry
    member = ClusterMember(
        node_id="server-node",
        description=discovery.get_self_description(),
        status=ClusterMemberStatus.ACTIVE,
        join_timestamp=time.time()
    )
    if not cluster.registry.get_member("server-node"):
        cluster.registry.add_member(member)
    cluster.registry.add_member(
        ClusterMember(
            node_id="worker-node-2",
            description=discovery.get_self_description(),
            status=ClusterMemberStatus.ACTIVE,
            join_timestamp=time.time()
        )
    )

    # Set both healthy
    heartbeat.registry.set_record(HealthRecord(node_id="server-node", state=HealthState.HEALTHY, last_heartbeat_timestamp=time.time()))
    heartbeat.registry.set_record(HealthRecord(node_id="worker-node-2", state=HealthState.HEALTHY, last_heartbeat_timestamp=time.time()))

    await server_transport.start()

    try:
        # Submit task with GPU capability constraint
        task = await scheduler.submit_task({"run": "train"}, TaskMetadata(constraints=TaskConstraints(required_capabilities=["gpu"])))
        
        # Initial placement selects server-node (the first eligible healthy node)
        decision1 = await placement.place_task(task)
        assert decision1.selected_node_id == "server-node"

        # Simulate execution failure on server-node
        task_failing = Task(
            task_id=task.task_id,
            creator_node_id="server-node",
            payload=task.payload,
            metadata=task.metadata
        )
        await engine.handle_execution_failure(task_failing, "OutOfMemoryException")

        # Verify task cooldown excludes server-node, forcing failover target to worker-node-2
        plan = engine.registry.get_plan(task.task_id)
        assert plan is not None
        assert plan.target_node_id == "worker-node-2"

    finally:
        await server_transport.stop()
        engine.registry.clear()
