# ADR 0012 – Distributed Raft Consensus Engine

**Date**: 2026-07-20  
**Status**: Accepted  
**Phase**: 12 – Distributed Consensus & Leader Election  
**Milestone**: E – Distributed Reliability & Production Features  

---

## Context

Flock is a brokerless, decentralised peer-to-peer task execution framework.  
Phases 1–11 established the complete distributed execution pipeline, including
transport, messaging, peer discovery, cluster membership, heartbeat, scheduling,
placement, worker runtime, result collection, and retry/recovery.

Phase 12 introduces the consensus layer required for:
- **Coordinator authority** – exactly one node must hold leadership at any time.
- **Ordering guarantees** – distributed decisions must be applied in the same
  order on all nodes.
- **Fault tolerance** – the cluster must continue operating when a minority of
  nodes fail.

A formal consensus protocol is required because ad-hoc "whoever answered first"
approaches produce split-brain conditions (multiple nodes believing they are the
coordinator) which are silent data-correctness bugs.

---

## Decision

We implement the **Raft** consensus algorithm as described in:

> "In Search of an Understandable Consensus Algorithm (Extended Version)"  
> Diego Ongaro and John Ousterhout, 2014.  
> https://raft.github.io/raft.pdf

Raft was selected over alternatives (see *Rejected Alternatives* below) because:
1. Its decomposition into three independent sub-problems (leader election, log
   replication, safety) maps directly onto clean, testable modules.
2. The leader-based architecture matches Flock's existing coordinator model.
3. Term-based authority is easy to reason about and audit.
4. The election protocol is stateless between terms, simplifying recovery.

---

## Architecture

### Module Decomposition

```
src/flock/consensus/
├── exceptions.py      – 7 typed exception classes
├── models.py          – 13 immutable Pydantic models
├── log.py             – ConsensusLog (thread-safe, 1-based indexing)
├── state_machine.py   – RaftStateMachine (role FSM, vote accounting)
├── election.py        – ElectionEngine (randomised timers, vote RPCs)
├── replication.py     – ReplicationEngine (AppendEntries RPCs)
└── service.py         – ConsensusService (orchestrator, 8 handlers)
```

### Dependency Hierarchy (no cycles)

```
ConsensusService
   ├── ElectionEngine     (reads ConsensusLog, mutates RaftStateMachine)
   ├── ReplicationEngine  (reads/writes ConsensusLog, mutates RaftStateMachine)
   └── RaftStateMachine   (owns RaftNodeState, vote accounting)
          └── ConsensusLog (thread-safe ordered log store)
```

The consensus package imports:
- `flock.events.bus.EventBus` (publishes events)
- `flock.messaging.bus.MessageBus` (dispatches RPCs)
- `flock.cluster.registry.MembershipRegistry` (peer enumeration)
- `flock.protocol.packet.MessageType` (8 new constants)

The consensus package does **not** import from: scheduler, placement, runtime,
recovery, or results packages. Dependency inversion is strictly enforced.

---

## Election Algorithm

### Randomised Timeout

Followers start with a randomised election timeout in [150ms, 300ms].
On expiry without receiving a valid AppendEntries RPC, the follower:
1. Increments `current_term` and transitions to CANDIDATE.
2. Votes for itself.
3. Broadcasts `RAFT_REQUEST_VOTE` to all known peers.
4. Restarts its election timer (for split-vote retry).

The range is configurable via `ConsensusService` constructor parameters.
All tests mock `asyncio.sleep` so no real wall-clock time is consumed.

### Vote Granting (Raft §5.2 + §5.4.1)

A follower grants a vote to candidate `C` iff:
1. `C.term >= localTerm` (term is current or advancing).
2. `voted_for is None OR voted_for == C.node_id` (one vote per term).
3. Candidate's log is at least as up-to-date:
   - `C.lastLogTerm > local.lastLogTerm`, OR
   - `C.lastLogTerm == local.lastLogTerm AND C.lastLogIndex >= local.lastLogIndex`.

Condition 3 is the **log completeness check** that ensures only nodes with
complete log histories can become leaders, preventing committed entries from
being lost.

### Quorum

```
quorum = cluster_size // 2 + 1
```

A candidate wins the election when `votes_received >= quorum` (strict majority).
For a 3-node cluster this requires 2 votes; for 5 nodes, 3 votes.

---

## Log Replication Strategy

### Leader-side (AppendEntries)

The leader maintains per-peer state:
- `nextIndex[peer]` – next log index to send to that peer (initialised to
  `last_log_index + 1` on election).
- `matchIndex[peer]` – highest log index known replicated on that peer
  (initialised to 0 on election).

On each heartbeat/replication cycle:
1. Construct `AppendEntriesRequest` with entries from `nextIndex[peer]` onwards.
2. Send via `MessageBus`.
3. On success: advance `matchIndex` and `nextIndex`; recalculate commit index.
4. On failure: decrement `nextIndex` using the follower's conflict hint.

### Follower-side (Receiver Implementation)

Implements Raft §5.3 receiver steps 1–5:
1. Reject if `term < currentTerm`.
2. Reject if `log[prev_log_index].term != prev_log_term`.
3. Truncate conflicting entries.
4. Append new entries.
5. Advance commit index to `min(leaderCommit, lastLogIndex)`.

### Optimised Conflict Hint

On rejection, the follower returns `conflict_index` and `conflict_term` so the
leader can jump directly to the first index of the conflicting term instead of
decrementing one-by-one (Raft paper optimisation from §5.3).

---

## Commit Index Calculation

The leader may only advance its commit index to index N when:
1. N has been replicated on a majority of servers (`matchIndex[peer] >= N` for
   a quorum of peers including the leader itself).
2. `log[N].term == currentTerm` (never commit entries from previous terms on
   behalf of the previous leader; Raft §5.4.2 safety requirement).

The `calculate_commit_index` static method sorts all match indexes (including
the leader's own last index) and returns the quorum-th highest value.

---

## Leadership Assumptions

- There is **at most one leader per term** (enforced by one-vote-per-term rule).
- The leader is the sole entry point for `submit_command`; followers redirect
  (currently raise `LeaderUnavailableError`; redirection is a future enhancement).
- Leadership is advisory and observable via `EventBus` events; higher-level
  subsystems (scheduler, placement) may choose to favour the leader for
  coordination decisions without Raft becoming a hard dependency.

---

## Phase 12 Protocol Extensions

Eight new `MessageType` constants (46–53) were added to `packet.py`:

| Constant                | Value | Purpose                               |
|-------------------------|-------|---------------------------------------|
| `RAFT_REQUEST_VOTE`     | 46    | Candidate → peers: RequestVote RPC    |
| `RAFT_VOTE_RESPONSE`    | 47    | Peers → candidate: vote grant/deny    |
| `RAFT_APPEND_ENTRIES`   | 48    | Leader → followers: log entries       |
| `RAFT_APPEND_RESPONSE`  | 49    | Followers → leader: ack/nack          |
| `RAFT_HEARTBEAT`        | 50    | Leader → followers: periodic keepalive |
| `RAFT_LEADER_ANNOUNCE`  | 51    | New leader → cluster: leadership notice |
| `RAFT_LOG_SYNC_REQUEST` | 52    | Lagging follower → leader: request entries |
| `RAFT_LOG_SYNC_RESPONSE`| 53    | Leader → follower: catch-up entries   |

---

## Scalability Considerations

- **Linear message complexity**: O(n) per heartbeat/election for n nodes.
- **Heartbeat suppression**: AppendEntries doubles as a heartbeat, reducing
  the number of distinct message types that must be dispatched.
- **Conflict hint optimisation**: O(log n) convergence per follower on conflict
  repair instead of O(n) one-at-a-time decrementing.
- **Thread safety**: `ConsensusLog` and `RaftStateMachine` use `threading.Lock`
  so they are safe for use across asyncio tasks that may execute on thread pools.

---

## Future Snapshot Integration (Phase 13)

`ConsensusLog.snapshot_state()` is the designated integration point for log
compaction and snapshotting. Phase 13 will:
1. Serialise the committed log prefix to stable storage.
2. Replace committed entries with a single snapshot entry.
3. Implement `InstallSnapshot` RPC for lagging followers.

Phase 12 does not persist any Raft state (current_term, voted_for, log entries).
This is intentional: Phase 13 will add durable storage, and the in-memory
implementation simplifies Phase 12 testing.

---

## Rejected Alternatives

### Paxos (Multi-Paxos / Classic Paxos)

Paxos provides equivalent safety guarantees but is significantly harder to
implement correctly and explain. The absence of a canonical "single leader"
role in classic Paxos makes engineering the log-ordering behaviour more complex.
Raft's explicit leader-centric design aligns better with Flock's existing
coordinator abstraction.

### View-Stamped Replication (VSR)

VSR is semantically equivalent to Raft but less well-known in the open-source
ecosystem, with fewer reference implementations and less community tooling.

### Etcd/external consensus service

Introducing an external consensus service (etcd, ZooKeeper) would contradict
Flock's core design principle of being completely brokerless. Flock must be
self-contained and deployable without any external infrastructure dependencies.

### CRDT-based eventual consistency

CRDTs provide conflict-free eventual consistency but do not provide the strong
ordering guarantees required for coordinator elections (only one leader at a
time). Strong consistency via Raft is non-negotiable for this use case.

---

## Consequences

**Positive**:
- Exactly one leader per term — no split-brain.
- Committed entries are never lost as long as a majority of nodes are healthy.
- Leadership is observable (EventBus events) without tight coupling.
- Modular design enables Phase 13 snapshotting without rewriting election or
  replication logic.

**Negative / Trade-offs**:
- Availability requires a quorum (majority) of nodes. A 3-node cluster
  tolerates 1 failure; 5-node tolerates 2.
- Write latency increases with cluster size (O(RTT) per replication round).
- `submit_command` is currently synchronous to the local log append; async
  commit notification is delivered via `consensus.log.committed` EventBus event.

---

## References

1. Ongaro, D. and Ousterhout, J. (2014). In Search of an Understandable
   Consensus Algorithm. USENIX ATC 2014.
   https://raft.github.io/raft.pdf
2. Ongaro, D. (2014). Consensus: Bridging Theory and Practice (PhD Thesis).
   https://web.stanford.edu/~ouster/cgi-bin/papers/OngaroPhD.pdf
3. TiKV Raft Implementation Reference:
   https://github.com/tikv/raft-rs
