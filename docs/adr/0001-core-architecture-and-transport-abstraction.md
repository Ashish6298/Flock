# ADR 0001: Core Architecture, Transport, and Serialization Abstraction

## Context & Problem Statement
Flock requires a brokerless, decentralized architecture. Nodes must communicate, discover each other, serialize/deserialize packets, and execute tasks without centralized components. To maintain scalability and allow swapping physical networking protocols (e.g., raw TCP, UDP, QUIC, TLS) or serialization formats (e.g., JSON, Msgpack, Protobuf), we must define clear, decoupled interfaces.

## Selected Solution
We introduce abstract Interfaces/Protocols for:
1. `Serializer`: Governs object/message encoding and decoding.
2. `Transport`: Handles raw message sending/receiving and connection lifecycles asynchronously.
3. `Discovery`: Handles peer auto-discovery mechanisms.

These layers communicate via structured, versioned envelopes (Packets) to guarantee backwards/forwards compatibility.

## Consequences & Trade-offs
- Loose coupling enables easy plug-in replacement.
- Slight abstraction overhead, which is negligible compared to standard network latencies.
