"""Replication Coordinator resolving sync status."""

from __future__ import annotations

import threading
from typing import Dict, Set

from flock.datagrid.exceptions import ReplicationSyncError


class ReplicationCoordinator:
    """Manages tracking status replication updates across nodes."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # node_id -> set of synchronized keys
        self._synced_nodes: Dict[str, Set[str]] = {}

    def mark_synchronized(self, node_id: str, key: str) -> None:
        """Register key state synchronization match."""
        with self._lock:
            if node_id not in self._synced_nodes:
                self._synced_nodes[node_id] = set()
            self._synced_nodes[node_id].add(key)

    def is_synchronized(self, node_id: str, key: str) -> bool:
        """Check sync state database registry."""
        with self._lock:
            keys_set = self._synced_nodes.get(node_id)
            return key in keys_set if keys_set else False
