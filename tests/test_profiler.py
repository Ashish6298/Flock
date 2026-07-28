"""Unit tests for Runtime Profiler Engine decorators and hotspot analyzers."""

import time
from flock.performance.registry import PerformanceRegistry
from flock.performance.profiler import RuntimeProfilerEngine, profile_execution


def test_profiler_session_recording() -> None:
    registry = PerformanceRegistry()
    engine = RuntimeProfilerEngine(registry)

    calls = []

    def target_method(val: int) -> int:
        calls.append(val)
        return val * 2

    # Run profiler
    res = engine.profile_call("session-123", target_method, 5)
    assert res == 10
    assert calls == [5]

    # Verify session recorded in registry
    session = registry.get_session("session-123")
    assert session is not None
    assert session.session_id == "session-123"
    assert len(session.cpu_snapshots) == 1
    assert session.cpu_snapshots[0].function_name == "target_method"
    assert session.cpu_snapshots[0].call_count == 1
    assert session.cpu_snapshots[0].total_time_ms > 0
    assert len(session.memory_snapshots) == 1
    assert session.memory_snapshots[0].allocation_bytes > 0


def test_profiler_decorator_and_hotspots() -> None:
    registry = PerformanceRegistry()
    engine = RuntimeProfilerEngine(registry)

    @profile_execution("session-decorator", registry)
    def target_decorator(val: int) -> int:
        time.sleep(0.005)
        return val + 1

    res = target_decorator(10)
    assert res == 11

    # Verify session recorded
    session = registry.get_session("session-decorator")
    assert session is not None
    assert session.cpu_snapshots[0].function_name == "target_decorator"

    # Verify hotspot analysis
    hotspots = engine.get_hotspots()
    assert len(hotspots) == 1
    assert hotspots[0]["function_name"] == "target_decorator"
    assert hotspots[0]["cumulative_time_ms"] > 0
