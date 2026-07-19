"""Unit tests validating ResultRegistry future resolutions and TTL evictions."""

import pytest
import asyncio
import time
from flock.results.models import ExecutionResult, ResultMetadata
from flock.results.registry import ResultRegistry
from flock.results.exceptions import DuplicateResultError, ResultTimeoutError

def test_result_registry_operations() -> None:
    registry = ResultRegistry(ttl_sec=1.0)
    res = ExecutionResult(
        task_id="task-1",
        node_id="worker-1",
        completed_timestamp=time.time(),
        duration_ms=10.0,
        serialized_value=b"test-val",
        checksum="abcd"
    )

    registry.register_result(res)
    assert registry.get_result("task-1") == res

    # Duplicate check
    with pytest.raises(DuplicateResultError):
        registry.register_result(res)

@pytest.mark.asyncio
async def test_result_registry_future_wait() -> None:
    registry = ResultRegistry(ttl_sec=5.0)
    res = ExecutionResult(
        task_id="task-2",
        node_id="worker-1",
        completed_timestamp=time.time(),
        duration_ms=10.0,
        serialized_value=b"test-val",
        checksum="abcd"
    )

    async def register_later() -> None:
        await asyncio.sleep(0.1)
        registry.register_result(res)

    # Concurrently wait and register
    wait_coro = registry.wait_for_result("task-2", timeout_sec=2.0)
    results = await asyncio.gather(wait_coro, register_later())
    assert results[0] == res

    # Timeout check
    with pytest.raises(ResultTimeoutError):
        await registry.wait_for_result("task-non-existent", timeout_sec=0.1)
