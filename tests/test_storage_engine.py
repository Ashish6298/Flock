"""Unit tests for PersistentStorageEngine."""

import os
import shutil
import tempfile
from flock.storage.backend import FileStorageBackend
from flock.storage.engine import PersistentStorageEngine
from flock.storage.models import StorageConfiguration, StorageMetadata, RecoveryCheckpoint


def test_storage_engine_meta_and_checkpoint() -> None:
    temp_dir = tempfile.mkdtemp()
    try:
        backend = FileStorageBackend(temp_dir)
        config = StorageConfiguration(data_directory=temp_dir)
        engine = PersistentStorageEngine(backend, config)

        meta = StorageMetadata(
            node_id="node-1",
            current_term=5,
            voted_for="node-2",
            last_applied_index=10,
        )

        engine.write_metadata(meta)
        read_meta = engine.read_metadata()
        assert read_meta is not None
        assert read_meta.current_term == 5
        assert read_meta.voted_for == "node-2"

        # Checkpoint operations
        checkpoint = RecoveryCheckpoint(
            snapshot_id="snap-checksum",
            last_included_index=10,
            last_included_term=2,
            wal_offset=0,
        )

        engine.write_checkpoint(checkpoint)
        read_checkpoint = engine.read_checkpoint()
        assert read_checkpoint is not None
        assert read_checkpoint.snapshot_id == "snap-checksum"
    finally:
        shutil.rmtree(temp_dir)
