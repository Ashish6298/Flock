# ADR 0004: Transport-Independent Peer Discovery

## Context & Problem Statement
In building Milestone B (Cluster Formation) for Flock, nodes need to locate other instances. Hardcoding static target parameters undermines the dynamic benefits of decentralized clusters. We must introduce a discovery layer that remains decoupled from underlying TCP or alternate transports, enabling dynamic registration loops.

## Selected Solution
We design:
1. **NodeDescription**: An immutable representation of public node metrics (Framework versions, capabilities, tags, port definitions).
2. **PeerRegistry**: A catalog managing dynamic peer mappings. It registers nodes, suppresses duplicates, cleans stale definitions via configurable TTL values, and remains independent from cluster membership state machines.
3. **DiscoveryService**: Translates lifecycle triggers (startup queries, announces, leaves) into `MessageBus` send calls using standard `DISCOVERY_REQUEST`, `DISCOVERY_RESPONSE`, `NODE_ANNOUNCE`, and `NODE_LEAVE` messaging types.

## Consequences & Trade-offs
- Keeps discovery completely separated from membership and leader voting components.
- Enables dropping in static lists, multicast, or Kubernetes API lookup strategies later by changing the strategy backend without touching core transport code.
