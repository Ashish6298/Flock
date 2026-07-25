# Milestone B — Observability & Visualization Changelog

All notable changes implemented for Milestone B are documented below.

## [1.1.0] - 2026-07-26

### Added
- Centralized metrics registry in `flock.observability.registry` tracking counters and rates.
- Telemetry collector engine `TelemetryCollector` registering named callables.
- WebSocket broadcaster manager supporting broadcast pools.
- Telemetry dashboard adapter translating raw statistics into visual panel widgets.
- Complete unit and integration tests verifying all metrics aggregation and WebSocket flows.
