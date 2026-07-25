# Milestone B — Observability & Visualization Architecture Report

---

## 1. Executive Summary
This report analyzes the software architecture, design principles, and decoupling strategies implemented in Flock's observability and dashboard pipelines.

---

## 2. Telemetry Pipeline Architecture

The complete observability pipeline flows linearly from core runtime engines down to visual dashboard consumers:

```
    [ Core Distributed Runtime ] (Consensus, Scheduler, DataGrid)
                 │
                 ▼ (Record metrics/logs)
         [ Metrics Registry ] (Thread-safe registry database)
                 │
                 ▼ (Calculates rates, counters, RAM utilization)
          [ Metrics Engine ]
                 │
                 ▼ (Asynchronously invokes named producers)
        [ Telemetry Collector ]
                 │
                 ▼ (Applies window averages & summaries)
        [ Aggregation Engine ]
                 │
                 ▼ (Applies TTL retention pruning)
        [ Retention Engine ]
                 │
                 ▼ (Wraps metrics as MetricDataPoints)
     [ Dashboard Telemetry Adapter ]
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
 [ Terminal TUI ]     [ Dashboard Service ]
 (flock CLI)          (websocket/REST APIs)
```

### Layer Responsibilities
1. **Metrics Registry (`flock.observability.registry`)**: Stores telemetry points in a thread-safe registry protected by a `threading.RLock`.
2. **Metrics Engine (`flock.observability.metrics`)**: Computes time-series states (e.g. system usage, heartbeats latencies).
3. **Telemetry Collector (`flock.observability.collector`)**: Aggregates batch snapshots on-demand from registered named producers.
4. **Dashboard Telemetry Adapter (`flock.observability.dashboard`)**: The bridge adapter. Translates raw collectors data into dashboard-native `DataSourceResult` formats.
5. **Dashboard Service (`flock.dashboard.service`)**: Manages WebSocket broad-casting pipelines, panel definitions, alerts, and sessions.

---

## 3. Design Guarantees & Thread Safety
- **Lock Protection**: All registry entries, collections buffers, and session lists use dedicated `threading.RLock` contexts, ensuring thread-safe access from concurrent background cluster routines.
- **Strict Decoupling**: Visualizers read metrics exclusively via the `DashboardTelemetryAdapter`, preventing the dashboard from directly inspecting or lock-blocking the core distributed runtime loops.

================================================================================
ARCHITECTURE CERTIFIED: 2026-07-26
================================================================================
