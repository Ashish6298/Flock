"""Unit tests for StreamStorage persistence."""

import os
import shutil
import tempfile
import time
from flock.storage.backend import FileStorageBackend
from flock.streaming.models import EventMessage
from flock.streaming.storage import StreamStorage


def test_storage_appends_and_reads_ordered() -> None:
    temp_dir = tempfile.mkdtemp()
    try:
        backend = FileStorageBackend(temp_dir)
        storage = StreamStorage(backend)

        m1 = EventMessage(
            message_id="m1",
            topic_id="t-4",
            partition_id=0,
            payload=b"abc",
            offset=0,
            timestamp=time.time(),
        )
        storage.append_message(m1)

        m2 = EventMessage(
            message_id="m2",
            topic_id="t-4",
            partition_id=0,
            payload=b"def",
            offset=1,
            timestamp=time.time(),
        )
        storage.append_message(m2)

        messages = storage.read_messages("t-4", 0, start_offset=0)
        assert len(messages) == 2
        assert messages[0].message_id == "m1"
        assert messages[1].message_id == "m2"
    finally:
        shutil.rmtree(temp_dir)
