# Flock

**Brokerless, decentralised, peer-to-peer distributed task execution framework for Python.**

Flock eliminates all centralised brokers (Redis, RabbitMQ, Kafka, Celery, etc.) by
implementing a complete distributed computing stack directly in Python: from TCP transport
and peer discovery through to Raft consensus, distributed scheduling, worker execution,
result collection, and automatic failure recovery.

---

## Features

- **Fully brokerless** – no external infrastructure dependencies.
- **Peer-to-peer networking** – asyncio TCP transport with binary packet framing.
- **Dynamic peer discovery** – announce/query/expire lifecycle over the MessageBus.
- **Cluster membership** – join/ack handshake with versioned snapshot synchronisation.
- **Heartbeat & failure detection** – periodic health monitoring with configurable timeouts.
- **Distributed task scheduler** – priority queues, constraint validation, EventBus notifications.
- **Intelligent task placement** – capability matching, resource-aware ranking, assignment handshakes.
- **Worker runtime** – pluggable Thread, Process, and Async execution backends.
- **Distributed result collection** – checksum-verified payloads, async Future completion.
- **Retry & recovery engine** – Fixed/Linear/Exponential-Jitter backoff, automatic reassignment.
- **Raft consensus** – leader election with randomised timeouts, AppendEntries log replication,
  quorum-gated commit index, and strict log completeness enforcement.
- **Transport-independent** – all subsystems communicate through the `MessageBus`; no subsystem
  depends directly on networking code.
- **mypy strict** – entire codebase verified at `--strict` level.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Application Layer                  │
├──────────────────┬──────────────────────────────────┤
│  ConsensusService│  Milestone E: Reliability         │
│  (Raft Leader    │  RecoveryEngine (Phase 11)        │
│  Election +      │  RetryPolicyEngine (Phase 11)     │
│  Log Replication)│                                   │
├──────────────────┴──────────────────────────────────┤
│              Milestone D: Distributed Execution      │
│  WorkerRuntimeService  │  ResultService              │
│  PlacementEngine        │  ResultRegistry            │
├─────────────────────────────────────────────────────┤
│              Milestone C: Distributed Scheduling     │
│  TaskSchedulerService   │  PlacementEngine           │
├─────────────────────────────────────────────────────┤
│              Milestone B: Cluster Formation          │
│  HeartbeatService       │  ClusterMembershipService  │
│  HealthRegistry          │  MembershipRegistry       │
├─────────────────────────────────────────────────────┤
│              Milestone A: Core Infrastructure        │
│  DiscoveryService       │  MessageBus / EventBus     │
│  TcpTransport           │  JsonSerializer / Packet   │
└─────────────────────────────────────────────────────┘
```

---

## Project Status

| Phase | Name | Status |
|-------|------|--------|
| 1  | Setup and Architecture Core | ✓ Complete |
| 2  | Protocol Serialization & Transport Layer | ✓ Complete |
| 3  | Communication & Messaging Core | ✓ Complete |
| 4  | Peer Discovery | ✓ Complete |
| 5  | Cluster Membership | ✓ Complete |
| 6  | Heartbeat & Failure Detection | ✓ Complete |
| 7  | Distributed Task Scheduler | ✓ Complete |
| 8  | Distributed Task Placement Engine | ✓ Complete |
| 9  | Worker Runtime & Execution Engine | ✓ Complete |
| 10 | Distributed Result Collection & Completion Pipeline | ✓ Complete |
| 11 | Distributed Retry & Recovery Engine | ✓ Complete |
| 12 | Distributed Raft Consensus Engine | ✓ Complete |
| 13 | Persistent Distributed Log & Snapshot Management | ⬜ Planned |

**Current Version**: 0.6.0  
**Total Tests**: 138 passing (0 failing, 0 skipped)  
**mypy**: strict / 0 issues  

---

## Package Structure

```
src/flock/
├── core/           # Common primitives, types, exceptions
├── protocol/       # Binary packet framing, MessageType constants (53 defined)
├── serialization/  # JSON / MessagePack adapters
├── transport/      # asyncio TCP transport
├── messaging/      # MessageBus, MessageRouter, middleware, EventBus
├── discovery/      # Peer discovery service and registry
├── cluster/        # Cluster membership service and registry
├── heartbeat/      # Heartbeat service and health registry
├── scheduler/      # Distributed task scheduler
├── placement/      # Task placement engine
├── runtime/        # Worker runtime and execution backends
├── results/        # Result collection and completion pipeline
├── recovery/       # Retry policy engine and recovery coordinator
└── consensus/      # Raft consensus (Phase 12)
    ├── exceptions.py   – 7 typed exception classes
    ├── models.py       – 13 immutable Pydantic models
    ├── log.py          – ConsensusLog (thread-safe, 1-based)
    ├── state_machine.py– RaftStateMachine (role FSM)
    ├── election.py     – ElectionEngine (vote solicitation)
    ├── replication.py  – ReplicationEngine (AppendEntries)
    └── service.py      – ConsensusService (orchestrator)
```

---

## Raft Consensus (Phase 12)

### Leader Election

Nodes start as followers with a randomised election timeout (150–300ms).
On timeout, a follower:
1. Increments its term and becomes a candidate.
2. Votes for itself.
3. Broadcasts `RAFT_REQUEST_VOTE` to all peers.
4. Becomes leader on receiving a majority of votes.

**Vote granting** follows Raft §5.2 + §5.4.1: a voter only grants its vote when
the candidate's term is current and its log is at least as up-to-date as the
voter's log (prevents losing committed entries on leadership change).

### Log Replication

The leader periodically sends `RAFT_APPEND_ENTRIES` to all followers.
Followers apply the 5-step Raft receiver algorithm, truncating conflicting
entries and appending new ones. The commit index advances only after a quorum
acknowledges replication.

### EventBus Events

| Event | Payload |
|---|---|
| `consensus.leader.elected` | `{leader_id, term}` |
| `consensus.term.changed` | `{old_term, new_term}` |
| `consensus.log.committed` | `{index, entry_id, term}` |
| `consensus.replication.failed` | `{peer_id, error}` |

### Usage

```python
from flock.consensus.service import ConsensusService

service = ConsensusService(
    node_id="node-1",
    message_bus=bus,
    event_bus=events,
    membership_registry=registry,
    min_election_timeout=0.15,
    max_election_timeout=0.30,
    heartbeat_interval=0.05,
)

await service.start()

# Submit a command (leader only)
if service.is_leader():
    entry = await service.submit_command(b"my-payload")
```

---

## Installation

```bash
pip install -e .
```

Requirements: Python ≥ 3.11, pydantic ≥ 2.0, structlog, msgpack.

---

## Running Tests

```bash
python -m pytest tests/ -v
```

---

## Documentation

- `docs/adr/` — Architecture Decision Records (0001–0012)
- `docs/audits/` — Phase audit reports and retrospectives
- `CHANGELOG.md` — Full version history
- `PROJECT_STATE.json` — Machine-readable project state

---

## Contributing

This is a research/educational project demonstrating how to build a complete
distributed task execution framework from first principles. Contributions,
suggestions, and questions are welcome.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
