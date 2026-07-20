"""Unit tests for Write-Ahead Log (WAL)."""

import pytest
import tempfile
import shutil
import os
from flock.storage.backend import FileStorageBackend
from flock.storage.wal import WriteAheadLog
from flock.storage.exceptions import WALCorruptionError


def test_wal_append_and_read() -> None:
    temp_dir = tempfile.mkdtemp()
    try:
        backend = FileStorageBackend(temp_dir)
        wal = WriteAheadLog(backend, max_segment_size=100)

        # Append two entries
        wal.append(index=1, term=1, command_id="c1", payload=b"payload-1")
        wal.append(index=2, term=1, command_id="c2", payload=b"payload-2")

        entries = wal.read_entries()
        assert len(entries) == 2
        assert entries[0].index == 1
        assert entries[0].command_id == "c1"
        assert entries[1].payload == b"payload-2"
    finally:
        shutil.rmtree(temp_dir)


def test_wal_corruption_throws() -> None:
    temp_dir = tempfile.mkdtemp()
    try:
        backend = FileStorageBackend(temp_dir)
        wal = WriteAheadLog(backend, max_segment_size=100)

        wal.append(index=1, term=1, command_id="c1", payload=b"payload")

        # Corrupt segment file on disk
        files = backend.list_files("wal_segment_")
        assert len(files) == 1
        corrupted_data = b"invalid json content"
        backend.write_atomically(files[0], corrupted_data)

        with pytest.raises(WALCorruptionError):
            wal.read_entries()
    finally:
        shutil.rmtree(temp_dir)
