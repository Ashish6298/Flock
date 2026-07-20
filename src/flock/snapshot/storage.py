"""Snapshot storage engine."""

from __future__ import annotations

import copy
import hashlib
import json
import threading
from typing import Any, Dict, List, Optional, Tuple

from flock.snapshot.exceptions import (
    SnapshotChecksumError,
    SnapshotRestoreError,
)
from flock.snapshot.models import SnapshotMetadata


class SnapshotStorage:
    """Manages snapshot descriptors, file listings, verification, and history."""

    def __init__(self, max_snapshots: int = 3) -> None:
        self.max_snapshots = max_snapshots
        self._lock = threading.Lock()
        
        # In-memory database index representing stored snapshots: snapshot_id -> (metadata, raw_bytes)
        self._snapshots: Dict[str, Tuple[SnapshotMetadata, bytes]] = {}
        self._history: List[str] = []

    def save_snapshot(self, metadata: SnapshotMetadata, data: bytes) -> None:
        """Save a new snapshot and metadata descriptor into storage.

        Args:
            metadata: SnapshotMetadata description block.
            data: Raw serialized snapshot payload.

        Raises:
            SnapshotChecksumError: If checksum verification fails.
        """
        # Validate checksum of saved snapshot bytes
        calculated = hashlib.sha256(data).hexdigest()
        if calculated != metadata.checksum:
            raise SnapshotChecksumError(
                f"Checksum mismatch: expected {metadata.checksum}, calculated {calculated}."
            )

        with self._lock:
            snap_id = metadata.snapshot_id
            self._snapshots[snap_id] = (metadata, data)
            
            if snap_id in self._history:
                self._history.remove(snap_id)
            self._history.append(snap_id)

            # Enforce history retention limits
            self._enforce_retention()

    def get_snapshot(self, snapshot_id: str) -> Optional[Tuple[SnapshotMetadata, bytes]]:
        """Retrieve snapshot metadata and payload for a given snapshot_id."""
        with self._lock:
            return self._snapshots.get(snapshot_id)

    def get_latest_snapshot(self) -> Optional[Tuple[SnapshotMetadata, bytes]]:
        """Retrieve the latest snapshot metadata and payload from storage."""
        with self._lock:
            if not self._history:
                return None
            latest_id = self._history[-1]
            return self._snapshots.get(latest_id)

    def list_snapshots(self) -> List[SnapshotMetadata]:
        """List metadata for all active snapshots in storage."""
        with self._lock:
            return [self._snapshots[snap_id][0] for snap_id in self._history]

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete an old snapshot from storage."""
        with self._lock:
            if snapshot_id in self._snapshots:
                del self._snapshots[snapshot_id]
                if snapshot_id in self._history:
                    self._history.remove(snapshot_id)
                return True
            return False

    def clear(self) -> None:
        """Clear all stored snapshots."""
        with self._lock:
            self._snapshots.clear()
            self._history.clear()

    def _enforce_retention(self) -> None:
        """Purge oldest snapshots beyond configured retention limits."""
        while len(self._history) > self.max_snapshots:
            oldest_id = self._history.pop(0)
            if oldest_id in self._snapshots:
                del self._snapshots[oldest_id]
