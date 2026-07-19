# Next Milestone Plan: Milestone B — Cluster Formation

## Objectives
Milestone B will build upon the core infrastructure created in Milestone A by establishing dynamic node clusters. Nodes will automatically discover each other and maintain a shared list of active members.

## Phased Rollout Plan
- **Phase 4: Peer Discovery & Membership**: Implement dynamic multicast discovery, gossip protocols for membership propagation, and cluster membership state transitions (Join, Leave, Dead).
- **Phase 5: Heartbeat & Failure Detection**: Implement a dedicated node heartbeat monitor to detect crashed or offline workers and trigger failover notifications.

## Architecture Guidelines
- Ensure member lists are thread-safe and asynchronous.
- Failures must trigger Event Bus notifications locally so other subsystems can act accordingly.
