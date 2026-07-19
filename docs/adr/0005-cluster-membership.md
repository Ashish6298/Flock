# ADR 0005: Cluster Membership Synchronization

## Context & Problem Statement
With peer discovery completed in Phase 4, nodes can find other instances. However, discovery alone does not represent a synchronized cluster state. Nodes need a deterministic mechanism to request to join a cluster, synchronize authoritative lists of active members, detect stale data via monotonic version counts, and notify local services.

## Selected Solution
We implement:
1. **ClusterMember**: An immutable representation of a node's membership profile including role descriptions, status enums, and monotonic versions.
2. **MembershipRegistry**: An asyncio-safe membership catalog validating state transitions (Joining -> Active -> Leaving -> Removed). Version counters increment on updates.
3. **ClusterMembershipService**: Registers callbacks on DiscoveryService. When discovery detects a peer, a join handshake is initiated. The service handles join requests, registers dynamic status updates, serializes snapshot arrays, and triggers local `EventBus` signals.

## Consequences & Trade-offs
- The membership layer runs independently of future heartbeat failure checkers.
- Simple monotonic version comparison is sufficient for dynamic joins, but complex nets will require consensus algorithms (e.g. Raft) in future production milestones.
