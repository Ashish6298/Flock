"""Unit and integration tests for Plugin Diagnostics, Health Monitoring & Telemetry."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from flock.plugins.models import PluginRuntimeMetrics, PluginHealthStatus
from flock.plugins.registry import PluginRegistry
from flock.plugins.diagnostics import PluginDiagnosticsEngine


def test_telemetry_event_recording() -> None:
    registry = PluginRegistry()
    engine = PluginDiagnosticsEngine(registry)

    engine.record_telemetry_event("plugin-a", "ACTIVATE", {"timestamp": "now"})
    events = registry.query_telemetry("plugin-a")
    assert len(events) == 1
    assert events[0].event_name == "ACTIVATE"

    # EXECUTE events should update execution_count stats
    engine.record_telemetry_event("plugin-a", "EXECUTE")
    stats = registry.get_statistics("plugin-a")
    assert stats.execution_count == 1


def test_diagnostic_logging() -> None:
    registry = PluginRegistry()
    engine = PluginDiagnosticsEngine(registry)

    engine.record_diagnostic_log("plugin-a", "WARNING", "Potential delay detected", "Scheduler")
    logs = registry.query_diagnostics("plugin-a")
    assert len(logs) == 1
    assert logs[0].level == "WARNING"

    stats = registry.get_statistics("plugin-a")
    assert stats.warning_count == 1


def test_failure_exception_logging() -> None:
    registry = PluginRegistry()
    engine = PluginDiagnosticsEngine(registry)

    try:
        raise ValueError("Lifecycle exception")
    except ValueError as exc:
        engine.record_failure("plugin-a", exc, fatal=True)

    failures = registry.query_failures("plugin-a")
    assert len(failures) == 1
    assert failures[0].exception_class == "ValueError"
    assert failures[0].fatal is True

    stats = registry.get_statistics("plugin-a")
    assert stats.error_count == 1
    assert stats.restart_count == 1


def test_health_evaluation_thresholds() -> None:
    registry = PluginRegistry()
    engine = PluginDiagnosticsEngine(registry)

    # Initially healthy
    snap = engine.evaluate_health("plugin-a")
    assert snap.status == PluginHealthStatus.HEALTHY

    # Exceed error count threshold
    for _ in range(5):
        engine.record_diagnostic_log("plugin-a", "ERROR", "Connection failed", "Loader")

    snap2 = engine.evaluate_health("plugin-a", error_threshold=5)
    assert snap2.status == PluginHealthStatus.DEGRADED

    # High latency warning
    registry.update_runtime_metrics("plugin-b", PluginRuntimeMetrics(execution_latency_ms=1200.0))
    snap3 = engine.evaluate_health("plugin-b", latency_threshold_ms=1000.0)
    assert snap3.status == PluginHealthStatus.WARNING

    # Fatal failure sets state to FAILED
    engine.record_failure("plugin-c", ValueError("Fatal error"), fatal=True)
    snap4 = engine.evaluate_health("plugin-c")
    assert snap4.status == PluginHealthStatus.FAILED


def test_generate_health_report_and_diagnostic_summary() -> None:
    registry = PluginRegistry()
    engine = PluginDiagnosticsEngine(registry)

    report = engine.generate_health_report("plugin-a")
    assert report.plugin_id == "plugin-a"
    assert report.overall_status == PluginHealthStatus.HEALTHY

    summary = engine.generate_diagnostic_summary(["plugin-a", "plugin-b"])
    assert summary.plugins_analyzed == 2
    assert summary.healthy_count == 2


def test_record_uptime_and_clear() -> None:
    registry = PluginRegistry()
    engine = PluginDiagnosticsEngine(registry)

    engine.record_uptime("plugin-a", 15.0)
    stats = registry.get_statistics("plugin-a")
    assert stats.uptime_seconds == 15.0

    # Clear diagnostics should purge all stats and lists
    registry.clear_diagnostics("plugin-a")
    cleared_stats = registry.get_statistics("plugin-a")
    assert cleared_stats.uptime_seconds == 0.0
    assert len(registry.query_telemetry("plugin-a")) == 0
