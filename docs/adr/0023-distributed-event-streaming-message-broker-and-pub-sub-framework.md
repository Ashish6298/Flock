# ADR 0023 – Distributed Event Streaming, Message Broker & Pub/Sub Framework

**Date**: 2026-07-20  
**Status**: Accepted  
**Phase**: 23 – Distributed Event Streaming, Message Broker & Pub/Sub Framework  
**Milestone**: J – Distributed Workflow Orchestration  

---

## Context

Flock requires a decentralized event streaming and message broker subsystem capable of publishing and subscribing to topics across partitioning boundaries without requiring explicit broker configurations.

---

## Decision

We implement a complete **Distributed Event Streaming, Message Broker & Pub/Sub Framework**:

1. **TopicRegistry**: Stores partition and metadata mapping directories.
2. **StreamStorage**: Sequentially persists base64 encoded event logs to storage backends.
3. **PublisherEngine**: Validates and key-hashes payloads to select destinations.
4. **SubscriberEngine**: Manages consumer offsets updates and triggers EventBus delivery alerts.
5. **BackpressureController**: Tracks rate ticks and enforces throttling limits.
6. **StreamingService**: Coordinates synchronizations and endpoints on the MessageBus.

---

## Consequences

- **Local Persistence**: Messages are saved to the local file storage system.
- **Backpressure Handling**: Throttles publish requests exceeding rate limits.
- **Ordered Partitions**: Consistently hashes keys to partition IDs to maintain sequential offsets.
