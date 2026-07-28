"""Unit tests for Performance Monitoring & Live Metrics Dashboard Engine."""

import pytest
from flock.performance.models import MetricsThreshold
from flock.performance.registry import PerformanceRegistry
from flock.performance.monitor import PerformanceMonitorEngine


def test_monitor_metric_recording_and_health() -> None:
    registry = PerformanceRegistry()
    engine = PerformanceMonitorEngine(registry)

    # 1. Record healthy metrics
    engine.record_metric("latency_ms", 45.0)
    engine.record_metric("cpu_percent", 50.0)

    # Calculate health
    active = {"latency_ms": 45.0, "cpu_percent": 50.0}
    assert engine.calculate_system_health(active) == "HEALTHY"

    # 2. Record degraded metrics
    active_degraded = {"latency_ms": 120.0, "cpu_percent": 50.0}
    assert engine.calculate_system_health(active_degraded) == "DEGRADED"

    # 3. Record critical metrics
    active_critical = {"latency_ms": 120.0, "cpu_percent": 95.0}
    assert engine.calculate_system_health(active_critical) == "CRITICAL"


def test_alerts_evaluation() -> None:
    registry = PerformanceRegistry()
    engine = PerformanceMonitorEngine(registry)

    thresholds = [
        MetricsThreshold(
            metric_name="latency_ms",
            warning_limit=100.0,
            error_limit=200.0,
        )
    ]

    # No alerts
    alerts_none = engine.evaluate_alerts({"latency_ms": 50.0}, thresholds)
    assert len(alerts_none) == 0

    # Warning alert
    alerts_warn = engine.evaluate_alerts({"latency_ms": 150.0}, thresholds)
    assert len(alerts_warn) == 1
    assert alerts_warn[0].severity == "WARNING"
    assert alerts_warn[0].observed_value == 150.0

    # Error alert
    alerts_err = engine.evaluate_alerts({"latency_ms": 250.0}, thresholds)
    assert len(alerts_err) == 1
    assert alerts_err[0].severity == "ERROR"
    assert alerts_err[0].observed_value == 250.0


def test_dashboard_aggregation() -> None:
    registry = PerformanceRegistry()
    engine = PerformanceMonitorEngine(registry)

    # Record history
    engine.record_metric("throughput", 80.0)
    engine.record_metric("throughput", 95.0)

    snapshot = engine.generate_dashboard_snapshot()
    assert snapshot.health_status == "HEALTHY"
    assert snapshot.active_metrics["throughput"] == 95.0
    assert len(snapshot.series) == 1
    assert snapshot.series[0].name == "throughput"
    assert snapshot.series[0].values == [80.0, 95.0]
