"""Pluggable Storage Backend abstraction and Local Filesystem implementation."""

from __future__ import annotations

import abc
import os
import shutil
import tempfile
from typing import Dict, List, Optional, Tuple

from flock.storage.exceptions import StorageBackendError


class StorageBackend(abc.ABC):
    """Abstract interface defining required storage IO primitives."""

    @abc.abstractmethod
    def write_atomically(self, path: str, data: bytes) -> None:
        """Atomically write data block to disk using temp-swap."""
        pass

    @abc.abstractmethod
    def read_file(self, path: str) -> bytes:
        """Read data block from disk."""
        pass

    @abc.abstractmethod
    def exists(self, path: str) -> bool:
        """Check if file path exists."""
        pass

    @abc.abstractmethod
    def delete_file(self, path: str) -> None:
        """Delete file from disk."""
        pass

    @abc.abstractmethod
    def list_files(self, prefix: str) -> List[str]:
        """List files matching prefix."""
        pass


class FileStorageBackend(StorageBackend):
    """Local filesystem storage backend with atomic renames."""

    def __init__(self, root_dir: str) -> None:
        self.root_dir = root_dir
        os.makedirs(root_dir, exist_ok=True)

    def write_atomically(self, path: str, data: bytes) -> None:
        full_path = os.path.join(self.root_dir, path)
        parent_dir = os.path.dirname(full_path)
        os.makedirs(parent_dir, exist_ok=True)

        # Stage in temporary file and rename atomically
        try:
            fd, temp_path = tempfile.mkstemp(dir=parent_dir)
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(fd)

            shutil.move(temp_path, full_path)
        except Exception as exc:
            raise StorageBackendError(f"Atomic write to '{path}' failed: {exc}") from exc

    def read_file(self, path: str) -> bytes:
        full_path = os.path.join(self.root_dir, path)
        if not os.path.exists(full_path):
            raise StorageBackendError(f"File '{path}' not found.")
        try:
            with open(full_path, "rb") as f:
                return f.read()
        except Exception as exc:
            raise StorageBackendError(f"Reading file '{path}' failed: {exc}") from exc

    def exists(self, path: str) -> bool:
        return os.path.exists(os.path.join(self.root_dir, path))

    def delete_file(self, path: str) -> None:
        full_path = os.path.join(self.root_dir, path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except Exception as exc:
                raise StorageBackendError(f"Deleting file '{path}' failed: {exc}") from exc

    def list_files(self, prefix: str) -> List[str]:
        # Walk directory and return basenames starting with prefix
        try:
            files = os.listdir(self.root_dir)
            return sorted([f for f in files if f.startswith(prefix)])
        except Exception as exc:
            raise StorageBackendError(f"Listing files in root failed: {exc}") from exc
