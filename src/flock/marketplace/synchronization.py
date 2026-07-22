"""Federated registry sync workflows and offline registry mirrors updates."""

from __future__ import annotations

import time
import threading
from typing import Dict, List, Optional
from flock.marketplace.models import PackageManifest


class RegistrySynchronizer:
    """Synchronizes manifests registries between federated clusters and offline mirrors."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sync_history: Dict[str, float] = {}

    def sync_registry_mirror(self, target_mirror_id: str, manifests: List[PackageManifest]) -> None:
        """Simulate syncing list of package manifests to a target mirror/federated cluster."""
        with self._lock:
            self._sync_history[target_mirror_id] = time.time()

    def get_last_sync_time(self, mirror_id: str) -> Optional[float]:
        """Get last synchronized time for a mirror."""
        with self._lock:
            return self._sync_history.get(mirror_id)
