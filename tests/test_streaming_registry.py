"""Unit tests for TopicRegistry."""

import pytest
from flock.streaming.exceptions import TopicNotFoundError
from flock.streaming.models import Topic
from flock.streaming.registry import TopicRegistry


def test_registry_create_and_delete() -> None:
    registry = TopicRegistry()
    topic = Topic(topic_id="t-1", name="telemetry", partitions_count=2)

    registry.create_topic(topic)
    assert registry.get_topic("t-1") == topic
    assert len(registry.list_topics()) == 1

    parts = registry.get_partitions("t-1")
    assert len(parts) == 2

    registry.subscribe_client("t-1", "client-a")
    assert registry.list_subscribers("t-1") == ["client-a"]

    registry.delete_topic("t-1")
    assert registry.get_topic("t-1") is None
