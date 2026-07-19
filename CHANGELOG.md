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
