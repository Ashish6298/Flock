# ADR 0010: Result Collection & Completion Pipeline

## Context & Problem Statement
With scheduling, task placement, and worker runtimes operational, Flock needs a transport-independent, decentralized result collection subsystem. The subsystem must receive completed task outputs, collect execution failures, validate integrity parameters, register results securely, notify asynchronous clients, and clean up expired catalog records.

## Selected Solution
We implement:
1. **ExecutionResult** & **FailureResult**: Immutable representations of execution metrics.
2. **ResultSerializer**: Separated from transport layers, wrapping JSON and Msgpack formatters with SHA256 checksum validations.
3. **ResultRegistry**: Thread-safe async waiting registries completing waiting futures and evicting expired records under a configurable TTL.
4. **ResultCollector**: Listeners routing incoming `TASK_RESULT` network envelopes into the local registry.
5. **ResultService**: Orchestrator coordinating result transmissions (`submit_result`, `submit_failure`, `wait_for_result`).

## Consequences & Trade-offs
- Complete isolation between serialization formatting and TCP network socket loops.
- Storing returned values ephemerally in memory satisfies Milestone D, preparing for future persistent storage and fault recovery replication systems.
