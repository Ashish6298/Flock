"""Subscriber Engine routing offsets and acknowledging deliveries."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from flock.events.bus import EventBus
from flock.streaming.exceptions import OffsetOutOfRangeError
from flock.streaming.models import ConsumerOffset, EventMessage
from flock.streaming.storage import StreamStorage


class SubscriberEngine:
    """Manages active offsets subscriptions and pull intervals."""

    def __init__(self, storage: StreamStorage, event_bus: EventBus) -> None:
        self._storage = storage
        self._events = event_bus
        self._lock = threading.Lock()
        
        # key: (group_id, topic_id, partition_id) -> offset
        self._offsets: Dict[tuple[str, str, int], int] = {}

    def commit_offset(self, commit: ConsumerOffset) -> None:
        """Update committed offset coordinates in catalog registry."""
        with self._lock:
            key = (commit.group_id, commit.topic_id, commit.partition_id)
            self._offsets[key] = commit.offset

    def get_offset(self, group_id: str, topic_id: str, partition_id: int) -> int:
        """Fetch committed offset index."""
        with self._lock:
            key = (group_id, topic_id, partition_id)
            return self._offsets.get(key, 0)

    async def fetch_next(self, group_id: str, topic_id: str, partition_id: int) -> Optional[EventMessage]:
        """Fetch next pending message for consumer."""
        current_offset = self.get_offset(group_id, topic_id, partition_id)
        
        messages = self._storage.read_messages(topic_id, partition_id, current_offset)
        if not messages:
            return None

        msg = messages[0]
        
        # Commit next offset sequentially
        self.commit_offset(
            ConsumerOffset(
                group_id=group_id,
                topic_id=topic_id,
                partition_id=partition_id,
                offset=msg.offset + 1,
            )
        )

        await self._events.publish(
            "message.acknowledged",
            {
                "message_id": msg.message_id,
                "group_id": group_id,
            },
        )

        return msg
