# ADR 0034 – Distributed Observability, Monitoring & Telemetry Platform

**Date**: 2026-07-22
**Status**: Accepted
**Phase**: 34 – Distributed Observability, Monitoring & Telemetry Platform
**Milestone**: K – Full-Platform Observability & Operations

---

## Context

Phase 16 delivered a foundational observability package with a basic metrics
registry, span-based tracing, health monitoring, and Prometheus/JSON export.
After 17 additional phases (17–33) added security, resource management,
orchestration, federation, workflow, scheduling, streaming, API gateway, plugins,
service mesh, deployment, serverless, data grid, query engine, AI intelligence,
CLI, and dashboard, the platform lacked:

- Extended metric instruments (EMA, rolling windows, throughput counters, latency percentiles)
- Structured JSON logging with search, pagination, and correlation identifiers
- A pluggable telemetry collector aggregating data from any registered producer
- Sliding-window aggregation with anomaly baselines and trend detection
- TTL-based retention management with archival hooks
- Multi-strategy trace sampling (probabilistic, adaptive, rule-based)
- An observability-native alert manager (distinct from the dashboard alert engine)
- Lightweight profiling via context managers with hotspot ranking
- A clean adapter to push live telemetry into the Phase 33 dashboard

## Decision

Extended `src/flock/observability/` with 8 new production modules alongside the
existing Phase 16 files.  All new code is fully backward compatible; the existing
`MetricsRegistry`, `TracingEngine`, `HealthMonitor`, `TelemetryExporter`,
`TelemetryAggregator`, and `ObservabilityService` are unchanged.

| New Module | Primary Class | Responsibility |
|---|---|---|
| `metrics.py` | `MetricsEngine` | EMA, rolling windows, throughput, latency percentiles |
| `logging.py` | `StructuredLogger` | Severity-filtered JSON logging, search, pagination |
| `collector.py` | `TelemetryCollector` | Named producer registry + batch collection |
| `aggregation.py` | `AggregationEngine` | Sliding-window stats, anomaly baselines, trend analysis |
| `retention.py` | `RetentionManager` | TTL eviction, capacity enforcement, archival |
| `sampling.py` | `SamplingEngine` | Probabilistic/adaptive/rule-based trace sampling |
| `alerts.py` | `ObservabilityAlertManager` | Threshold alerts with cooldown, suppression, lifecycle |
| `profiling.py` | `ProfilingEngine` | Context-manager timing, percentile summaries, hotspots |
| `dashboard.py` | `DashboardTelemetryAdapter` | Bridge to Phase 33 dashboard data sources |

Protocol packet extended with:
- Phase 33 types: `DASHBOARD_*` (252–261)
- Phase 34 types: `TELEMETRY_SUBMIT` through `OBSERVABILITY_STATE_SYNC` (262–271)

## Consequences

**Positive**
- Unified observability pipeline; every Flock subsystem can now register a
  telemetry producer and contribute to centralised collection
- Dashboard adapter connects Phase 34 pipeline directly to Phase 33 visual layer
  without coupling HTTP concerns to observability logic
- Anomaly detection and trend analysis provide the AI subsystem (Phase 31) with
  ready-made signals for predictive scheduling

**Negative**
- Anomaly baseline requires at least 2 samples with non-zero standard deviation
  before detecting outliers; constant-valued metrics will never trigger anomaly
  detection (expected behaviour, documented in module docstrings)
- Sampling engine uses `random.random()` which is not cryptographically secure;
  for security-sensitive trace sampling a CSPRNG should be substituted
