"""Write-Ahead Log (WAL) manager with segment rotation and validation."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from typing import List, Optional

from flock.storage.backend import StorageBackend
from flock.storage.exceptions import WALCorruptionError
from flock.storage.models import WALEntry, WALSegment


class WriteAheadLog:
    """Manages appending, rotation, checksumming, and loading of log entries."""

    def __init__(self, backend: StorageBackend, max_segment_size: int = 1024 * 1024) -> None:
        self._backend = backend
        self.max_segment_size = max_segment_size
        self._lock = threading.Lock()

        self._active_segment_id: Optional[str] = None
        self._active_entries: List[WALEntry] = []
        self._start_index = 0

    def append(self, index: int, term: int, command_id: str, payload: bytes) -> WALEntry:
        """Append a transaction record to the Write-Ahead Log.

        Handles CRC-style checksum verification and automatic segment rotation.
        """
        with self._lock:
            if not self._active_segment_id:
                self._rotate_segment(index)

            # Generate SHA-256 Checksum
            hash_input = f"{index}:{term}:{command_id}".encode("utf-8") + payload
            checksum = hashlib.sha256(hash_input).hexdigest()

            entry = WALEntry(
                index=index,
                term=term,
                command_id=command_id,
                payload=payload,
                timestamp=time.time(),
                checksum=checksum,
            )

            self._active_entries.append(entry)

            # Save updated active segment
            self._save_active_segment()

            # Trigger rotation if size limit is exceeded
            total_size = sum(len(e.payload) for e in self._active_entries)
            if total_size >= self.max_segment_size:
                self._rotate_segment(index + 1)

            return entry

    def read_entries(self) -> List[WALEntry]:
        """Read all validated WAL entries from storage across all segments."""
        with self._lock:
            all_entries: List[WALEntry] = []
            segment_files = self._backend.list_files("wal_segment_")
            
            for file_name in segment_files:
                data = self._backend.read_file(file_name)
                if not data:
                    continue
                try:
                    raw_entries = json.loads(data.decode("utf-8"))
                    for raw in raw_entries:
                        # Decode payload from base64 if encoded (JSON serialization requires text)
                        import base64
                        raw_payload = base64.b64decode(raw["payload"])
                        entry = WALEntry(
                            index=raw["index"],
                            term=raw["term"],
                            command_id=raw["command_id"],
                            payload=raw_payload,
                            timestamp=raw["timestamp"],
                            checksum=raw["checksum"],
                        )
                        # Verify integrity checksum
                        hash_input = f"{entry.index}:{entry.term}:{entry.command_id}".encode("utf-8") + entry.payload
                        expected = hashlib.sha256(hash_input).hexdigest()
                        if expected != entry.checksum:
                            raise WALCorruptionError(f"Checksum mismatch for WAL index {entry.index}.")
                        
                        all_entries.append(entry)
                except Exception as exc:
                    raise WALCorruptionError(f"Corruption in segment file '{file_name}': {exc}") from exc

            return all_entries

    def truncate_prefix(self, last_included_index: int) -> None:
        """Purge obsolete segment files whose indices fall below threshold."""
        with self._lock:
            segment_files = self._backend.list_files("wal_segment_")
            for file_name in segment_files:
                # Extract end index from file name if encoded, or load manifest
                # Let's inspect the files by reading them
                try:
                    data = self._backend.read_file(file_name)
                    raw_entries = json.loads(data.decode("utf-8"))
                    if not raw_entries:
                        continue
                    max_idx = max(e["index"] for e in raw_entries)
                    # If all entries in this segment are older than last_included_index, delete it
                    if max_idx <= last_included_index:
                        # Active segment should not be deleted if it is active
                        if file_name != f"wal_segment_{self._active_segment_id}":
                            self._backend.delete_file(file_name)
                except Exception:
                    pass

    def _rotate_segment(self, start_index: int) -> None:
        """Rotate segment by creating a new active log file on disk."""
        self._active_segment_id = f"{start_index:09d}"
        self._active_entries = []
        self._start_index = start_index

    def _save_active_segment(self) -> None:
        """Serialize and atomically save the active segment entries."""
        if not self._active_segment_id:
            return
        
        # We need base64 encoding to serialize raw bytes safely to JSON
        import base64
        serializable = []
        for e in self._active_entries:
            serializable.append({
                "index": e.index,
                "term": e.term,
                "command_id": e.command_id,
                "payload": base64.b64encode(e.payload).decode("utf-8"),
                "timestamp": e.timestamp,
                "checksum": e.checksum,
            })

        data_bytes = json.dumps(serializable).encode("utf-8")
        self._backend.write_atomically(f"wal_segment_{self._active_segment_id}", data_bytes)
