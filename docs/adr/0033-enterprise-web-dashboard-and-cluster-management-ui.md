# ADR 0033 – Enterprise Web Dashboard & Distributed Cluster Management UI

**Date**: 2026-07-21
**Status**: Accepted
**Phase**: 33 – Enterprise Web Dashboard & Distributed Cluster Management UI
**Milestone**: K – Full-Platform Observability & Operations

---

## Context

After completing 32 phases of Flock development—including networking, consensus,
workflow, federation, scheduling, streaming, API gateway, plugin runtime, service
mesh, deployment, serverless functions, data grid, query engine, AI intelligence,
and the CLI—operators and developers lacked a visual, browser-based interface for
monitoring and managing the cluster in real time.

The dashboard subsystem must provide:
- Real-time cluster health and node status visibility
- Widget-based panel composition with per-role access control
- Pluggable metric data sources mapped to widget types
- Alert rule evaluation with threshold-based event dispatch
- Authenticated session management with TTL expiry
- UI theme management (dark, light, midnight, custom)
- Data export in JSON, CSV, and report formats
- Real-time push via WebSocket channel fan-out

## Decision

Implemented `src/flock/dashboard/` as a fully transport-independent, thread-safe
Python subsystem with the following modules:

| Module | Responsibility |
|---|---|
| `exceptions.py` | Exception hierarchy (12 typed exceptions) |
| `models.py` | Pydantic v2 frozen models (17 models) |
| `widgets.py` | WidgetRegistry – CRUD + type/source filtering |
| `panels.py` | PanelRegistry – CRUD + RBAC access control |
| `datasources.py` | DataSourceManager – named callable registry + safe querying |
| `renderer.py` | DashboardRenderer – 6 widget-type strategies |
| `alerts.py` | AlertEngine – threshold evaluation + handler dispatch |
| `sessions.py` | SessionManager – TTL sessions + purge |
| `themes.py` | ThemeManager – 3 built-in + custom themes |
| `exporter.py` | ExportEngine – JSON/CSV/PDF-stub/PNG-stub |
| `websocket.py` | WebSocketBroadcaster – channel fan-out + error isolation |
| `handlers.py` | DashboardApiHandler – REST facade wiring all subsystems |
| `service.py` | DashboardService – top-level lifecycle orchestrator |
| `__init__.py` | Full public API surface with `__all__` |

## Consequences

**Positive**:
- Clean separation of concerns – each module is independently testable
- Transport-independent design – HTTP, WebSocket, gRPC can all drive the handler
- Thread-safe – all registries use `threading.RLock`
- Zero external dependencies beyond Pydantic v2

**Negative**:
- PDF/PNG export are text stubs; a headless renderer (Playwright/WeasyPrint)
  must be integrated for production PDF/PNG output
- WebSocket broadcaster is in-process; production scale requires a pub/sub bus
  (e.g. the Streaming subsystem from Phase 23)
