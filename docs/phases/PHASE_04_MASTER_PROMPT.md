# Phase 4 Master Prompt

## Objective
Implement decentralized peer discovery for Flock, enabling nodes to dynamically discover each other.

## Scope
- Create discovery exceptions and data structures.
- Declare `NodeDescription` as immutable node details.
- Implement the PeerRegistry catalog to track discovered peer instances.
- Build the DiscoveryService managing request queries, responses, and periodically announcing state transitions.
