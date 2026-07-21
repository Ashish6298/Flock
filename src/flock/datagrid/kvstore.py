"""KeyValue Engine managing versioned CAS actions."""

from __future__ import annotations

import threading
from typing import Any, Dict, Optional

from flock.datagrid.exceptions import RecordNotFoundError
from flock.datagrid.models import KeyValueRecord


class KeyValueEngine:
    """Manages versioned transactional mutation changes."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # key -> KeyValueRecord
        self._store: Dict[str, KeyValueRecord] = {}

    def put(self, key: str, value: Any) -> KeyValueRecord:
        """Upsert value record incrementing revision index."""
        with self._lock:
            current = self._store.get(key)
            new_ver = (current.version + 1) if current else 1
            rec = KeyValueRecord(key=key, value=value, version=new_ver)
            self._store[key] = rec
            return rec

    def get(self, key: str) -> KeyValueRecord:
        """Fetch versioned key record.

        Raises:
            RecordNotFoundError: If key is missing.
        """
        with self._lock:
            rec = self._store.get(key)
            if not rec:
                raise RecordNotFoundError(f"Key '{key}' not found in KeyValueEngine store.")
            return rec

    def compare_and_swap(self, key: str, expected_version: int, new_value: Any) -> bool:
        """Modify value conditionally if version matches."""
        with self._lock:
            current = self._store.get(key)
            if not current:
                return False

            if current.version != expected_version:
                return False

            rec = KeyValueRecord(key=key, value=new_value, version=current.version + 1)
            self._store[key] = rec
            return True

    def delete(self, key: str) -> None:
        """Remove key from persistent dictionary."""
        with self._lock:
            if key not in self._store:
                raise RecordNotFoundError(f"Key '{key}' not found in KeyValueEngine store.")
            self._store.pop(key, None)
