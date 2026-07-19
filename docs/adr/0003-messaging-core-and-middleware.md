# ADR 0003: Transport-Independent Messaging Core and Middleware

## Context & Problem Statement
To keep Flock's core cluster layers (such as Heartbeats, Gossip protocols, and Task execution routing) clean, we need a unified messaging pipeline. This pipeline must decouple physical transport networks (such as TCP socket handles) from payload deserialization, middleware layers (like rate limits, logging), and message dispatching.

## Selected Solution
We introduce:
1. **MessageContext**: Packages decoded payloads, metadata, and routing identifiers.
2. **MessageBus**: Implements RPC Request/Response tracking using correlation maps, and processes incoming pipelines.
3. **Middleware Chain**: Intercepts packets using a deterministic onion-style middleware callback chain before executing target handlers.
4. **Local EventBus**: Coordinates decoupled module operations (e.g. state change alerts) locally on the node using asynchronous pub/sub listeners.

## Consequences & Implications
- Ensures the framework can introduce TLS, transport protocols, or alternate serialized engines without rewriting higher distributed cluster orchestration modules.
