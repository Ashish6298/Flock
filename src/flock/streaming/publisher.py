"""Publisher Engine validating and partition-key hashing publish requests."""

from __future__ import annotations

import hashlib
import time
import uuid

from flock.events.bus import EventBus
from flock.streaming.exceptions import TopicNotFoundError
from flock.streaming.models import DeliveryReceipt, EventMessage, PublishRequest
from flock.streaming.registry import TopicRegistry
from flock.streaming.storage import StreamStorage


class PublisherEngine:
    """Computes target partition keys and appends messages to storage."""

    def __init__(self, registry: TopicRegistry, storage: StreamStorage, event_bus: EventBus) -> None:
        self._registry = registry
        self._storage = storage
        self._events = event_bus

    async def publish(self, request: PublishRequest) -> DeliveryReceipt:
        """Route payload to target partition, append to storage, and alert EventBus.

        Raises:
            TopicNotFoundError: If target topic registry is missing.
        """
        topic = self._registry.get_topic(request.topic_id)
        if not topic:
            raise TopicNotFoundError(f"Topic '{request.topic_id}' not found.")

        # Hash routing key to select partition id
        partition_id = 0
        if request.key:
            hashval = int(hashlib.md5(request.key.encode("utf-8")).hexdigest(), 16)
            partition_id = hashval % topic.partitions_count

        # Read current messages to calculate offset index
        current = self._storage.read_messages(request.topic_id, partition_id, 0)
        next_offset = len(current)

        msg = EventMessage(
            message_id=str(uuid.uuid4()),
            topic_id=request.topic_id,
            partition_id=partition_id,
            payload=request.payload,
            offset=next_offset,
            timestamp=time.time(),
        )

        self._storage.append_message(msg)

        # Notify EventBus
        await self._events.publish(
            "message.published",
            {
                "message_id": msg.message_id,
                "topic_id": msg.topic_id,
                "partition_id": msg.partition_id,
            },
        )

        return DeliveryReceipt(
            message_id=msg.message_id,
            offset=msg.offset,
            partition_id=msg.partition_id,
            success=True,
        )
