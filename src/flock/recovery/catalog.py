"""Unified catalog registry tracking recovery artifacts and backup histories."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional
from flock.recovery.models import BackupArchive, ClusterSnapshot, CheckpointDescriptor


class RecoveryCatalog:
    """Consolidated catalog registry indexing all snapshots, backups, and checkpoints."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._backups: Dict[str, BackupArchive] = {}
        self._snapshots: Dict[str, ClusterSnapshot] = {}
        self._checkpoints: Dict[str, CheckpointDescriptor] = {}

    def register_backup(self, backup: BackupArchive) -> None:
        with self._lock:
            self._backups[backup.backup_id] = backup

    def register_snapshot(self, snapshot: ClusterSnapshot) -> None:
        with self._lock:
            self._snapshots[snapshot.snapshot_id] = snapshot

    def register_checkpoint(self, checkpoint: CheckpointDescriptor) -> None:
        with self._lock:
            self._checkpoints[checkpoint.checkpoint_id] = checkpoint

    def get_backup(self, backup_id: str) -> Optional[BackupArchive]:
        with self._lock:
            return self._backups.get(backup_id)

    def get_snapshot(self, snapshot_id: str) -> Optional[ClusterSnapshot]:
        with self._lock:
            return self._snapshots.get(snapshot_id)

    def get_checkpoint(self, checkpoint_id: str) -> Optional[CheckpointDescriptor]:
        with self._lock:
            return self._checkpoints.get(checkpoint_id)

    def list_backups(self) -> List[BackupArchive]:
        with self._lock:
            return list(self._backups.values())

    def list_snapshots(self) -> List[ClusterSnapshot]:
        with self._lock:
            return list(self._snapshots.values())

    def list_checkpoints(self) -> List[CheckpointDescriptor]:
        with self._lock:
            return list(self._checkpoints.values())
