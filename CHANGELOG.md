# Flock Changelog

All notable changes to the Flock project will be documented here.

## [0.1.0] - 2026-07-11

### Added
- Centralized project layout, including exception hierarchy, typing primitives, and Pydantic configuration support.
- Custom binary message protocol with frame verification (`FLOK` header).
- Asyncio TCP Transport implementation for decentralized message delivery.
- JSON and MessagePack serialization engines.
- Test suites covering custom framing, serialization engine fallbacks, and TCP loopbacks.
- Transport-independent `MessageBus` for payload coordination.
- Registry-based `MessageRouter` mapping types to handlers.
- Pre and post middleware processing pipelines.
- RPC Request-Response manager with correlation context tracking.
- Node-local Event Bus for decoupled local event notifications.
- Peer Discovery service with dynamic registration loops, announcement broadcasts, and leave notifications.
- Expiration-based PeerRegistry inventory.

## [0.1.1] - 2026-07-19

### Added
- Cluster membership core package (`src/flock/cluster/`).
- Immutable `ClusterMember` mapping record and `ClusterMemberStatus` enum lifecycle states.
- Authoritative `MembershipRegistry` container validating state transitions.
- `ClusterMembershipService` coordinating join handshakes (`MEMBER_JOIN_REQ`, `MEMBER_JOIN_ACK`) and EventBus notification dispatches.
- Snapshot synchronization and deserialization merge pipelines.

## [0.1.2] - 2026-07-19

### Added
- Heartbeat and Failure Detection package (`src/flock/heartbeat/`).
- Immutable `HealthRecord` tracking RTT metrics and `HealthState` enum reachability states.
- Authoritative `HealthRegistry` validating state transitions.
- `FailureDetector` evaluating missed heartbeat ping windows and publishing EventBus status notifications.
- `HeartbeatService` coordinating background ping-pong schedules over MessageBus transports.

## [0.2.0] - 2026-07-19

### Added
- Distributed Task Scheduler package (`src/flock/scheduler/`).
- Immutable `Task` and `TaskMetadata` configurations.
- `SchedulingQueue` sorting tasks via FIFO and Priority policies.
- `TaskSchedulerService` coordinating submissions, validator deadlines, queue insertions, and EventBus status notifications.
- Distributed Task Placement Engine package (`src/flock/placement/`).
- Immutable `NodeCapability`, `PlacementDecision`, and `AssignmentRecord` metadata mappings.
- `PlacementRegistry` tracking task assignment nodes.
- `PlacementEngine` executing constraint tag filters and task assignment handshakes (`TASK_ASSIGN`, `TASK_ASSIGN_ACK`).

## [0.3.0] - 2026-07-19

### Added
- Worker Runtime & Execution Engine package (`src/flock/runtime/`).
- Immutable `WorkerInfo` metadata records and `ExecutionState` lifecycle progress states.
- Pluggable local execution backend pools (`ThreadPoolExecutorBackend`, `ProcessPoolExecutorBackend`, `AsyncExecutorBackend`).
- `ExecutionContext` containers implementing cooperative cancellation token callbacks.
- `WorkerRuntimeService` orchestrating execution queues, local worker registers, andEventBus progress updates.

## [0.4.0] - 2026-07-19

### Added
- Distributed Result Collection package (`src/flock/results/`).
- Immutable `ExecutionResult`, `FailureResult`, and `ResultMetadata` envelopes.
- `ResultSerializer` supporting JSON/Msgpack payload transformations and integrity checksum verify hashes.
- Asynchronous `ResultRegistry` container processing waiters and TTL cleanup sweeps.
- `ResultCollector` routing incoming TASK_RESULT network packets.
- Orchestration `ResultService` implementing asynchronous client result waiting hooks.

## [0.5.0] - 2026-07-19

### Added
- Distributed Retry & Recovery Engine package (`src/flock/recovery/`).
- Immutable `RetryPolicy`, `RetryContext`, `RetryDecision`, and `RecoveryPlan` logs.
- `RetryPolicyEngine` supporting Fixed, Linear, and Exponential Jitter backoff algorithms.
- `RecoveryRegistry` managing active recovery tasks and worker cooldown exclusions.
- `RecoveryEngine` coordinating with PlacementEngine to schedule task reassignments.
- `RecoveryService` managing node recovery handshake packets.

## [0.6.0] - 2026-07-20

### Added
- Distributed Raft Consensus Engine package (`src/flock/consensus/`).
- `ConsensusLog` – thread-safe, 1-based indexed replicated log with commit semantics, truncation for conflict repair, and Phase 13 snapshot hooks.
- `RaftStateMachine` – deterministic FOLLOWER/CANDIDATE/LEADER role FSM with one-vote-per-term enforcement, log completeness checks (Raft §5.4.1), and commit index advancement.
- `ElectionEngine` – randomised election timers (150–300ms, configurable), vote solicitation via MessageBus, quorum detection, and leader promotion.
- `ReplicationEngine` – AppendEntries 5-step receiver logic, optimised conflict hints, per-peer nextIndex/matchIndex tracking, and quorum-gated commit index advancement.
- `ConsensusService` – top-level orchestrator wiring all components; registers 8 Raft message handlers; publishes `consensus.leader.elected`, `consensus.term.changed`, `consensus.log.committed`, and `consensus.replication.failed` events.
- 8 new `MessageType` constants (46–53): `RAFT_REQUEST_VOTE`, `RAFT_VOTE_RESPONSE`, `RAFT_APPEND_ENTRIES`, `RAFT_APPEND_RESPONSE`, `RAFT_HEARTBEAT`, `RAFT_LEADER_ANNOUNCE`, `RAFT_LOG_SYNC_REQUEST`, `RAFT_LOG_SYNC_RESPONSE`.
- 7 typed exception classes: `InvalidTermError`, `LogConflictError`, `ElectionTimeoutError`, `LeaderUnavailableError`, `ConsensusViolationError`, `ReplicationFailureError`, `QuorumNotReachedError`.
- 13 immutable Pydantic models: `RaftRole`, `RaftNodeState`, `LogEntry`, `TermInfo`, `VoteRequest`, `VoteResponse`, `AppendEntriesRequest`, `AppendEntriesResponse`, `ElectionResult`, `HeartbeatPayload`, `LeaderAnnouncePayload`, `LogSyncRequest`, `LogSyncResponse`.
- ADR 0012 documenting Raft algorithm selection, election algorithm, replication strategy, rejected alternatives, and Phase 13 integration hooks.
- 98 automated tests across 5 new test files; 138/138 total tests passing; mypy strict: 0 issues.
