# ADR 0015 – Persistent Storage Engine & Write-Ahead Logging (WAL)

**Date**: 2026-07-20  
**Status**: Accepted  
**Phase**: 15 – Persistent Storage Engine & Write-Ahead Logging (WAL)  
**Milestone**: E – Distributed Reliability & Production Features  

---

## Context

Flock requires a production-grade, crash-safe storage layout to ensure that committed consensus logs, state machine updates, and replication snapshots survive process shutdowns, crashes, and hardware failures. 

To address this, we build a Write-Ahead Log (WAL) that captures mutations sequentially, persistent metadata indexing capabilities, and a structured recovery loop that reconstructs FSM states on startup.

---

## Decision

We implement a **Durable persistence engine and Write-Ahead Logging (WAL)**:

1. **WriteAheadLog (WAL)**: Stores transaction entries on disk. Ensures checksum integrity using SHA-256 hashes generated from payload, index, and term contents. Rotates segments when they exceed configured size limits.
2. **FileStorageBackend**: A local filesystem implementation of the pluggable `StorageBackend` abstraction. Performs writes atomically by writing to temporary files and renaming them into place.
3. **RecoveryEngine**: Initiates startup state reconstructions by restoring the latest verified checkpoint snapshot, replaying trailing WAL records, and updating FSM state machines sequentially.
4. **StorageService**: Coordinates background WAL appends, registers storage health query message endpoints, and publishes EventBus lifecycle updates.

### Atomic Swaps & Fsync Safety
To guarantee disk consistency during half-written files or unexpected power outages:
- Every metadata or state segment write is staged inside temporary staging files.
- Renames are executed using atomic operations (`shutil.move`), ensuring the disk never holds a corrupt manifest.
- Checkpoint indexes bind compaction truncation points directly to verified FSM snapshot persistence boundaries.

---

## Consequences

- **Durability Invariant**: Commits are durably registered before execution acknowledgment.
- **Crash Recovery**: Disrupted state machines recover automatically up to the last written log entry.
- **Pluggable Storage**: The abstract `StorageBackend` interface permits replacing filesystem storage with SQLite or key-value engines (e.g. RocksDB) in the future without changing higher-level services.
