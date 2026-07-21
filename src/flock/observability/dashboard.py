"""Dashboard Telemetry Adapter – Phase 34.

Bridges the observability pipeline with the Phase 33 dashboard subsystem
by supplying live telemetry streams, health summaries, topology metrics,
alert summaries, and resource utilisation panels as dashboard data
source results.

The adapter is intentionally decoupled from the dashboard HTTP layer;
it produces :class:`~flock.dashboard.models.DataSourceResult` instances
that any dashboard data-source consumer can query.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from flock.dashboard.models import DataSourceResult, MetricDataPoint
from flock.observability.aggregation import AggregationEngine
from flock.observability.alerts import ObservabilityAlertManager
from flock.observability.collector import TelemetryCollector
from flock.observability.exceptions import DashboardAdapterError
from flock.observability.logging import StructuredLogger
from flock.observability.metrics import MetricsEngine
from flock.observability.profiling import ProfilingEngine
from flock.observability.registry import MetricsRegistry


class DashboardTelemetryAdapter:
    """Supplies real-time telemetry data to the dashboard data-source layer.

    Each public method returns a :class:`DataSourceResult` that can be
    registered as a dashboard data source callable.  The adapter wraps
    the observability subsystems and translates their outputs into the
    :class:`MetricDataPoint` format expected by the dashboard renderer.

    Attributes:
        _registry: Phase 16 metrics registry.
        _engine: Phase 34 extended metrics engine.
        _aggregation: Aggregation engine.
        _collector: Telemetry collector.
        _alerts: Alert manager.
        _logger: Structured logger.
        _profiler: Profiling engine.
    """

    def __init__(
        self,
        registry: MetricsRegistry,
        engine: MetricsEngine,
        aggregation: AggregationEngine,
        collector: TelemetryCollector,
        alerts: ObservabilityAlertManager,
        logger: StructuredLogger,
        profiler: ProfilingEngine,
    ) -> None:
        """Initialise the adapter."""
        self._registry: MetricsRegistry = registry
        self._engine: MetricsEngine = engine
        self._aggregation: AggregationEngine = aggregation
        self._collector: TelemetryCollector = collector
        self._alerts: ObservabilityAlertManager = alerts
        self._logger: StructuredLogger = logger
        self._profiler: ProfilingEngine = profiler

    # ------------------------------------------------------------------
    # Data source callables
    # ------------------------------------------------------------------

    def metrics_source(self) -> DataSourceResult:
        """Return all registry metrics as dashboard data points.

        Returns:
            :class:`DataSourceResult` with one point per metric.
        """
        try:
            points: List[MetricDataPoint] = []
            for mv in self._registry.list_metrics():
                points.append(
                    MetricDataPoint(
                        timestamp=mv.timestamp,
                        metric_name=mv.name,
                        value=mv.value,
                        labels=mv.labels,
                    )
                )
            return DataSourceResult(
                source_name="observability.metrics",
                data_points=points,
            )
        except Exception as exc:
            raise DashboardAdapterError(
                f"metrics_source failed: {exc}"
            ) from exc

    def aggregation_source(self) -> DataSourceResult:
        """Return aggregation engine latests as dashboard data points.

        Returns:
            One :class:`MetricDataPoint` per tracked metric (latest value).
        """
        try:
            points: List[MetricDataPoint] = []
            for name in self._aggregation.list_metrics():
                s = self._aggregation.summary(name)
                if s:
                    points.append(
                        MetricDataPoint(
                            timestamp=time.time(),
                            metric_name=name,
                            value=s.get("latest", 0.0),
                        )
                    )
            return DataSourceResult(
                source_name="observability.aggregation",
                data_points=points,
            )
        except Exception as exc:
            raise DashboardAdapterError(
                f"aggregation_source failed: {exc}"
            ) from exc

    def alert_summary_source(self) -> DataSourceResult:
        """Return a data point per active alert severity count.

        Returns:
            Points for ``alert.info``, ``alert.warning``, ``alert.critical``.
        """
        try:
            firing = self._alerts.get_firing()
            counts: Dict[str, float] = {
                "alert.info": 0.0,
                "alert.warning": 0.0,
                "alert.critical": 0.0,
            }
            for inc in firing:
                key = f"alert.{inc.severity.value}"
                counts[key] = counts.get(key, 0.0) + 1.0

            now = time.time()
            points = [
                MetricDataPoint(
                    timestamp=now, metric_name=k, value=v
                )
                for k, v in counts.items()
            ]
            return DataSourceResult(
                source_name="observability.alerts",
                data_points=points,
            )
        except Exception as exc:
            raise DashboardAdapterError(
                f"alert_summary_source failed: {exc}"
            ) from exc

    def profiling_source(self) -> DataSourceResult:
        """Return profiling mean-durations as dashboard data points.

        Returns:
            One :class:`MetricDataPoint` per profiled operation.
        """
        try:
            now = time.time()
            points: List[MetricDataPoint] = []
            for op in self._profiler.list_operations():
                s = self._profiler.summary(op)
                if s:
                    points.append(
                        MetricDataPoint(
                            timestamp=now,
                            metric_name=op,
                            value=s.get("mean", 0.0),
                        )
                    )
            return DataSourceResult(
                source_name="observability.profiling",
                data_points=points,
            )
        except Exception as exc:
            raise DashboardAdapterError(
                f"profiling_source failed: {exc}"
            ) from exc

    def log_count_source(self) -> DataSourceResult:
        """Return a single data point with the current buffered log count.

        Returns:
            One :class:`MetricDataPoint` for ``log.buffer.count``.
        """
        count = float(self._logger.count())
        return DataSourceResult(
            source_name="observability.logs",
            data_points=[
                MetricDataPoint(
                    timestamp=time.time(),
                    metric_name="log.buffer.count",
                    value=count,
                )
            ],
        )

    def collector_source(self) -> DataSourceResult:
        """Return telemetry batch producer count as a dashboard point.

        Returns:
            One :class:`MetricDataPoint` for ``telemetry.producers``.
        """
        return DataSourceResult(
            source_name="observability.collector",
            data_points=[
                MetricDataPoint(
                    timestamp=time.time(),
                    metric_name="telemetry.producers",
                    value=float(self._collector.count()),
                )
            ],
        )

    # ------------------------------------------------------------------
    # Registration helper
    # ------------------------------------------------------------------

    def register_all(
        self, datasource_manager: Any
    ) -> None:
        """Register all adapter data sources with a DataSourceManager.

        Args:
            datasource_manager: A
                :class:`~flock.dashboard.datasources.DataSourceManager`
                instance to register sources with.
        """
        datasource_manager.register(
            "observability.metrics", self.metrics_source
        )
        datasource_manager.register(
            "observability.aggregation", self.aggregation_source
        )
        datasource_manager.register(
            "observability.alerts", self.alert_summary_source
        )
        datasource_manager.register(
            "observability.profiling", self.profiling_source
        )
        datasource_manager.register(
            "observability.logs", self.log_count_source
        )
        datasource_manager.register(
            "observability.collector", self.collector_source
        )
