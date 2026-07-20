# ADR 0014 – Distributed Snapshot Replication & Log Compaction

**Date**: 2026-07-20  
**Status**: Accepted  
**Phase**: 14 – Distributed Snapshot Replication & Log Compaction  
**Milestone**: E – Distributed Reliability & Production Features  

---

## Context

In standard Raft consensus, the log grows indefinitely as commands are submitted. Over time, this unbounded growth consumes storage capacity and makes recovery processes extremely slow (since a booting node has to replay the entire history of committed entries).

To maintain production-grade efficiency, the system must support **Log Compaction** (Raft §7), which discards old committed entries whose state has already been captured inside verified snapshots. Furthermore, when a lagging or new node joins the cluster, transferring millions of obsolete log entries is wasteful; the leader must instead replicate the snapshot directly using an incremental chunked replication stream (**InstallSnapshot**).

---

## Decision

We implement a complete **Distributed Snapshot Replication and Log Compaction** architecture:

1. **SnapshotStorage**: Retains snapshot metadata records, checks SHA-256 payload integrity, and implements configurable history retention policies.
2. **LogCompactor**: Safely discards entries from the `ConsensusLog` up to the latest snapshot's applied index, while preserving Raft invariants by storing `last_included_index` and `last_included_term`.
3. **SnapshotReplicator**: Splits snapshots into uniform chunks, streams them incrementally using `SNAPSHOT_CHUNK` packets, and handles reassembly, checksum validation, and out-of-order packet rejection.
4. **SnapshotService**: Coordinates triggers (e.g. log thresholds), triggers state compaction, handles leader-to-follower installation handshakes, and restores state machine contexts atomically.

### InstallSnapshot Protocol Integration
When a follower lags significantly behind the leader's truncated log, the leader initiates snapshot replication:
- Streams manifest descriptors via `SNAPSHOT_INSTALL_REQUEST`.
- Transmits sequential binary blocks using `SNAPSHOT_CHUNK` frames.
- FOLLOWERS reconstruct the payload, verify chunk checksums, invoke FSM snapshot restoration, and execute log compaction to clear obsolete history.

### Verification and Rollbacks
By validating SHA-256 checksums at chunk, manifest, and assembly boundaries, we prevent corrupted transfers from being imported into the state store. Historic snapshot tracking supports automatic cleanup of obsolete data while maintaining previous versions for safety rollbacks.

---

## Consequences

- **Bounded Log Size**: Log segments are truncated, ensuring stable disk usage.
- **Fast Bootstrap**: New or partitioned nodes catch up quickly via snapshot sync instead of log replay.
- **Chunked Resilience**: Segmenting large snapshots into uniform packages prevents network buffer exhaustion and supports high-throughput cluster links.
