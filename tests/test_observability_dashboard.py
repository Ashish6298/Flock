"""Unit tests for DashboardTelemetryAdapter – Phase 34."""

import pytest

from flock.observability.aggregation import AggregationEngine
from flock.observability.alerts import AlertRule, AlertSeverity, ObservabilityAlertManager
from flock.observability.collector import TelemetryCollector
from flock.observability.dashboard import DashboardTelemetryAdapter
from flock.observability.logging import StructuredLogger
from flock.observability.metrics import MetricsEngine
from flock.observability.profiling import ProfilingEngine
from flock.observability.registry import MetricsRegistry
from flock.observability.models import MetricType


def _make_adapter() -> DashboardTelemetryAdapter:
    registry = MetricsRegistry()
    engine = MetricsEngine()
    aggregation = AggregationEngine()
    collector = TelemetryCollector()
    alerts = ObservabilityAlertManager()
    logger = StructuredLogger()
    profiler = ProfilingEngine()
    return DashboardTelemetryAdapter(
        registry=registry,
        engine=engine,
        aggregation=aggregation,
        collector=collector,
        alerts=alerts,
        logger=logger,
        profiler=profiler,
    )


def test_metrics_source_empty() -> None:
    adapter = _make_adapter()
    result = adapter.metrics_source()
    assert result.success is True
    assert result.source_name == "observability.metrics"


def test_metrics_source_with_data() -> None:
    registry = MetricsRegistry()
    registry.register("cpu", MetricType.GAUGE)
    registry.set_gauge("cpu", 72.5)
    adapter = DashboardTelemetryAdapter(
        registry=registry,
        engine=MetricsEngine(),
        aggregation=AggregationEngine(),
        collector=TelemetryCollector(),
        alerts=ObservabilityAlertManager(),
        logger=StructuredLogger(),
        profiler=ProfilingEngine(),
    )
    result = adapter.metrics_source()
    assert any(p.metric_name == "cpu" for p in result.data_points)


def test_aggregation_source_empty() -> None:
    adapter = _make_adapter()
    result = adapter.aggregation_source()
    assert result.success is True
    assert result.source_name == "observability.aggregation"


def test_aggregation_source_with_data() -> None:
    agg = AggregationEngine()
    agg.observe("latency", 25.0)
    adapter = DashboardTelemetryAdapter(
        registry=MetricsRegistry(),
        engine=MetricsEngine(),
        aggregation=agg,
        collector=TelemetryCollector(),
        alerts=ObservabilityAlertManager(),
        logger=StructuredLogger(),
        profiler=ProfilingEngine(),
    )
    result = adapter.aggregation_source()
    assert any(p.metric_name == "latency" for p in result.data_points)


def test_alert_summary_source_no_alerts() -> None:
    adapter = _make_adapter()
    result = adapter.alert_summary_source()
    assert result.success is True
    # All counts should be 0
    for point in result.data_points:
        assert point.value == 0.0


def test_alert_summary_source_with_firing_alert() -> None:
    alerts = ObservabilityAlertManager()
    alerts.add_rule(AlertRule(
        rule_id="r1",
        metric_name="cpu",
        threshold=80.0,
        severity=AlertSeverity.WARNING,
        cooldown_seconds=0.0,
    ))
    alerts.evaluate("cpu", 95.0)
    adapter = DashboardTelemetryAdapter(
        registry=MetricsRegistry(),
        engine=MetricsEngine(),
        aggregation=AggregationEngine(),
        collector=TelemetryCollector(),
        alerts=alerts,
        logger=StructuredLogger(),
        profiler=ProfilingEngine(),
    )
    result = adapter.alert_summary_source()
    warning_point = next(
        (p for p in result.data_points if p.metric_name == "alert.warning"), None
    )
    assert warning_point is not None
    assert warning_point.value == 1.0


def test_profiling_source_with_data() -> None:
    profiler = ProfilingEngine()
    profiler.record("api.query", 15.0)
    adapter = DashboardTelemetryAdapter(
        registry=MetricsRegistry(),
        engine=MetricsEngine(),
        aggregation=AggregationEngine(),
        collector=TelemetryCollector(),
        alerts=ObservabilityAlertManager(),
        logger=StructuredLogger(),
        profiler=profiler,
    )
    result = adapter.profiling_source()
    assert any(p.metric_name == "api.query" for p in result.data_points)


def test_log_count_source() -> None:
    logger = StructuredLogger()
    logger.info("comp", "msg1")
    logger.info("comp", "msg2")
    adapter = DashboardTelemetryAdapter(
        registry=MetricsRegistry(),
        engine=MetricsEngine(),
        aggregation=AggregationEngine(),
        collector=TelemetryCollector(),
        alerts=ObservabilityAlertManager(),
        logger=logger,
        profiler=ProfilingEngine(),
    )
    result = adapter.log_count_source()
    assert result.data_points[0].value == 2.0


def test_collector_source() -> None:
    collector = TelemetryCollector()
    collector.register("p1", lambda: {})
    adapter = DashboardTelemetryAdapter(
        registry=MetricsRegistry(),
        engine=MetricsEngine(),
        aggregation=AggregationEngine(),
        collector=collector,
        alerts=ObservabilityAlertManager(),
        logger=StructuredLogger(),
        profiler=ProfilingEngine(),
    )
    result = adapter.collector_source()
    assert result.data_points[0].value == 1.0


def test_register_all() -> None:
    """Verify all sources are registered with a DataSourceManager."""
    from flock.dashboard.datasources import DataSourceManager
    adapter = _make_adapter()
    mgr = DataSourceManager()
    adapter.register_all(mgr)
    names = mgr.list_sources()
    assert "observability.metrics" in names
    assert "observability.aggregation" in names
    assert "observability.alerts" in names
    assert "observability.profiling" in names
    assert "observability.logs" in names
    assert "observability.collector" in names


def test_register_all_sources_queryable() -> None:
    """All registered sources should be callable without error."""
    from flock.dashboard.datasources import DataSourceManager
    adapter = _make_adapter()
    mgr = DataSourceManager()
    adapter.register_all(mgr)
    results = mgr.query_all()
    assert all(r.success for r in results)
