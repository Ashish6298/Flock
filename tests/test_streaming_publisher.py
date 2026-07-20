"""Unit tests for PublisherEngine."""

import os
import shutil
import tempfile
import pytest
from flock.events.bus import EventBus
from flock.storage.backend import FileStorageBackend
from flock.streaming.models import PublishRequest, Topic
from flock.streaming.publisher import PublisherEngine
from flock.streaming.registry import TopicRegistry
from flock.streaming.storage import StreamStorage


@pytest.mark.asyncio
async def test_publisher_partitions_hashing() -> None:
    temp_dir = tempfile.mkdtemp()
    try:
        events = EventBus()
        backend = FileStorageBackend(temp_dir)
        storage = StreamStorage(backend)
        registry = TopicRegistry()

        topic = Topic(topic_id="t-2", name="logs", partitions_count=4)
        registry.create_topic(topic)

        publisher = PublisherEngine(registry, storage, events)

        # Publish request with key hashes consistently to a partition
        req = PublishRequest(topic_id="t-2", payload=b"hello", key="partition-key-a")
        receipt = await publisher.publish(req)

        assert receipt.success is True
        assert receipt.offset == 0
        assert receipt.partition_id in [0, 1, 2, 3]
    finally:
        shutil.rmtree(temp_dir)
