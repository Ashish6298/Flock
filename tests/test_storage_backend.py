"""Unit tests for Storage Backend."""

import os
import shutil
import tempfile
import pytest
from flock.storage.backend import FileStorageBackend
from flock.storage.exceptions import StorageBackendError


def test_file_storage_backend_operations() -> None:
    temp_dir = tempfile.mkdtemp()
    try:
        backend = FileStorageBackend(temp_dir)
        backend.write_atomically("test.txt", b"hello world")

        assert backend.exists("test.txt") is True
        assert backend.read_file("test.txt") == b"hello world"

        # List files prefix
        files = backend.list_files("test")
        assert len(files) == 1
        assert files[0] == "test.txt"

        # Delete file
        backend.delete_file("test.txt")
        assert backend.exists("test.txt") is False
    finally:
        shutil.rmtree(temp_dir)


def test_read_missing_raises() -> None:
    temp_dir = tempfile.mkdtemp()
    try:
        backend = FileStorageBackend(temp_dir)
        with pytest.raises(StorageBackendError):
            backend.read_file("missing.txt")
    finally:
        shutil.rmtree(temp_dir)
