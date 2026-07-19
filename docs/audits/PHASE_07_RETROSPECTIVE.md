# Phase 07 - Retrospective

## What Went Well
- **Priority Heap Inversion**: Inverting priority IntEnums to negative numbers within min-heaps easily implemented critical-first ordering.
- **State Machine Separation**: Keeping task scheduling states decoupled from execution running states prepared the codebase for simple placement extensions.

## Challenges & Solutions
- **Registry Status Propagation**: Submitting tasks initially returned outdated memory configurations. Fetching the updated descriptor from the registry before returning resolved the discrepancy.
- **mypy Heap Types**: Defining queue heaps explicitly as `List[Tuple[int, int, Task]]` satisfied strict type annotations.
