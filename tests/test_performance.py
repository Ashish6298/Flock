"""Unit tests for Performance Foundation models, timer, engine, and registry."""

import time
from flock.performance.models import BenchmarkDefinition
from flock.performance.timer import PerformanceTimer, time_execution
from flock.performance.registry import PerformanceRegistry
from flock.performance.engine import BenchmarkEngine


def test_timer_context_and_decorator() -> None:
    captured: list[float] = []

    def callback(d: float) -> None:
        captured.append(d)

    # 1. Scoped context timer
    with PerformanceTimer("context-test", callback=callback) as timer:
        time.sleep(0.01)

    assert len(captured) == 1
    assert captured[0] > 0.0
    assert timer.duration == captured[0]

    # 2. Decorator timing
    @time_execution("decorator-test", callback=callback)
    def dummy_method() -> None:
        time.sleep(0.01)

    dummy_method()
    assert len(captured) == 2
    assert captured[1] > 0.0


def test_performance_registry() -> None:
    registry = PerformanceRegistry()
    defn = BenchmarkDefinition(
        name="serialization-latency",
        warmup_iterations=2,
        measured_iterations=5,
    )
    registry.register_benchmark(defn)

    # Fetch initial empty results
    assert len(registry.get_results("serialization-latency")) == 0


def test_benchmark_engine_run() -> None:
    engine = BenchmarkEngine()
    defn = BenchmarkDefinition(
        name="test-run",
        warmup_iterations=1,
        measured_iterations=3,
    )

    calls = []

    def workload() -> None:
        calls.append(1)
        time.sleep(0.005)

    res = engine.execute_benchmark(defn, workload)
    assert res.name == "test-run"
    assert len(calls) == 4  # 1 warmup + 3 measured
    assert res.mean_duration_ms > 0
    assert res.throughput > 0
    assert res.std_dev_ms >= 0
