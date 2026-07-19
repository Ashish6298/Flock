"""Integration tests validating WorkerRuntimeService executor backends and cancellation token flows."""

import pytest
import asyncio
import time
from typing import Dict, Any
from flock.transport.tcp import TcpTransport
from flock.serialization.json import JsonSerializer
from flock.messaging.bus import MessageBus
from flock.events.bus import EventBus
from flock.scheduler.models import Task, TaskMetadata
from flock.runtime.service import WorkerRuntimeService
from flock.runtime.models import WorkerInfo, ExecutionState
from flock.runtime.executor import ThreadPoolExecutorBackend, AsyncExecutorBackend
from flock.runtime.exceptions import ExecutionStateError

def mock_target_fn(val: int) -> int:
    return val * 2

async def mock_async_target_fn(val: int) -> int:
    await asyncio.sleep(0.5)
    return val * 3

@pytest.mark.asyncio
async def test_worker_registration_and_thread_execution() -> None:
    server_transport = TcpTransport("127.0.0.1", 26001)
    serializer = JsonSerializer()
    server_bus = MessageBus(server_transport, serializer)
    server_events = EventBus()

    runtime = WorkerRuntimeService(
        node_id="worker-node",
        message_bus=server_bus,
        event_bus=server_events
    )

    worker = WorkerInfo(worker_id="worker-1", executor_type="thread")
    runtime.register_worker(worker)
    assert len(runtime._workers) == 1

    await server_transport.start()
    await runtime.start()

    try:
        task = Task(task_id="task-1", creator_node_id="worker-node", payload={"run": 10})
        res = await runtime.execute_task(task, mock_target_fn, 10)
        assert res == 20
        assert runtime.get_execution_state("task-1") == ExecutionState.COMPLETED

    finally:
        await runtime.stop()
        await server_transport.stop()

@pytest.mark.asyncio
async def test_async_executor_and_cancellation() -> None:
    server_transport = TcpTransport("127.0.0.1", 26002)
    serializer = JsonSerializer()
    server_bus = MessageBus(server_transport, serializer)
    server_events = EventBus()

    async_executor = AsyncExecutorBackend()
    runtime = WorkerRuntimeService(
        node_id="worker-node",
        message_bus=server_bus,
        event_bus=server_events,
        executor=async_executor
    )

    await server_transport.start()
    await runtime.start()

    try:
        task = Task(task_id="task-2", creator_node_id="worker-node", payload={"run": 5})
        
        # Async execution check
        res = await runtime.execute_task(task, mock_async_target_fn, 5)
        assert res == 15
        
        # Cancellation check
        cancel_task = Task(task_id="task-3", creator_node_id="worker-node", payload={"run": 100})
        
        async def run_and_cancel() -> None:
            await asyncio.sleep(0.05)
            await runtime.request_cancellation("task-3")

        cancel_coro = runtime.execute_task(cancel_task, mock_async_target_fn, 100)
        
        # Run execution and cancellation concurrently
        with pytest.raises(asyncio.CancelledError):
            await asyncio.gather(cancel_coro, run_and_cancel())
            
        assert runtime.get_execution_state("task-3") == ExecutionState.CANCELLED

    finally:
        await runtime.stop()
        await server_transport.stop()
