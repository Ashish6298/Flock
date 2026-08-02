"""Plugin Diagnostics, Health Monitoring & Telemetry Engine.

Passively monitors runtime logs, resource metrics, event telemetry, uptime records,
and evaluates configurable health classification thresholds.
"""

from __future__ import annotations

import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from flock.plugins.exceptions import PluginHealthReportError
from flock.plugins.models import (
    PluginDiagnosticRecord,
    PluginDiagnosticSummary,
    PluginFailureRecord,
    PluginTelemetryHealthReport,
    PluginHealthSnapshot,
    PluginHealthStatus,
    PluginStatistics,
    PluginTelemetryEvent,
)
from flock.plugins.registry import PluginRegistry

logger = structlog.get_logger()


class PluginDiagnosticsEngine:
    """Passively collects, evaluates, and exports diagnostic summaries and health reports."""

    def __init__(self, registry: PluginRegistry) -> None:
        self._registry = registry

    def record_telemetry_event(self, plugin_id: str, event_name: str, payload: Optional[Dict[str, Any]] = None) -> None:
        """Appends a passive telemetry tracking event to registry streams."""
        event = PluginTelemetryEvent(
            event_id=str(uuid.uuid4()),
            plugin_id=plugin_id,
            event_name=event_name,
            timestamp=datetime.now(timezone.utc),
            payload=payload or {},
        )
        self._registry.record_telemetry(event)

        # Update stats count
        stats = self._registry.get_statistics(plugin_id)
        updated_stats = PluginStatistics(
            plugin_id=plugin_id,
            uptime_seconds=stats.uptime_seconds,
            execution_count=stats.execution_count + 1 if event_name == "EXECUTE" else stats.execution_count,
            error_count=stats.error_count,
            warning_count=stats.warning_count,
            restart_count=stats.restart_count,
            last_reset_at=stats.last_reset_at,
        )
        self._registry.update_statistics(updated_stats)

    def record_diagnostic_log(self, plugin_id: str, level: str, message: str, source: str) -> None:
        """Appends a diagnostic record to the registry database."""
        rec = PluginDiagnosticRecord(
            record_id=str(uuid.uuid4()),
            plugin_id=plugin_id,
            timestamp=datetime.now(timezone.utc),
            level=level.upper(),
            message=message,
            source_component=source,
        )
        self._registry.record_diagnostic(rec)

        # Update warnings/errors counts in statistics
        stats = self._registry.get_statistics(plugin_id)
        err_inc = 1 if level.upper() == "ERROR" else 0
        warn_inc = 1 if level.upper() == "WARNING" else 0

        updated_stats = PluginStatistics(
            plugin_id=plugin_id,
            uptime_seconds=stats.uptime_seconds,
            execution_count=stats.execution_count,
            error_count=stats.error_count + err_inc,
            warning_count=stats.warning_count + warn_inc,
            restart_count=stats.restart_count,
            last_reset_at=stats.last_reset_at,
        )
        self._registry.update_statistics(updated_stats)

    def record_failure(self, plugin_id: str, exception: Exception, fatal: bool = False) -> None:
        """Appends failure logs and error statistics matching exceptions."""
        tb_str = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        fail = PluginFailureRecord(
            failure_id=str(uuid.uuid4()),
            plugin_id=plugin_id,
            timestamp=datetime.now(timezone.utc),
            exception_class=exception.__class__.__name__,
            error_message=str(exception),
            stack_trace=tb_str,
            fatal=fatal,
        )
        self._registry.record_failure(fail)

        # Increment stats error count
        stats = self._registry.get_statistics(plugin_id)
        updated_stats = PluginStatistics(
            plugin_id=plugin_id,
            uptime_seconds=stats.uptime_seconds,
            execution_count=stats.execution_count,
            error_count=stats.error_count + 1,
            warning_count=stats.warning_count,
            restart_count=stats.restart_count + (1 if fatal else 0),
            last_reset_at=stats.last_reset_at,
        )
        self._registry.update_statistics(updated_stats)

    def evaluate_health(
        self,
        plugin_id: str,
        error_threshold: int = 5,
        latency_threshold_ms: float = 1000.0,
    ) -> PluginHealthSnapshot:
        """Evaluates health snapshot status applying configurable count thresholds."""
        stats = self._registry.get_statistics(plugin_id)
        metrics = self._registry.get_runtime_metrics(plugin_id)
        failures = self._registry.query_failures(plugin_id)

        # Default state
        status = PluginHealthStatus.HEALTHY
        msg = "Plugin is performing within nominal thresholds."

        # Check fatal execution failure count
        fatal_count = sum(1 for f in failures if f.fatal)
        if fatal_count > 0:
            status = PluginHealthStatus.FAILED
            msg = f"Plugin has encountered {fatal_count} fatal runtime failure(s)."
        elif stats.error_count >= error_threshold:
            status = PluginHealthStatus.DEGRADED
            msg = f"Plugin error count ({stats.error_count}) exceeds threshold limits."
        elif metrics.execution_latency_ms > latency_threshold_ms:
            status = PluginHealthStatus.WARNING
            msg = f"Execution latency ({metrics.execution_latency_ms:.1f}ms) exceeds WARNING threshold."

        snap = PluginHealthSnapshot(
            plugin_id=plugin_id,
            status=status,
            timestamp=datetime.now(timezone.utc),
            message=msg,
            details={
                "error_count": stats.error_count,
                "warning_count": stats.warning_count,
                "latency_ms": metrics.execution_latency_ms,
                "fatal_count": fatal_count,
            },
        )
        self._registry.record_health_snapshot(snap)
        return snap

    def generate_health_report(self, plugin_id: str) -> PluginTelemetryHealthReport:
        """Consolidates current stats, metrics, failures and snapshot into a report."""
        try:
            snapshot = self.evaluate_health(plugin_id)
            stats = self._registry.get_statistics(plugin_id)
            metrics = self._registry.get_runtime_metrics(plugin_id)
            failures = self._registry.query_failures(plugin_id)

            return PluginTelemetryHealthReport(
                plugin_id=plugin_id,
                overall_status=snapshot.status,
                generated_at=datetime.now(timezone.utc),
                snapshot=snapshot,
                statistics=stats,
                metrics=metrics,
                recent_failures=failures[-5:],  # Limit to 5 most recent failures
            )
        except Exception as exc:
            raise PluginHealthReportError(f"Failed to generate health report for plugin '{plugin_id}': {exc}") from exc

    def generate_diagnostic_summary(self, plugin_ids: List[str]) -> PluginDiagnosticSummary:
        """Consolidates health metrics across list of plugin IDs."""
        summaries: Dict[str, PluginHealthStatus] = {}
        healthy = 0
        warning = 0
        failed = 0

        for pid in plugin_ids:
            snap = self.evaluate_health(pid)
            summaries[pid] = snap.status
            if snap.status == PluginHealthStatus.HEALTHY:
                healthy += 1
            elif snap.status in (PluginHealthStatus.WARNING, PluginHealthStatus.DEGRADED):
                warning += 1
            elif snap.status == PluginHealthStatus.FAILED:
                failed += 1

        return PluginDiagnosticSummary(
            plugins_analyzed=len(plugin_ids),
            healthy_count=healthy,
            warning_count=warning,
            failed_count=failed,
            timestamp=datetime.now(timezone.utc),
            summaries=summaries,
        )

    def record_uptime(self, plugin_id: str, duration_seconds: float) -> None:
        """Updates statistics uptime tracking values."""
        stats = self._registry.get_statistics(plugin_id)
        updated_stats = PluginStatistics(
            plugin_id=plugin_id,
            uptime_seconds=stats.uptime_seconds + duration_seconds,
            execution_count=stats.execution_count,
            error_count=stats.error_count,
            warning_count=stats.warning_count,
            restart_count=stats.restart_count,
            last_reset_at=stats.last_reset_at,
        )
        self._registry.update_statistics(updated_stats)
