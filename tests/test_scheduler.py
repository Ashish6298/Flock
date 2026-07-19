"""Integration tests validating TaskSchedulerService queue sorting, validation, and handshake flows."""

import pytest
import asyncio
import time
from typing import Dict, Any
from flock.types import NodeInfo
from flock.transport.tcp import TcpTransport
from flock.serialization.json import JsonSerializer
from flock.messaging.bus import MessageBus
from flock.events.bus import EventBus
from flock.scheduler.service import TaskSchedulerService
from flock.scheduler.models import Task, TaskMetadata, TaskStatus, TaskPriority, SchedulingPolicy
from flock.scheduler.exceptions import TaskValidationError, InvalidTaskStateTransitionError

def test_task_registry_transitions() -> None:
    from flock.scheduler.registry import TaskRegistry
    registry = TaskRegistry()
    
    task = Task(
        task_id="task-1",
        creator_node_id="node-1",
        payload={"cmd": "echo 1"},
        status=TaskStatus.CREATED
    )
    
    registry.register(task)
    assert len(registry.list_tasks()) == 1
    
    # Valid transition
    registry.update_status("task-1", TaskStatus.QUEUED)
    assert registry.get_task("task-1").status == TaskStatus.QUEUED # type: ignore
    
    # Transition to CANCELLED (terminal)
    registry.update_status("task-1", TaskStatus.CANCELLED)
    
    # Invalid transition check from terminal state
    with pytest.raises(InvalidTaskStateTransitionError):
        registry.update_status("task-1", TaskStatus.ASSIGNED)

def test_queue_ordering() -> None:
    from flock.scheduler.queue import SchedulingQueue
    
    # FIFO Policy
    fifo_q = SchedulingQueue(policy=SchedulingPolicy.FIFO)
    t1 = Task("t1", "node-1", {"cmd": "1"})
    t2 = Task("t2", "node-1", {"cmd": "2"})
    fifo_q.push(t1)
    fifo_q.push(t2)
    assert fifo_q.pop().task_id == "t1" # type: ignore
    assert fifo_q.pop().task_id == "t2" # type: ignore

    # Priority Policy
    priority_q = SchedulingQueue(policy=SchedulingPolicy.PRIORITY)
    t_low = Task("t_low", "node-1", {"cmd": "low"}, TaskMetadata(priority=TaskPriority.LOW))
    t_crit = Task("t_crit", "node-1", {"cmd": "crit"}, TaskMetadata(priority=TaskPriority.CRITICAL))
    priority_q.push(t_low)
    priority_q.push(t_crit)
    assert priority_q.pop().task_id == "t_crit" # type: ignore
    assert priority_q.pop().task_id == "t_low" # type: ignore

@pytest.mark.asyncio
async def test_scheduler_service_submission_flow() -> None:
    server_transport = TcpTransport("127.0.0.1", 24001)
    serializer = JsonSerializer()
    server_bus = MessageBus(server_transport, serializer)
    server_events = EventBus()

    scheduler = TaskSchedulerService(
        node_id="server-node",
        message_bus=server_bus,
        event_bus=server_events
    )

    await server_transport.start()

    try:
        # Submit valid task
        task = await scheduler.submit_task({"run": "test"})
        assert task.status == TaskStatus.QUEUED
        assert scheduler.queue.size() == 1

        # Submit invalid task past deadline
        past_deadline_meta = TaskMetadata(execution_deadline=time.time() - 10)
        with pytest.raises(TaskValidationError):
            await scheduler.submit_task({"run": "bad"}, past_deadline_meta)

    finally:
        await server_transport.stop()
