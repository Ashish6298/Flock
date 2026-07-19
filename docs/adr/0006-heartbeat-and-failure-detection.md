# ADR 0006: Heartbeat & Failure Detection Subsystem

## Context & Problem Statement
With the peer discovery and cluster membership layers operational, Flock needs a deterministic, transport-independent health monitor to determine if registered cluster nodes are currently reachable and healthy.

## Selected Solution
We implement:
1. **HealthRegistry**: Container storing immutable `HealthRecord` objects containing states (`Healthy`, `Suspected`, `Unreachable`, `Recovering`).
2. **FailureDetector**: Compares missed heartbeat windows and transitions states, emitting event bus alerts (e.g. `heartbeat.node_suspected`, `heartbeat.node_unreachable`).
3. **HeartbeatService**: Sets background `asyncio.Task` loop scheduling ping messages to active nodes and processing return pongs.

## Consequences & Trade-offs
- Health updates are decoupled from membership registration; if a node becomes `UNREACHABLE`, it is flagged in the `HealthRegistry` and EventBus alerts are triggered, but the member record in `MembershipRegistry` is preserved to support automated reconnection loops.
- Localized evaluation loops are sufficient for local clusters; scale-out clusters will require gossip protocols in subsequent optimization phases.
