"""Unit tests for SubscriberEngine."""

import os
import shutil
import tempfile
import time
import pytest
from flock.events.bus import EventBus
from flock.storage.backend import FileStorageBackend
from flock.streaming.models import EventMessage
from flock.streaming.storage import StreamStorage
from flock.streaming.subscriber import SubscriberEngine


@pytest.mark.asyncio
async def test_subscriber_commit_and_fetch() -> None:
    temp_dir = tempfile.mkdtemp()
    try:
        events = EventBus()
        backend = FileStorageBackend(temp_dir)
        storage = StreamStorage(backend)
        subscriber = SubscriberEngine(storage, events)

        # Write test message
        msg = EventMessage(
            message_id="msg-1",
            topic_id="t-3",
            partition_id=0,
            payload=b"abc",
            offset=0,
            timestamp=time.time(),
        )
        storage.append_message(msg)

        # Fetch and verify commit sequence increments
        fetched = await subscriber.fetch_next("group-x", "t-3", 0)
        assert fetched is not None
        assert fetched.message_id == "msg-1"
        assert subscriber.get_offset("group-x", "t-3", 0) == 1
    finally:
        shutil.rmtree(temp_dir)
