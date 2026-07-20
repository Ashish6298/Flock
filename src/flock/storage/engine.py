"""Durable persistence engine orchestrating atomic writes and filesystem syncs."""

from __future__ import annotations

import json
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import structlog

from flock.storage.backend import StorageBackend
from flock.storage.exceptions import PersistenceFailureError, StorageIntegrityError
from flock.storage.models import (
    RecoveryCheckpoint,
    StorageConfiguration,
    StorageMetadata,
    StorageStatistics,
)
from flock.storage.wal import WriteAheadLog

logger = structlog.get_logger()


class PersistentStorageEngine:
    """Manages WAL writes, metadata checkpoints, and retention cleanups."""

    def __init__(self, backend: StorageBackend, config: StorageConfiguration) -> None:
        self._backend = backend
        self._config = config
        self._lock = threading.Lock()

        # Write-Ahead Log instance
        self.wal = WriteAheadLog(self._backend, max_segment_size=self._config.max_segment_size_bytes)

    def write_metadata(self, metadata: StorageMetadata) -> None:
        """Atomically persist node consensus metadata (term, voted_for, last_applied_index)."""
        with self._lock:
            try:
                data_bytes = json.dumps(metadata.model_dump()).encode("utf-8")
                self._backend.write_atomically("storage_metadata.json", data_bytes)
            except Exception as exc:
                raise PersistenceFailureError(f"Failed to write metadata: {exc}") from exc

    def read_metadata(self) -> Optional[StorageMetadata]:
        """Read persisted consensus metadata if present."""
        with self._lock:
            if not self._backend.exists("storage_metadata.json"):
                return None
            try:
                data = self._backend.read_file("storage_metadata.json")
                raw = json.loads(data.decode("utf-8"))
                return StorageMetadata(**raw)
            except Exception as exc:
                raise StorageIntegrityError(f"Failed to parse metadata file: {exc}") from exc

    def write_checkpoint(self, checkpoint: RecoveryCheckpoint) -> None:
        """Atomically persist a transaction log checkpoint marker."""
        with self._lock:
            try:
                data_bytes = json.dumps(checkpoint.model_dump()).encode("utf-8")
                self._backend.write_atomically("checkpoint.json", data_bytes)
            except Exception as exc:
                raise PersistenceFailureError(f"Failed to write checkpoint: {exc}") from exc

    def read_checkpoint(self) -> Optional[RecoveryCheckpoint]:
        """Read persisted checkpoint if present."""
        with self._lock:
            if not self._backend.exists("checkpoint.json"):
                return None
            try:
                data = self._backend.read_file("checkpoint.json")
                raw = json.loads(data.decode("utf-8"))
                return RecoveryCheckpoint(**raw)
            except Exception as exc:
                raise StorageIntegrityError(f"Failed to parse checkpoint file: {exc}") from exc

    def write_snapshot_data(self, snapshot_id: str, data: bytes) -> None:
        """Atomically persist snapshot payload data to disk."""
        with self._lock:
            try:
                self._backend.write_atomically(f"snapshot_{snapshot_id}.bin", data)
            except Exception as exc:
                raise PersistenceFailureError(f"Failed to save snapshot file '{snapshot_id}': {exc}") from exc

    def read_snapshot_data(self, snapshot_id: str) -> bytes:
        """Read snapshot payload data from disk."""
        with self._lock:
            try:
                return self._backend.read_file(f"snapshot_{snapshot_id}.bin")
            except Exception as exc:
                raise StorageIntegrityError(f"Failed to read snapshot file '{snapshot_id}': {exc}") from exc

    def get_statistics(self) -> StorageStatistics:
        """Gather size and allocation metrics for disk files."""
        with self._lock:
            segment_files = self._backend.list_files("wal_segment_")
            total_size = 0
            for file_name in segment_files:
                try:
                    data = self._backend.read_file(file_name)
                    total_size += len(data)
                except Exception:
                    pass

            return StorageStatistics(
                total_entries_written=0,  # Calculated dynamically from wal entries if needed
                segment_count=len(segment_files),
                size_on_disk_bytes=total_size,
            )

    def compact_log_with_snapshot(
        self,
        snapshot_id: str,
        last_included_index: int,
        last_included_term: int,
        snapshot_bytes: bytes,
    ) -> None:
        """Coordinate WAL truncation after successful snapshot persistence."""
        # 1. Save Snapshot data
        self.write_snapshot_data(snapshot_id, snapshot_bytes)

        # 2. Write checkpoint descriptor
        checkpoint = RecoveryCheckpoint(
            snapshot_id=snapshot_id,
            last_included_index=last_included_index,
            last_included_term=last_included_term,
            wal_offset=0,
        )
        self.write_checkpoint(checkpoint)

        # 3. Truncate obsolete WAL segments below compaction threshold
        self.wal.truncate_prefix(last_included_index)
        logger.info(
            "WAL prefix compacted with snapshot",
            snapshot_id=snapshot_id,
            last_included_index=last_included_index,
        )
