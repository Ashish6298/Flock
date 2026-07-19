# ADR 0011: Distributed Retry & Recovery Engine

## Context & Problem Statement
With Milestone D complete, Flock is capable of scheduled placements, executions, and result deliveries. However, a production-grade distributed system must handle network splits and task worker failures. Flock requires a transport-independent Retry & Recovery engine to re-run placements, schedule backoffs, and mark unrecoverable tasks as dead letter.

## Selected Solution
We implement:
1. **RetryPolicy**: Configurable max attempts and backoff strategies (Fixed, Linear, Exponential with randomized Jitter).
2. **RecoveryRegistry**: Tracks retry contextual metrics and active failover cooldown node exclusions.
3. **RecoveryEngine**: Integrates with the scheduler and placement layers to route failed tasks to alternate active nodes.
4. **RecoveryService**: API wrapping failover handshakes (`TASK_RECOVERY_REQUEST`, `TASK_RECOVERY_ACK`).

## Consequences & Trade-offs
- Task retry actions run on the scheduling coordinator rather than local worker loop layers.
- Simple cooldown node exclusion satisfies Milestone E, preparing for future replicated consensus ledgers.
