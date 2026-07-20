"""Topic Registry managing topics, partitions, and subscriptions metadata."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional, Set

from flock.streaming.exceptions import TopicNotFoundError
from flock.streaming.models import Partition, Topic


class TopicRegistry:
    """Thread-safe catalog directory keeping active topic partitions configurations."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # topic_id -> Topic
        self._topics: Dict[str, Topic] = {}
        # topic_id -> List[Partition]
        self._partitions: Dict[str, List[Partition]] = {}
        # topic_id -> Set[str] (subscriber client IDs)
        self._subscriptions: Dict[str, Set[str]] = {}

    def create_topic(self, topic: Topic) -> None:
        """Create a new topic registry entry with partitions."""
        with self._lock:
            self._topics[topic.topic_id] = topic
            self._subscriptions[topic.topic_id] = set()

            parts = []
            for i in range(topic.partitions_count):
                parts.append(Partition(partition_id=i, topic_id=topic.topic_id, leader_node=""))
            self._partitions[topic.topic_id] = parts

    def get_topic(self, topic_id: str) -> Optional[Topic]:
        """Fetch registered topic blueprint."""
        with self._lock:
            return self._topics.get(topic_id)

    def list_topics(self) -> List[Topic]:
        """List all registered topics."""
        with self._lock:
            return list(self._topics.values())

    def delete_topic(self, topic_id: str) -> None:
        """Remove a topic and partitions configurations."""
        with self._lock:
            self._topics.pop(topic_id, None)
            self._partitions.pop(topic_id, None)
            self._subscriptions.pop(topic_id, None)

    def get_partitions(self, topic_id: str) -> List[Partition]:
        """Fetch partition maps.

        Raises:
            TopicNotFoundError: If topic is missing.
        """
        with self._lock:
            if topic_id not in self._topics:
                raise TopicNotFoundError(f"Topic '{topic_id}' not found.")
            return self._partitions.get(topic_id, [])

    def subscribe_client(self, topic_id: str, client_id: str) -> None:
        """Register subscriber mappings."""
        with self._lock:
            if topic_id not in self._topics:
                raise TopicNotFoundError(f"Topic '{topic_id}' not found.")
            self._subscriptions[topic_id].add(client_id)

    def unsubscribe_client(self, topic_id: str, client_id: str) -> None:
        """Remove subscriber mappings."""
        with self._lock:
            if topic_id in self._subscriptions:
                self._subscriptions[topic_id].discard(client_id)

    def list_subscribers(self, topic_id: str) -> List[str]:
        """List clients subscribed to topic."""
        with self._lock:
            return list(self._subscriptions.get(topic_id, set()))
