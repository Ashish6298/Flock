"""Federated clusters policy synchronization manager."""

from __future__ import annotations

import time
import threading
from typing import Dict, List, Optional
from flock.policy.models import PolicyDefinition


class PolicySynchronizer:
    """Synchronizes Policy-as-Code documents across federated cluster nodes."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sync_history: Dict[str, float] = {}

    def sync_policies_to_node(self, target_node_id: str, policies: List[PolicyDefinition]) -> None:
        with self._lock:
            self._sync_history[target_node_id] = time.time()

    def get_last_sync_time(self, target_node_id: str) -> Optional[float]:
        with self._lock:
            return self._sync_history.get(target_node_id)
