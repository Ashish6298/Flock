"""Data Lifecycle Manager enforcing TTL checks."""

from __future__ import annotations

import time
import threading
from typing import Dict, Set


class DataLifecycleManager:
    """Manages tracking timestamps metrics to evict records."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # key -> expiration timestamp
        self._expirations: Dict[str, float] = {}

    def set_expiration(self, key: str, ttl_seconds: float) -> None:
        """Register TTL boundaries."""
        with self._lock:
            self._expirations[key] = time.time() + ttl_seconds

    def evaluate_expired_keys(self) -> Set[str]:
        """Collect and return expired keys."""
        now = time.time()
        expired: Set[str] = set()
        with self._lock:
            for key, expires_at in list(self._expirations.items()):
                if now > expires_at:
                    expired.add(key)
                    self._expirations.pop(key, None)
        return expired
