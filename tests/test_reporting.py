"""Unit tests for Performance Reporting & Engineering Analytics Engine."""

import pytest
from flock.performance.models import BenchmarkResult, PerformanceFinding
from flock.performance.registry import PerformanceRegistry
from flock.performance.reporting import PerformanceReportingEngine


def test_performance_report_generation_and_certification() -> None:
    registry = PerformanceRegistry()
    engine = PerformanceReportingEngine(registry)

    # Healthy election result
    res_healthy = BenchmarkResult(
        name="election-speed",
        mean_duration_ms=45.0,
        min_duration_ms=40.0,
        max_duration_ms=50.0,
        std_dev_ms=2.0,
        throughput=22.0,
    )

    finding = PerformanceFinding(
        severity="INFO",
        description="Startup initialization completed within expected SLA parameters.",
        impacted_area="Initialization",
    )

    # 1. Generate certified report
    report = engine.generate_performance_report("election-speed", res_healthy, [finding])
    assert report.name == "election-speed"
    assert report.scorecard.overall_score == 95.0
    assert report.scorecard.latency_rating == "A"
    assert report.certification.is_certified is True
    assert len(report.findings) == 1

    # 2. Verify registry lookup
    retrieved = registry.get_performance_report("election-speed")
    assert retrieved is not None
    assert retrieved.scorecard.overall_score == 95.0


def test_reports_comparison_and_deltas() -> None:
    registry = PerformanceRegistry()
    engine = PerformanceReportingEngine(registry)

    res_v1 = BenchmarkResult(
        name="task-execution",
        mean_duration_ms=80.0,  # B rating, 85 score
        min_duration_ms=75.0,
        max_duration_ms=85.0,
        std_dev_ms=3.0,
        throughput=12.5,
    )
    res_v2 = BenchmarkResult(
        name="task-execution",
        mean_duration_ms=45.0,  # A rating, 95 score
        min_duration_ms=40.0,
        max_duration_ms=50.0,
        std_dev_ms=2.0,
        throughput=22.0,
    )

    report_v1 = engine.generate_performance_report("run1", res_v1)
    report_v2 = engine.generate_performance_report("run2", res_v2)

    # Compare
    comparison = engine.compare_reports(report_v1, report_v2)
    assert comparison.improvement_detected is True
    assert comparison.latency_delta_percent > 0.0
