# ADR 0013 – Replicated Distributed State Machine & Metadata Store

**Date**: 2026-07-20  
**Status**: Accepted  
**Phase**: 13 – Replicated Distributed State Machine & Metadata Store  
**Milestone**: E – Distributed Reliability & Production Features  

---

## Context

Flock requires a strongly consistent, replicated store to manage authoritative cluster metadata (e.g. active tasks, scheduler states, placement constraints, and worker records). Ad-hoc memory sharing or eventually consistent strategies run the risk of state corruption, split-brain coordination, and divergent state updates when network partitions or leader failovers happen.

To address this, we build a Replicated State Machine (RSM) on top of the Raft Consensus engine implemented in Phase 12. Every state change is serialized into a deterministic command, committed to the Raft log, and subsequently applied to an identical local memory store on every node in exactly the same sequence.

---

## Decision

We implement a **Deterministic Replicated State Machine** architecture comprising:
1. `StateCommand`: Schema defining the operation, key, value, and client-provided command UUID.
2. `ReplicatedStateStore`: A thread-safe, purely memory-based store implementing core operations: `PUT`, `UPDATE`, `DELETE`, `UPSERT`, `INCREMENT`, `APPEND`, `SET_ADD`, `SET_REMOVE`, `MAP_PUT`, `MAP_DELETE`.
3. `StateMachineEngine`: Coordinates raw commit byte processing, validates indices sequentially, manages duplicate cache records (for idempotency), executes operations against the store, and manages applied index version tracking.
4. `StateMachineService`: Integrates with the Consensus log commit notification hook via the local EventBus, exposes clean submission, read, and snapshot APIs to other packages.

### Deterministic Command Execution
All mutations are strictly bound to Raft logs. A transaction is only executed against the state machine store *after* the corresponding log index has been safely committed across a quorum of consensus participants. No framework components are allowed to modify the state store directly, guaranteeing that all nodes reach consensus before applying state transitions.

### Idempotence and Retries
To ensure that client retries or network retry storms do not result in duplicate state modifications (e.g. double increments or duplicate list appends), every `StateCommand` carries a unique `command_id`. The engine maintains a cache of executed command IDs. If a duplicate command ID is received, it is ignored by the state store, but the log applied index is advanced normally to prevent the consensus commit pipeline from blocking.

### Snapshot Architecture
Large log files degrade recovery performance. We implement a local snapshotting model where the current store contents are serialized alongside metadata (applied index, current term, checksum). Checksums are generated dynamically using stable sorted key-value structures, enabling remote nodes to verify state equivalence before importing a state block.

---

## Design Choices & Rationale

- **Memory-based Store**: Using in-memory dicts with a synchronization lock ensures extremely low latency reads while writing commands sequentially.
- **Strict Separation of Concerns**: The storage engine is entirely unaware of the transport layer, protocol messages, or scheduler business logic. It operates purely on basic operations (`PUT`, `INCREMENT`, etc.), ensuring it remains highly reusable.
- **Dynamic Collection Primitives**: Beyond simple string key-value storage, adding native support for arrays, sets, and maps allows complex structures (like peer catalogs, worker descriptors, or task tables) to be replicated with minimal serialization overhead.

---

## Consequences

- **Consistent Metadata**: All nodes have access to a verified, duplicate-filtered, identical metadata catalog.
- **Read Scalability**: Because the state store is updated on every node through Raft replication, local nodes can fulfill read requests (`get()`, `exists()`, etc.) instantly without invoking network consensus.
- **Commit Latency**: Write requests (`submit_command()`) must undergo a complete Raft replication loop before completing, binding write performance directly to network round-trip time.
