"""Unit tests for storage integrity validation."""

import os
import shutil
import tempfile
import pytest
from flock.storage.backend import FileStorageBackend
from flock.storage.engine import PersistentStorageEngine
from flock.storage.models import StorageConfiguration, StorageMetadata
from flock.storage.exceptions import StorageIntegrityError


def test_metadata_integrity_failure_raises() -> None:
    temp_dir = tempfile.mkdtemp()
    try:
        backend = FileStorageBackend(temp_dir)
        config = StorageConfiguration(data_directory=temp_dir)
        engine = PersistentStorageEngine(backend, config)

        # Corrupt file metadata format on disk
        backend.write_atomically("storage_metadata.json", b"corrupted data")

        with pytest.raises(StorageIntegrityError):
            engine.read_metadata()
    finally:
        shutil.rmtree(temp_dir)
