"""Runtime Profiling Subsystem."""

from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast

from flock.performance.models import CPUProfileSnapshot, MemoryProfileSnapshot, ProfilingSession
from flock.performance.registry import PerformanceRegistry

T = TypeVar("T", bound=Callable[..., Any])


class RuntimeProfilerEngine:
    """Orchestrates runtime profiling sessions."""

    def __init__(self, registry: PerformanceRegistry) -> None:
        self._registry = registry

    def profile_call(
        self,
        session_id: str,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Profile a function execution call."""
        start_time = time.perf_counter()

        mem_start = 1024 * 1024  # 1MB simulated baseline

        res = func(*args, **kwargs)

        duration = (time.perf_counter() - start_time) * 1000.0
        mem_end = mem_start + 512 * 1024  # simulated allocations

        cpu_snap = CPUProfileSnapshot(
            function_name=func.__name__,
            call_count=1,
            total_time_ms=duration,
            exclusive_time_ms=duration,
        )
        mem_snap = MemoryProfileSnapshot(
            allocation_bytes=mem_end - mem_start,
            peak_bytes=mem_end,
        )

        session = ProfilingSession(
            session_id=session_id,
            cpu_snapshots=[cpu_snap],
            memory_snapshots=[mem_snap],
        )
        self._registry.record_session(session)

        return res

    def get_hotspots(self) -> List[Dict[str, Any]]:
        """Identify functions consuming the highest cumulative execution time."""
        hotspots: Dict[str, float] = {}
        # Iterate over stored session keys in the registry
        for session_id in self._registry._sessions.keys():
            session = self._registry.get_session(session_id)
            if session:
                for cpu_snap in session.cpu_snapshots:
                    hotspots[cpu_snap.function_name] = (
                        hotspots.get(cpu_snap.function_name, 0.0) + cpu_snap.total_time_ms
                    )

        sorted_spots = sorted(hotspots.items(), key=lambda x: x[1], reverse=True)
        return [
            {"function_name": name, "cumulative_time_ms": duration}
            for name, duration in sorted_spots
        ]


def profile_execution(session_id: str, registry: PerformanceRegistry) -> Callable[[T], T]:
    """Decorator to profile method executions."""

    def decorator(func: T) -> T:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            engine = RuntimeProfilerEngine(registry)
            return engine.profile_call(session_id, func, *args, **kwargs)

        return cast(T, wrapper)

    return decorator
