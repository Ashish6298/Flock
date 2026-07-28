"""Unit tests for Performance Optimization & Execution Analysis Engine."""

import pytest
from flock.performance.models import (
    BenchmarkResult,
    ProfilingSession,
    CPUProfileSnapshot,
    MemoryProfileSnapshot,
    OptimizationPriority,
)
from flock.performance.registry import PerformanceRegistry
from flock.performance.optimizer import PerformanceOptimizationEngine


def test_execution_analysis_and_stability() -> None:
    registry = PerformanceRegistry()
    engine = PerformanceOptimizationEngine(registry)

    res = BenchmarkResult(
        name="serialization",
        mean_duration_ms=10.0,
        min_duration_ms=8.0,
        max_duration_ms=12.0,
        std_dev_ms=1.0,
        throughput=100.0,
    )

    analysis = engine.analyze_execution(res)
    assert analysis.mean_latency_ms == 10.0
    assert analysis.standard_deviation_ms == 1.0
    assert analysis.throughput_ops == 100.0
    assert analysis.stability_score == 90.0  # max(0.0, 100.0 - (1.0 / 10.0 * 100)) = 90.0


def test_optimization_recommendations_and_ranking() -> None:
    registry = PerformanceRegistry()
    engine = PerformanceOptimizationEngine(registry)

    # Setup profiles triggering critical CPU hotspots and high latency bottlenecks
    res = BenchmarkResult(
        name="consensus-election",
        mean_duration_ms=150.0,  # > 100ms -> HIGH latency recommendation
        min_duration_ms=120.0,
        max_duration_ms=180.0,
        std_dev_ms=15.0,
        throughput=6.6,
    )

    cpu_snap = CPUProfileSnapshot(
        function_name="elect_leader",
        call_count=1,
        total_time_ms=250.0,  # > 200ms -> CRITICAL CPU recommendation
        exclusive_time_ms=250.0,
    )
    mem_snap = MemoryProfileSnapshot(
        allocation_bytes=60 * 1024 * 1024,  # > 50MB -> MEDIUM memory recommendation
        peak_bytes=60 * 1024 * 1024,
    )
    session = ProfilingSession(
        session_id="session-consensus",
        cpu_snapshots=[cpu_snap],
        memory_snapshots=[mem_snap],
    )

    # 1. Compile report
    report = engine.generate_optimization_report("consensus-election", res, session)
    assert report.name == "consensus-election"
    assert len(report.bottlenecks) == 1
    assert report.bottlenecks[0].category == "Latency"

    # 2. Verify registry persistence
    retrieved = registry.get_optimization_report("consensus-election")
    assert retrieved is not None
    assert retrieved.resource_usage is not None
    assert retrieved.resource_usage.cpu_percent == 45.0

    # 3. Verify priority ranking
    ranked = engine.rank_recommendations(report)
    assert len(ranked) >= 3
    # Check that CRITICAL comes first, then HIGH, then MEDIUM
    assert ranked[0].priority == OptimizationPriority.CRITICAL
    assert ranked[1].priority == OptimizationPriority.HIGH
    assert ranked[2].priority == OptimizationPriority.MEDIUM
