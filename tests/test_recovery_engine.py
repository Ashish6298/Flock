"""Integration tests validating RecoveryEngine coordinator callbacks and state shifts."""

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
from flock.recovery.engine import RecoveryEngine

@pytest.mark.asyncio
async def test_recovery_engine_reassignment() -> None:
    server_transport = TcpTransport("127.0.0.1", 29001)
    serializer = JsonSerializer()
    server_bus = MessageBus(server_transport, serializer)
    server_events = EventBus()

    discovery = DiscoveryService("server-node", "127.0.0.1", 29001, server_bus)
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

    # Subscribed events
    retry_started_future = asyncio.get_running_loop().create_future()
    async def on_retry_start(event_data: Dict[str, Any]) -> None:
        if event_data["task_id"] == task.task_id:
            retry_started_future.set_result(True)
    server_events.subscribe("task.retry.started", on_retry_start)

    # Add server-node as ACTIVE and healthy (safely retrieve or update status)
    member = ClusterMember(
        node_id="server-node",
        description=discovery.get_self_description(),
        status=ClusterMemberStatus.ACTIVE,
        join_timestamp=time.time()
    )
    if not cluster.registry.get_member("server-node"):
        cluster.registry.add_member(member)

    await server_transport.start()

    try:
        # Submit mock task
        task = await scheduler.submit_task({"cmd": "calc"}, TaskMetadata())
        
        # Trigger mock execution failure
        await engine.handle_execution_failure(task, "Connection timeout error")

        # Verify retry is scheduled and started
        await asyncio.wait_for(retry_started_future, timeout=3.0)

        # Registry checks
        ctx = engine.registry.get_context(task.task_id)
        assert ctx.attempt_count == 1
        assert ctx.last_error_message == "Connection timeout error"

    finally:
        await server_transport.stop()
        engine.registry.clear()
