"""Stream Storage layer persisting partition event logs."""

from __future__ import annotations

import json
import threading
from typing import Dict, List, Optional

from flock.storage.backend import StorageBackend
from flock.streaming.exceptions import OffsetOutOfRangeError
from flock.streaming.models import EventMessage


class StreamStorage:
    """Writes partitioned event records sequentially to disk storage backends."""

    def __init__(self, storage_backend: StorageBackend) -> None:
        self._storage = storage_backend
        self._lock = threading.Lock()

    def append_message(self, message: EventMessage) -> None:
        """Atomically append a message payload record under partition key scopes."""
        with self._lock:
            # Filename: stream_{topic_id}_{partition_id}.jsonl
            path = f"stream_{message.topic_id}_{message.partition_id}.jsonl"
            
            # Read current file to assert offset sequence monotonicity
            lines: List[bytes] = []
            if self._storage.exists(path):
                raw = self._storage.read_file(path)
                lines = [line for line in raw.split(b"\n") if line.strip()]

            # Append new record
            data = message.model_dump()
            import base64
            data["payload"] = base64.b64encode(message.payload).decode("utf-8")
            
            data_bytes = json.dumps(data).encode("utf-8")
            lines.append(data_bytes)

            # Flush output stream
            payload = b"\n".join(lines) + b"\n"
            self._storage.write_atomically(path, payload)

    def read_messages(self, topic_id: str, partition_id: int, start_offset: int) -> List[EventMessage]:
        """Fetch messages sequential list starting from offset coordinate.

        Raises:
            OffsetOutOfRangeError: If start offset exceeds current records.
        """
        with self._lock:
            path = f"stream_{topic_id}_{partition_id}.jsonl"
            if not self._storage.exists(path):
                return []

            raw = self._storage.read_file(path)
            lines = [line for line in raw.split(b"\n") if line.strip()]

            messages: List[EventMessage] = []
            import base64
            for line in lines:
                data = json.loads(line.decode("utf-8"))
                data["payload"] = base64.b64decode(data["payload"].encode("utf-8"))
                msg = EventMessage(**data)
                if msg.offset >= start_offset:
                    messages.append(msg)

            return messages
