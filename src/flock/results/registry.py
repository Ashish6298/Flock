"""Authoritative container keeping completed execution result values and futures mappings."""

import time
import asyncio
import structlog
from typing import Dict, List, Optional
from flock.results.models import ExecutionResult
from flock.results.exceptions import DuplicateResultError, ResultTimeoutError

logger = structlog.get_logger()

class ResultRegistry:
    """Asyncio-safe result registry tracking completed execution metrics and future waiters."""

    def __init__(self, ttl_sec: float = 300.0) -> None:
        self.ttl = ttl_sec
        self._results: Dict[str, ExecutionResult] = {}
        self._waiters: Dict[str, List[asyncio.Future[ExecutionResult]]] = {}
        self._timestamps: Dict[str, float] = {}

    def register_result(self, result: ExecutionResult) -> None:
        """Register execution result and resolve pending waiters.

        Raises:
            DuplicateResultError: If result already registered.
        """
        task_id = result.task_id
        if task_id in self._results:
            raise DuplicateResultError(f"Result for task {task_id} already registered")

        self._results[task_id] = result
        self._timestamps[task_id] = time.time()

        # Resolve waiters
        waiters_list = self._waiters.pop(task_id, [])
        for fut in waiters_list:
            if not fut.done():
                fut.set_result(result)
        logger.info("Registered task result in registry", task_id=task_id, success=result.success)

    def get_result(self, task_id: str) -> Optional[ExecutionResult]:
        """Lookup result directly if already registered."""
        return self._results.get(task_id)

    async def wait_for_result(self, task_id: str, timeout_sec: float = 10.0) -> ExecutionResult:
        """Asynchronously block until task result arrives or timeout fires.

        Raises:
            ResultTimeoutError: If timeout window exceeded.
        """
        existing = self.get_result(task_id)
        if existing:
            return existing

        fut = asyncio.get_running_loop().create_future()
        if task_id not in self._waiters:
            self._waiters[task_id] = []
        self._waiters[task_id].append(fut)

        try:
            return await asyncio.wait_for(fut, timeout=timeout_sec)
        except asyncio.TimeoutError as err:
            # Cleanup waiter future reference
            if task_id in self._waiters:
                try:
                    self._waiters[task_id].remove(fut)
                except ValueError:
                    pass
            raise ResultTimeoutError(f"Timeout waiting for task {task_id} result after {timeout_sec}s") from err

    def cleanup_expired_entries(self) -> None:
        """Evict records older than configured TTL window bounds."""
        now = time.time()
        expired = [tid for tid, ts in self._timestamps.items() if now - ts > self.ttl]
        
        for tid in expired:
            self._results.pop(tid, None)
            self._timestamps.pop(tid, None)
            logger.info("Evicted expired task result registry record", task_id=tid)

    def clear(self) -> None:
        """Clear all registered results and waiters."""
        self._results.clear()
        self._waiters.clear()
        self._timestamps.clear()
