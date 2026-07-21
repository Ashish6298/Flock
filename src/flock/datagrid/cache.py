"""Distributed Cache Engine managing in-memory cached values."""

from __future__ import annotations

import time
import threading
from typing import Any, Dict, Optional

from flock.datagrid.models import CacheEntry


class DistributedCacheEngine:
    """Thread-safe local cache map supporting TTL expiration limits."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # key -> CacheEntry
        self._cache: Dict[str, CacheEntry] = {}

    def put(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """Add cached entry metadata."""
        expires_at = time.time() + ttl_seconds if ttl_seconds is not None else None
        entry = CacheEntry(key=key, value=value, expires_at=expires_at)
        
        with self._lock:
            self._cache[key] = entry

    def get(self, key: str) -> Optional[Any]:
        """Retrieve matching cached entry unless expired."""
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None

            if entry.expires_at is not None and time.time() > entry.expires_at:
                self._cache.pop(key, None)
                return None

            return entry.value

    def delete(self, key: str) -> None:
        """Remove entry from cache dictionary."""
        with self._lock:
            self._cache.pop(key, None)
