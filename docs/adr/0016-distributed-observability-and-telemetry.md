# ADR 0016 – Distributed Observability, Metrics & Telemetry Framework

**Date**: 2026-07-20  
**Status**: Accepted  
**Phase**: 16 – Distributed Observability, Metrics & Telemetry Framework  
**Milestone**: F – Production Operations & Observability  

---

## Context

Flock requires comprehensive diagnostics, runtime telemetry, and hierarchical tracing capabilities to track asynchronous executions, measure scheduling latencies, and expose metrics to standard aggregators without introducing circular dependencies or degrading framework performance.

---

## Decision

We implement a complete **Distributed Observability, Metrics & Telemetry Framework**:

1. **MetricsRegistry**: A thread-safe, memory-efficient store for counters, gauges, histograms, summaries, and timers.
2. **TelemetryExporter**: Decoupled formatter providing Prometheus-compatible text layouts and standard structured JSON outputs.
3. **TracingEngine**: Tracks nested operations asynchronously using `Span` mappings, parent-child relationships, and unique trace IDs.
4. **HealthMonitor**: Dynamically evaluates node parameters (e.g. heartbeat delays, WAL errors) to assert liveness states ("HEALTHY", "DEGRADED", "UNHEALTHY").
5. **ObservabilityService**: Schedules telemetry processing, exposes metrics query message handler targets, and dispatches EventBus hooks.

### EventBus-Driven Instrumentation Philosophy
To prevent architectural pollution:
- Subsytems do not import the observability package.
- Subsytems dispatch standard event names (`consensus.log.committed`, `task.scheduled`, `task.execution.started`) onto the shared `EventBus`.
- The `TelemetryAggregator` listens to these events reactively, updating the central metrics database out-of-band.

---

## Consequences

- **Zero Coupling**: Business logic is decoupled from exporter details.
- **APM Integration**: Enables end-to-end task pipeline performance profiles.
- **Prometheus Scrapes**: Exposes standard endpoints for Prometheus or Grafana integration.
