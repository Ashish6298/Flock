# Phase 4 Implementation Prompt

## Tasks
1. Extend package message types under `src/flock/protocol/packet.py` to support discovery requests.
2. Put exceptions under `src/flock/discovery/exceptions.py` and descriptions inside `src/flock/discovery/models.py`.
3. Create `PeerRegistry` catalog to record peers and prune expired references.
4. Implement `DiscoveryService` wrapping standard MessageBus RPC transactions.
5. Create tests asserting peer registries, discovery callbacks, and loopback setups.
