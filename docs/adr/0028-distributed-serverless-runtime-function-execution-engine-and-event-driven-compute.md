# ADR 0028 – Distributed Serverless Runtime, Function Execution Engine & Event-Driven Compute

**Date**: 2026-07-21  
**Status**: Accepted  
**Phase**: 28 – Distributed Serverless Runtime, Function Execution Engine & Event-Driven Compute  
**Milestone**: J – Distributed Workflow Orchestration  

---

## Context

Flock requires an on-demand serverless execution model to trigger short-lived lightweight operations globally without provisioning static container runtimes.

---

## Decision

We implement a complete **Distributed Serverless Runtime, Function Execution Engine & Event-Driven Compute**:

1. **FunctionRegistry**: Tracks definitions and handler codes.
2. **RuntimeEngine**: Safely evaluates function logic isolated.
3. **InvocationEngine**: Directs incoming invocations to the runtime.
4. **TriggerEngine**: Maps EventBus events or HTTP inputs to functions.
5. **AutoScalingEngine**: Computes target replicas dynamically.
6. **FunctionVersionManager**: Implements percentage-based traffic splits.
7. **ExecutionRecorder**: Logs historical metrics and logs outcomes.
8. **FunctionService**: Listens to sync actions on the MessageBus.

---

## Consequences

- **Secure Execution**: Isolated scope execution prevents rogue function runs from modifying core module properties.
- **Canary Routing**: Splits incoming function requests across aliases using percentage weights.
- **Durable Logging**: Keeps record logs inside the Persistent Storage subsystem.
