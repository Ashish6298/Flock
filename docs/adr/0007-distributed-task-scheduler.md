# ADR 0007: Distributed Task Scheduler Layer

## Context & Problem Statement
To distribute computational tasks among nodes, Flock requires a transport-independent task scheduling framework. The framework must accept task definitions, validate execution constraints, queue tasks deterministically according to scheduling policy, and track status lifecycle transitions.

## Selected Solution
We implement:
1. **Task**: An immutable task structure containing payload details, metadata, priority, constraints, and scheduling status enums.
2. **SchedulingQueue**: Supports FIFO and priority-based task sorting policies.
3. **TaskSchedulerService**: Coordinates local submissions, schema validations, queue placements, and EventBus status notifications (`scheduler.task_created`, `scheduler.task_queued`, etc.).

## Consequences & Trade-offs
- Task scheduling and storage remain transport-independent.
- The scheduler does not make placement decisions (node routing) or execute tasks. It only tracks scheduler status (Queued, Validated, Cancelled, Expired), preparing the foundation for future Task Placement and load balancing subsystems.
