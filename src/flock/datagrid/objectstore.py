"""Object Storage Engine managing binary data files."""

from __future__ import annotations

import hashlib
import threading
from typing import Dict

from flock.datagrid.exceptions import BucketQuotaExceededError
from flock.datagrid.models import ObjectRecord


class ObjectStorageEngine:
    """Tracks size limits and writes files to storage dictionaries."""

    def __init__(self, size_limit: int = 1048576) -> None:
        self.size_limit = size_limit
        self._lock = threading.Lock()
        
        # object_key -> ObjectRecord
        self._objects: Dict[str, ObjectRecord] = {}

    def upload_object(self, key: str, payload: bytes) -> ObjectRecord:
        """Add object records verifying size limits boundaries.

        Raises:
            BucketQuotaExceededError: If payload bytes exceed size_limit.
        """
        if len(payload) > self.size_limit:
            raise BucketQuotaExceededError(
                f"Payload size '{len(payload)}' exceeds limit '{self.size_limit}'."
            )

        hasher = hashlib.sha256(payload)
        checksum = hasher.hexdigest()

        rec = ObjectRecord(object_key=key, payload=payload, checksum=checksum)
        with self._lock:
            self._objects[key] = rec
            return rec

    def download_object(self, key: str) -> bytes:
        """Fetch payload from storage dictionary."""
        with self._lock:
            rec = self._objects.get(key)
            if not rec:
                raise KeyError(f"Object '{key}' not found in storage.")
            return rec.payload
