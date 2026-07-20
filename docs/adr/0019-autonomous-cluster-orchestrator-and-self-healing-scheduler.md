# ADR 0019 – Autonomous Cluster Orchestrator & Self-Healing Scheduler

**Date**: 2026-07-20  
**Status**: Accepted  
**Phase**: 19 – Autonomous Cluster Orchestrator & Self-Healing Scheduler  
**Milestone**: H – Cluster Operations & Resource Management  

---

## Context

Flock requires a self-healing cluster coordination layer capable of executing policy evaluations, directing live task migrations, and issuing autoscaling limits out-of-band without coupling to transport sockets.

---

## Decision

We implement a complete **Autonomous Cluster Orchestrator & Self-Healing Scheduler**:

1. **PolicyEngine**: Houses default policies (balanced, low latency, etc.) and tests skew violation bounds.
2. **AutonomousScheduler**: Dispatches migration events and monitors pre-check state validation gates.
3. **OptimizationEngine**: Generates target optimization plans.
4. **AutoScaler**: Generates scale-out and scale-in recommendations bounded by configured min/max limits.
5. **OrchestratorService**: Coordinates policy synchronization queries.

---

## Consequences

- **Self-Healing Scheduling**: Relocates workloads reactively when node capacities are pressured.
- **Durable Policy Configuration**: Synchronizes strategies across the cluster.
- **Isolated Actions**: Rebalancing plans are calculated and recommendations issued without side-effects on active socket transports.
