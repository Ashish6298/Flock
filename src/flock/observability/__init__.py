"""Flock Observability Subsystem.

Phase 16 – Distributed Observability, Metrics & Telemetry Framework (core)
Phase 34 – Distributed Observability, Monitoring & Telemetry Platform (extended)

Public API
----------
**Phase 16 (core)**

:class:`MetricsRegistry`
    Thread-safe counter/gauge/histogram registry.

:class:`TelemetryAggregator`
    EventBus-driven aggregator that subscribes to Flock lifecycle events.

:class:`TracingEngine`
    Distributed tracing with parent-child span hierarchies.

:class:`HealthMonitor`
    Node health evaluator producing :class:`NodeHealthReport`.

:class:`TelemetryExporter`
    JSON and Prometheus text format export.

:class:`ObservabilityService`
    Async lifecycle orchestrator wiring all Phase 16 subsystems.

**Phase 34 (extended)**

:class:`MetricsEngine`
    EMA, rolling windows, throughput counters, latency percentiles.

:class:`StructuredLogger`
    Severity-filtered structured JSON logging with search/pagination.

:class:`TelemetryCollector`
    Named producer registry with batch collection and history.

:class:`AggregationEngine`
    Sliding-window stats, anomaly baselines, trend analysis.

:class:`RetentionManager`
    TTL-based record eviction, capacity enforcement, archival hooks.

:class:`SamplingEngine`
    Probabilistic/adaptive/rule-based trace sampling.

:class:`ObservabilityAlertManager`
    Threshold alerts with cooldown, suppression, and ack/resolve lifecycle.

:class:`ProfilingEngine`
    Lightweight profiling with context manager and hotspot ranking.

:class:`DashboardTelemetryAdapter`
    Bridge between Phase 34 observability and Phase 33 dashboard sources.

Exceptions
----------
All exceptions are importable from :mod:`flock.observability.exceptions`.
"""

# Phase 16 – core
from flock.observability.exceptions import (
    TelemetryError,
    ExporterError,
    InvalidMetricError,
    AggregationError,
    LoggingError,
    CollectorError,
    RetentionError,
    SamplingError,
    AlertError,
    AlertRuleNotFoundError,
    ProfilingError,
    HealthCheckError,
    DashboardAdapterError,
)
from flock.observability.models import (
    MetricType,
    MetricValue,
    Span,
    NodeHealthReport,
    ClusterHealthReport,
)
from flock.observability.registry import MetricsRegistry
from flock.observability.aggregator import TelemetryAggregator
from flock.observability.tracing import TracingEngine
from flock.observability.health import HealthMonitor
from flock.observability.exporter import TelemetryExporter
from flock.observability.service import ObservabilityService

# Phase 34 – extended
from flock.observability.metrics import (
    MetricsEngine,
    MovingAverage,
    RollingWindow,
    ThroughputCounter,
    LatencyTracker,
)
from flock.observability.logging import (
    LogLevel,
    LogRecord,
    StructuredLogger,
)
from flock.observability.collector import (
    TelemetryBatch,
    TelemetryCollector,
)
from flock.observability.aggregation import (
    AggregationEngine,
    AnomalyBaseline,
    TrendAnalyzer,
    WindowedAggregation,
)
from flock.observability.retention import (
    RetentionManager,
    RetentionPolicy,
    RetentionStore,
)
from flock.observability.sampling import (
    SamplingDecision,
    SamplingEngine,
    SamplingRule,
    SamplingStrategy,
)
from flock.observability.alerts import (
    AlertIncident,
    AlertRule,
    AlertSeverity,
    AlertState,
    ObservabilityAlertManager,
)
from flock.observability.profiling import (
    ProfilingEngine,
    ProfilingSnapshot,
)
from flock.observability.dashboard import DashboardTelemetryAdapter

__all__ = [
    # Exceptions
    "TelemetryError",
    "ExporterError",
    "InvalidMetricError",
    "AggregationError",
    "LoggingError",
    "CollectorError",
    "RetentionError",
    "SamplingError",
    "AlertError",
    "AlertRuleNotFoundError",
    "ProfilingError",
    "HealthCheckError",
    "DashboardAdapterError",
    # Phase 16 models
    "MetricType",
    "MetricValue",
    "Span",
    "NodeHealthReport",
    "ClusterHealthReport",
    # Phase 16 services
    "MetricsRegistry",
    "TelemetryAggregator",
    "TracingEngine",
    "HealthMonitor",
    "TelemetryExporter",
    "ObservabilityService",
    # Phase 34 – metrics
    "MetricsEngine",
    "MovingAverage",
    "RollingWindow",
    "ThroughputCounter",
    "LatencyTracker",
    # Phase 34 – logging
    "LogLevel",
    "LogRecord",
    "StructuredLogger",
    # Phase 34 – collector
    "TelemetryBatch",
    "TelemetryCollector",
    # Phase 34 – aggregation
    "AggregationEngine",
    "AnomalyBaseline",
    "TrendAnalyzer",
    "WindowedAggregation",
    # Phase 34 – retention
    "RetentionManager",
    "RetentionPolicy",
    "RetentionStore",
    # Phase 34 – sampling
    "SamplingDecision",
    "SamplingEngine",
    "SamplingRule",
    "SamplingStrategy",
    # Phase 34 – alerts
    "AlertIncident",
    "AlertRule",
    "AlertSeverity",
    "AlertState",
    "ObservabilityAlertManager",
    # Phase 34 – profiling
    "ProfilingEngine",
    "ProfilingSnapshot",
    # Phase 34 – dashboard adapter
    "DashboardTelemetryAdapter",
]
