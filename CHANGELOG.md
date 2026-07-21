## [0.34.0] - 2026-07-22

### Phase 34 - Distributed Observability, Monitoring & Telemetry Platform

#### Added
- src/flock/observability/metrics.py: MetricsEngine, MovingAverage, RollingWindow, ThroughputCounter, LatencyTracker
- src/flock/observability/logging.py: StructuredLogger, LogRecord, LogLevel
- src/flock/observability/collector.py: TelemetryCollector, TelemetryBatch
- src/flock/observability/aggregation.py: AggregationEngine, WindowedAggregation, AnomalyBaseline, TrendAnalyzer
- src/flock/observability/retention.py: RetentionManager, RetentionPolicy, RetentionStore
- src/flock/observability/sampling.py: SamplingEngine, SamplingRule, SamplingDecision, SamplingStrategy
- src/flock/observability/alerts.py: ObservabilityAlertManager, AlertRule, AlertIncident, AlertSeverity, AlertState
- src/flock/observability/profiling.py: ProfilingEngine, ProfilingSnapshot
- src/flock/observability/dashboard.py: DashboardTelemetryAdapter (bridges Phase 34 to Phase 33)
- src/flock/protocol/packet.py: Message types 252-261 (Phase 33 Dashboard) and 262-271 (Phase 34 Observability)
- 152 new unit tests (10 test files) - 575 total; zero regressions
- ADR 0034, Phase 34 Audit Report, Retrospective, and Test Report

#### Changed
- src/flock/observability/exceptions.py: Added 9 new exception classes
- src/flock/observability/__init__.py: Extended to export all Phase 34 symbols

