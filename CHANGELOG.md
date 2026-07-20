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

## [0.7.0] - 2026-07-20

### Added
- Replicated Distributed State Machine & Metadata Store package (`src/flock/statemachine/`).
- Immutable `StateCommand`, `StateOperation`, `StateEntry`, `StateSnapshotMetadata`, and `ReplicatedValue` models.
- `ReplicatedStateStore` supporting PUT, UPDATE, DELETE, UPSERT, INCREMENT, APPEND, SET_ADD, SET_REMOVE, MAP_PUT, MAP_DELETE.
- `StateMachineEngine` enforcing sequential commit processing, duplicate command checks, and SHA256 checksummed snapshot generation.
- `StateMachineService` combining the store, engine, consensus commit callbacks, and asynchronous Future awaits.
- Protocol message definitions 54-61 mapping commands, updates, and sync actions.
- ADR 0013 detailing the state machine design, idempotency model, and checksum safety guarantees.
- 14 automated tests; 152/152 total tests passing; mypy strict type checker clean.

## [0.8.0] - 2026-07-20

### Added
- Distributed Snapshot Replication & Log Compaction package (`src/flock/snapshot/`).
- Immutable `SnapshotMetadata`, `SnapshotManifest`, `SnapshotChunk`, `SnapshotTransferSession`, `SnapshotInstallRequest`, `SnapshotInstallResponse`, `SnapshotRestoreResult`, and `CompactionStatistics` models.
- `SnapshotStorage` managing snapshot listings, SHA-256 integrity verifications, and configurable retention limits.
- `LogCompactor` safely truncating committed log prefixes.
- `SnapshotReplicator` performing segmenting, streaming, chunk verification, and reassembly.
- `SnapshotService` orchestrating auto-triggers, compaction pipelines, and InstallSnapshot message handshakes.
- Message type constants 62-71 mapping requests, chunks, and compaction notifications.
- ADR 0014 documenting log compaction strategy, chunked transfers, and InstallSnapshot invariants.
- 9 automated tests; 161/161 total tests passing; mypy strict clean.

## [0.9.0] - 2026-07-20

### Added
- Persistent Storage Engine & Write-Ahead Logging (WAL) package (`src/flock/storage/`).
- Immutable `WALEntry`, `WALSegment`, `StorageMetadata`, `RecoveryCheckpoint`, `PersistentState`, `StorageStatistics`, `WALReplayResult`, `StorageConfiguration`, and `StorageHealthReport` models.
- Pluggable `StorageBackend` abstraction and `FileStorageBackend` filesystem driver with atomic write-rename swaps.
- `WriteAheadLog` managing sequential entry appends, checksum validation, and segment rotations.
- `PersistentStorageEngine` coordinating metadata checkpoints and snapshot compaction logs.
- `RecoveryEngine` executing node state restoration via FSM snapshot loading and sequential WAL entry replays.
- Message type constants 72-81 mapping sync actions, checkpoints, and health report queries.
- ADR 0015 documenting Write-Ahead Logging formats, fsync guarantees, and recovery workflows.
- 9 automated tests; 169/169 total tests passing; mypy strict clean.

## [1.0.0] - 2026-07-20

### Added
- Distributed Observability, Metrics & Telemetry Framework package (`src/flock/observability/`).
- Immutable `MetricValue`, `Span`, `NodeHealthReport`, and `ClusterHealthReport` models.
- `MetricsRegistry` supporting counters, gauges, summaries, and histogram percentile bounds.
- `TelemetryExporter` outputting JSON streams and Prometheus exposition formats.
- `TracingEngine` generating traces, child spans, and timeline annotations.
- `HealthMonitor` evaluating liveness degradation parameters.
- `ObservabilityService` binding network endpoints.
- Message type constants 82-91 mapping metric requests, trace syncs, and diagnostics queries.
- ADR 0016 documenting EventBus-driven instrumentation and telemetry designs.
- 9 automated tests; 178/178 total tests passing; mypy strict clean.

## [1.1.0] - 2026-07-20

### Added
- Distributed Security, Authentication & Authorization Framework package (`src/flock/security/`).
- Immutable `NodeIdentity`, `SessionToken`, `AccessDecision`, and `SecurityAuditRecord` models.
- `CryptographyEngine` providing SHA-256 digests and HMAC-SHA256 signing and verifications.
- `IdentityManager` validating trusted certificates and peers.
- `AuthorizationEngine` implementing RBAC checks for coordinator, worker, and observer roles.
- `TokenManager` issuing and validating signed SessionTokens.
- `SecureHandshakeManager` performing challenge-response handshakes for joining nodes.
- `SecurityAuditLogger` recording immutable event logs to the EventBus.
- Message type constants 92-101 mapping authentication, token validation, and secure session handshakes.
- ADR 0017 documenting cryptographic signatures and RBAC policies.
- 10 automated tests; 188/188 total tests passing; mypy strict clean.

## [1.2.0] - 2026-07-20

### Added
- Distributed Resource Manager & Intelligent Cluster Load Balancer package (`src/flock/resources/`).
- Immutable `NodeResourceProfile`, `ResourceReservation`, `AllocationResult`, `WorkloadClassification`, `BalancingDecision`, and `CapacityForecast` models.
- `ResourceRegistry` tracking node capacities, utilization levels, and accelerator metrics.
- `ResourceAllocator` handling reservations, leases, and rollback allocations.
- `LoadBalancingEngine` executing Best-Fit, Least Loaded, and Round Robin strategies.
- `CapacityPlanner` forecasting cluster exhaustion timeframes and alerts.
- `AdmissionController` enforcing quota policy checks and node capability bounds.
- `ResourceBalancer` computing skew variance recommendations.
- Message type constants 102-111 mapping resource updates, allocation requests, and utilization broadcasts.
- ADR 0018 documenting load balancing strategies, quota limits, and capacity models.
- 8 automated tests; 196/196 total tests passing; mypy strict clean.

## [1.3.0] - 2026-07-20

### Added
- Autonomous Cluster Orchestrator & Self-Healing Scheduler package (`src/flock/orchestrator/`).
- Immutable `ClusterPolicy`, `OptimizationPlan`, `ScalingDecision`, `MigrationPlan`, `SchedulingRecommendation`, and `ClusterSnapshot` models.
- `PolicyEngine` tracking global placement configurations and threshold alerts.
- `AutonomousScheduler` directing task migration transactions and event logs.
- `OptimizationEngine` calculating target cluster rebalancing plans.
- `AutoScaler` computing scale-out and scale-in size changes.
- `OrchestratorService` exposing policy synchronization handlers.
- Message type constants 112-121 mapping policies, migrations, and rebalance notifications.
- ADR 0019 documenting orchestrator policies and autoscaler limits.
- 9 automated tests; 202/202 total tests passing; mypy strict clean.

## [1.4.0] - 2026-07-20

### Added
- Multi-Cluster Federation & Global Scheduler package (`src/flock/federation/`).
- Immutable `FederationCluster`, `FederationNode`, `GlobalTask`, `RoutingDecision`, `ReplicationPolicy`, `FederationHealth`, `FederationSnapshot`, and `ClusterAdvertisement` models.
- `FederationRegistry` managing member clusters and endpoints directories.
- `GlobalRoutingEngine` implementing capacity-aware destination selection heuristics.
- `GlobalScheduler` mapping task scheduling assignments across federation links.
- `CrossClusterReplicationEngine` replicating snapshots and node metrics out-of-band.
- `FederationService` exposing join handshake query routes.
- Message type constants 122-131 mapping federation join, state sync, and status report queries.
- ADR 0020 documenting multi-cluster routing models and replication sync.
- 10 automated tests; 212/212 total tests passing; mypy strict clean.
