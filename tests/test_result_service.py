"""Integration tests validating ResultService submit loops, wait routines, and runtime handovers."""

import pytest
import asyncio
import time
from typing import Dict, Any
from flock.types import NodeInfo
from flock.transport.tcp import TcpTransport
from flock.serialization.json import JsonSerializer
from flock.messaging.bus import MessageBus
from flock.events.bus import EventBus
from flock.results.service import ResultService

@pytest.mark.asyncio
async def test_result_service_submit_and_wait_handshake() -> None:
    server_transport = TcpTransport("127.0.0.1", 28001)
    client_transport = TcpTransport("127.0.0.1", 28002)
    serializer = JsonSerializer()

    server_bus = MessageBus(server_transport, serializer)
    client_bus = MessageBus(client_transport, serializer)

    server_events = EventBus()
    client_events = EventBus()

    # Coordinator node runs ResultService
    coordinator = ResultService("coordinator-node", server_bus, server_events)
    # Worker node runs ResultService to submit task completion returns
    worker = ResultService("worker-node", client_bus, client_events)

    await server_transport.start()
    await client_transport.start()

    try:
        task_id = "task-calc-1"
        target = NodeInfo("coordinator-node", "127.0.0.1", 28001)

        async def worker_submit_later() -> None:
            await asyncio.sleep(0.1)
            # Submit computation result value 42
            await worker.submit_result(target, task_id, 42)

        # Coordinator blocks waiting for computation result value
        wait_coro = coordinator.wait_for_result(task_id, timeout_sec=2.0)
        results = await asyncio.gather(wait_coro, worker_submit_later())
        
        # Verify returned value matches input
        assert results[0] == 42
        assert coordinator.get_result(task_id) == 42

    finally:
        coordinator.shutdown()
        worker.shutdown()
        await server_transport.stop()
        await client_transport.stop()
