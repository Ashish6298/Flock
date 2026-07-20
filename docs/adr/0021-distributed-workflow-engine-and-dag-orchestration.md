# ADR 0021 – Distributed Workflow Engine & DAG Orchestration

**Date**: 2026-07-20  
**Status**: Accepted  
**Phase**: 21 – Distributed Workflow Engine & DAG Orchestration  
**Milestone**: J – Distributed Workflow Orchestration  

---

## Context

Flock requires a distributed workflow engine capable of defining, validating, planning, executing, checkpointing, and recovering task-dependency graphs (DAGs) across cluster nodes without introducing dependencies on specific network transports.

---

## Decision

We implement a complete **Distributed Workflow Engine & DAG Orchestration**:

1. **WorkflowGraphEngine**: Performs topological sorting to resolve task execution orders, detecting circular dependency loops.
2. **WorkflowPlanner**: Maps topologically sorted nodes into discrete sequential planning stages.
3. **WorkflowCheckpointManager**: Atomically serializes execution progress snapshots on durable storage.
4. **WorkflowExecutor**: Coordinates task execution loops, executing checkpoints on each completed step.
5. **WorkflowService**: Integrates workflow submissions and registers network ports on the message bus.

---

## Consequences

- **DAG Safety**: Prevents deadlock tasks from scheduling by rejecting cycle loops.
- **Failover Resiliency**: Interrupted workflows resume execution from the last written node checkpoint.
- **High Concurrency**: Independent execution paths are isolated to run concurrently when dependencies are satisfied.
