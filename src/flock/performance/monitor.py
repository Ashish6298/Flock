"""Performance Monitoring & Live Dashboard Engine."""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from flock.performance.models import (
    PerformanceMetric,
    MetricsSnapshot,
    DashboardSnapshot,
    DashboardSeries,
    MetricsThreshold,
    MetricsAlert,
)
from flock.performance.registry import PerformanceRegistry


class PerformanceMonitorEngine:
    """Consolidates metrics data into dashboard snapshots and triggers threshold alerts."""

    def __init__(self, registry: PerformanceRegistry) -> None:
        self._registry = registry

    def record_metric(self, name: str, value: float) -> PerformanceMetric:
        """Record and store a single metric value inside the registry snapshots."""
        metric = PerformanceMetric(name=name, value=value, timestamp=time.time())
        snapshot = MetricsSnapshot(
            timestamp=time.time(),
            metrics={name: metric},
        )
        self._registry.record_metric_snapshot(snapshot)
        return metric

    def calculate_system_health(self, active_metrics: Dict[str, float]) -> str:
        """Analyze active metrics to compute overall health classification."""
        latency = active_metrics.get("latency_ms", 0.0)
        cpu = active_metrics.get("cpu_percent", 0.0)

        if latency > 200.0 or cpu > 90.0:
            return "CRITICAL"
        elif latency > 100.0 or cpu > 75.0:
            return "DEGRADED"
        return "HEALTHY"

    def evaluate_alerts(
        self,
        active_metrics: Dict[str, float],
        thresholds: List[MetricsThreshold],
    ) -> List[MetricsAlert]:
        """Verify metric violations against thresholds and record alerts."""
        alerts: List[MetricsAlert] = []
        for thresh in thresholds:
            val = active_metrics.get(thresh.metric_name)
            if val is not None:
                if val > thresh.error_limit:
                    alert = MetricsAlert(
                        metric_name=thresh.metric_name,
                        observed_value=val,
                        threshold_value=thresh.error_limit,
                        severity="ERROR",
                        explanation=f"Metric '{thresh.metric_name}' is currently {val}, exceeding critical limit {thresh.error_limit}.",
                    )
                    self._registry.record_alert(alert)
                    alerts.append(alert)
                elif val > thresh.warning_limit:
                    alert = MetricsAlert(
                        metric_name=thresh.metric_name,
                        observed_value=val,
                        threshold_value=thresh.warning_limit,
                        severity="WARNING",
                        explanation=f"Metric '{thresh.metric_name}' is currently {val}, exceeding warning limit {thresh.warning_limit}.",
                    )
                    self._registry.record_alert(alert)
                    alerts.append(alert)
        return alerts

    def generate_dashboard_snapshot(self) -> DashboardSnapshot:
        """Aggregate recent metrics snapshots into a consolidated dashboard representation."""
        snapshots = self._registry.get_metric_snapshots()
        active_metrics: Dict[str, float] = {}

        series_data: Dict[str, List[float]] = {}
        series_times: Dict[str, List[float]] = {}
        for snap in snapshots:
            for name, metric in snap.metrics.items():
                active_metrics[name] = metric.value
                series_data.setdefault(name, []).append(metric.value)
                series_times.setdefault(name, []).append(metric.timestamp)

        series_list = [
            DashboardSeries(name=name, values=vals, timestamps=times)
            for name, (vals, times) in sorted(
                [(k, (series_data[k], series_times[k])) for k in series_data.keys()]
            )
        ]

        health_status = self.calculate_system_health(active_metrics)

        return DashboardSnapshot(
            timestamp=time.time(),
            health_status=health_status,
            active_metrics=active_metrics,
            series=series_list,
        )
