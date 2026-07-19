"""Integration tests validating ResultCollector checksum checks and packet integrations."""

import pytest
import asyncio
import time
from typing import Dict, Any
from flock.types import NodeInfo
from flock.transport.tcp import TcpTransport
from flock.serialization.json import JsonSerializer
from flock.messaging.bus import MessageBus
from flock.events.bus import EventBus
from flock.results.collector import ResultCollector
from flock.results.registry import ResultRegistry
from flock.results.serializer import ResultSerializer
from flock.results.models import ExecutionResult
from flock.results.exceptions import ChecksumMismatchError

@pytest.mark.asyncio
async def test_result_collector_checksum_verify() -> None:
    server_transport = TcpTransport("127.0.0.1", 27001)
    serializer = JsonSerializer()
    server_bus = MessageBus(server_transport, serializer)
    server_events = EventBus()

    registry = ResultRegistry()
    res_serializer = ResultSerializer()
    collector = ResultCollector("server-node", server_bus, server_events, registry, res_serializer)

    await server_transport.start()

    try:
        # Valid checksum result
        valid_res = ExecutionResult(
            task_id="task-1",
            node_id="worker-1",
            completed_timestamp=time.time(),
            duration_ms=10.0,
            serialized_value=b"correct-val",
            checksum=res_serializer.generate_checksum(b"correct-val")
        )
        await collector.receive_result(valid_res)
        assert registry.get_result("task-1") == valid_res

        # Invalid checksum result check
        invalid_res = ExecutionResult(
            task_id="task-2",
            node_id="worker-1",
            completed_timestamp=time.time(),
            duration_ms=10.0,
            serialized_value=b"tampered-val",
            checksum="bad-checksum"
        )
        with pytest.raises(ChecksumMismatchError):
            await collector.receive_result(invalid_res)

    finally:
        await server_transport.stop()
