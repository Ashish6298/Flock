"""Unit tests for Performance Regression Detection & Baseline Management."""

import pytest
import time
from flock.performance.models import BenchmarkResult, RegressionThreshold
from flock.performance.registry import PerformanceRegistry
from flock.performance.regression import PerformanceRegressionEngine


def test_baseline_creation_and_lookup() -> None:
    registry = PerformanceRegistry()
    engine = PerformanceRegressionEngine(registry)

    res = BenchmarkResult(
        name="serialization-throughput",
        mean_duration_ms=10.0,
        min_duration_ms=8.0,
        max_duration_ms=12.0,
        std_dev_ms=1.0,
        throughput=100.0,
    )

    # 1. Create baseline
    baseline = engine.create_baseline("serialization-throughput", res)
    assert baseline.name == "serialization-throughput"
    assert baseline.target_mean_duration_ms == 10.0
    assert baseline.target_throughput == 100.0

    # 2. Lookup baseline
    retrieved = registry.get_baseline("serialization-throughput")
    assert retrieved is not None
    assert retrieved.target_mean_duration_ms == 10.0

    # 3. Remove baseline
    registry.remove_baseline("serialization-throughput")
    assert registry.get_baseline("serialization-throughput") is None


def test_regression_comparisons_and_thresholds() -> None:
    registry = PerformanceRegistry()
    engine = PerformanceRegressionEngine(registry)

    # Base baseline
    res_base = BenchmarkResult(
        name="task-execution",
        mean_duration_ms=50.0,
        min_duration_ms=45.0,
        max_duration_ms=55.0,
        std_dev_ms=2.0,
        throughput=20.0,
    )
    engine.create_baseline("task-execution", res_base)

    # 1. PASSED comparison (identical metrics)
    comp_passed = engine.compare_against_baseline(res_base)
    assert comp_passed.status == "PASSED"
    assert comp_passed.latency_change_percent == 0.0

    # 2. WARNING comparison (slight degradation below limits)
    res_warn = res_base.model_copy(
        update={
            "mean_duration_ms": 52.5,  # +5% (limit is 10%)
            "throughput": 19.5,  # -2.5% (limit is 10%)
        }
    )
    comp_warn = engine.compare_against_baseline(res_warn)
    assert comp_warn.status == "WARNING"

    # 3. FAILED comparison (degradation exceeds threshold limit)
    res_fail = res_base.model_copy(
        update={
            "mean_duration_ms": 60.0,  # +20% (exceeds limit 10%)
            "throughput": 15.0,  # -25% (exceeds limit 10%)
        }
    )
    comp_fail = engine.compare_against_baseline(res_fail)
    assert comp_fail.status == "FAILED"
    assert "regression detected" in comp_fail.message


def test_performance_trend_aggregation() -> None:
    registry = PerformanceRegistry()
    engine = PerformanceRegressionEngine(registry)

    # Empty trend
    trend_empty = engine.get_performance_trends("messaging-latency")
    assert trend_empty.direction == "STABLE"
    assert trend_empty.history_count == 0

    # Stable trend
    for i in range(4):
        res = BenchmarkResult(
            name="messaging-latency",
            mean_duration_ms=10.0,
            min_duration_ms=9.0,
            max_duration_ms=11.0,
            std_dev_ms=0.5,
            throughput=100.0,
            timestamp=time.time() + i,
        )
        registry.record_result(res)

    trend_stable = engine.get_performance_trends("messaging-latency")
    assert trend_stable.direction == "STABLE"
    assert trend_stable.history_count == 4
