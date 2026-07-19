# ADR 0002: TCP-Based Network Transport and Binary framing

## Context & Problem Statement
In designing Flock, a decentralized peer-to-peer system, nodes must exchange execution payloads and system control messages (like heartbeats, status updates, and peer lists). We need to determine the primary transport implementation for early phases and outline how frames are structured to prevent packet fragmentation issues and allow forward-compatibility checks.

## Selected Solution
1. **TCP Transport Layer**: We build a TCP transport layer utilizing standard library `asyncio` streams. TCP handles guaranteed message ordering, delivery confirmation, and congestion control naturally.
2. **Standard Frame Protocol**: We design a binary protocol packet format consisting of:
   - **Header (8 bytes)**:
     - `MAGIC_BYTES` (`b"FLOK"`, 4 bytes) - validates protocol integrity.
     - `PROTOCOL_VERSION` (1 byte) - enables future schema version updates.
     - `MESSAGE_TYPE` (1 byte) - indicates payload category (heartbeats, cluster joins, task submits).
     - `PAYLOAD_SIZE` (4 bytes, unsigned integer) - denotes body length.
   - **Payload**: Raw byte representation of serialized message.

## Consequences
- Clean abstraction; serializing occurs before sending.
- Transport has no dependency on specific serialization engines.
