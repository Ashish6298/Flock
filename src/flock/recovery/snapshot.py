"""Consistent cluster snapshot builder and catalog module."""

from __future__ import annotations

import time
import uuid
import hashlib
import json
import threading
from typing import Dict, List, Optional, Any
from flock.recovery.exceptions import SnapshotError
from flock.recovery.models import ClusterSnapshot


class SnapshotManager:
    """Creates, validates, and manages cluster-wide snapshots."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._snapshots: Dict[str, ClusterSnapshot] = {}

    def create_snapshot(self, state_data: Dict[str, Any], metadata: Optional[Dict[str, str]] = None) -> ClusterSnapshot:
        """Create a consistent snapshot of the current state data."""
        with self._lock:
            snap_id = str(uuid.uuid4())
            now = time.time()
            
            # Deterministic state hash
            serialized = json.dumps(state_data, sort_keys=True)
            state_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
            
            snapshot = ClusterSnapshot(
                snapshot_id=snap_id,
                timestamp=now,
                state_hash=state_hash,
                metadata=metadata or {},
                data=state_data,
            )
            self._snapshots[snap_id] = snapshot
            return snapshot

    def delete_snapshot(self, snapshot_id: str) -> None:
        """Remove a snapshot from the catalog."""
        with self._lock:
            if snapshot_id not in self._snapshots:
                raise SnapshotError(f"Snapshot '{snapshot_id}' does not exist.")
            del self._snapshots[snapshot_id]

    def get_snapshot(self, snapshot_id: str) -> ClusterSnapshot:
        """Retrieve snapshot details."""
        with self._lock:
            if snapshot_id not in self._snapshots:
                raise SnapshotError(f"Snapshot '{snapshot_id}' does not exist.")
            return self._snapshots[snapshot_id]

    def list_snapshots(self) -> List[ClusterSnapshot]:
        """List all available snapshots."""
        with self._lock:
            return list(self._snapshots.values())
