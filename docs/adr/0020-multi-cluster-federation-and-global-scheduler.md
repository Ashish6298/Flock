# ADR 0020 – Multi-Cluster Federation & Global Scheduler

**Date**: 2026-07-20  
**Status**: Accepted  
**Phase**: 20 – Multi-Cluster Federation & Global Scheduler  
**Milestone**: I – Multi-Cluster Federation & Global Coordination  

---

## Context

Flock needs a decentralized multi-cluster federation framework to schedule workloads globally, maintain member cluster listings, and replicate state summaries without violating internal cluster boundaries or local Raft consensus loops.

---

## Decision

We implement a complete **Multi-Cluster Federation & Global Scheduler**:

1. **FederationRegistry**: Stores active cluster endpoints and capacity ratings.
2. **GlobalRoutingEngine**: Resolves target destinations based on capacity metrics.
3. **GlobalScheduler**: Handles global task scheduling assignments and logs.
4. **CrossClusterReplicationEngine**: Replicates snapshots out-of-band to target clusters.
5. **FederationService**: Exposes federation join network handler ports.

---

## Consequences

- **Local Autonomy**: Individual clusters maintain isolated Raft consensus loops.
- **Failover Capabilities**: Unhealthy target clusters are bypassed during task routing calculations.
- **High Scalability**: Spreads scheduling footprints globally across independent computing zones.
