"""Unit tests for checkpoint management."""

import os
import shutil
import tempfile
from flock.storage.backend import FileStorageBackend
from flock.storage.engine import PersistentStorageEngine
from flock.storage.models import StorageConfiguration, RecoveryCheckpoint


def test_checkpoint_creation_and_restore() -> None:
    temp_dir = tempfile.mkdtemp()
    try:
        backend = FileStorageBackend(temp_dir)
        config = StorageConfiguration(data_directory=temp_dir)
        engine = PersistentStorageEngine(backend, config)

        checkpoint = RecoveryCheckpoint(
            snapshot_id="snap-chk-1",
            last_included_index=15,
            last_included_term=2,
            wal_offset=100,
        )

        engine.write_checkpoint(checkpoint)
        assert engine.read_checkpoint() == checkpoint
    finally:
        shutil.rmtree(temp_dir)
