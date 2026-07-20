"""Workflow Checkpoint Manager persisting progress snapshots."""

from __future__ import annotations

import json
import threading
from typing import Dict, Optional

from flock.storage.backend import StorageBackend
from flock.workflow.exceptions import WorkflowCheckpointError
from flock.workflow.models import WorkflowCheckpoint


class WorkflowCheckpointManager:
    """Saves and restores executing workflow checkpoint states atomically."""

    def __init__(self, storage_backend: StorageBackend) -> None:
        self._storage = storage_backend
        self._lock = threading.Lock()

    def save_checkpoint(self, checkpoint: WorkflowCheckpoint) -> None:
        """Atomically persist execution progress checkpoint payload on disk."""
        with self._lock:
            try:
                data_bytes = json.dumps(checkpoint.model_dump()).encode("utf-8")
                self._storage.write_atomically(f"wf_checkpoint_{checkpoint.instance_id}.json", data_bytes)
            except Exception as exc:
                raise WorkflowCheckpointError(f"Failed to persist workflow checkpoint: {exc}") from exc

    def load_checkpoint(self, instance_id: str) -> Optional[WorkflowCheckpoint]:
        """Load and restore execution progress checkpoint if found."""
        with self._lock:
            path = f"wf_checkpoint_{instance_id}.json"
            if not self._storage.exists(path):
                return None
            try:
                data = self._storage.read_file(path)
                raw = json.loads(data.decode("utf-8"))
                return WorkflowCheckpoint(**raw)
            except Exception as exc:
                raise WorkflowCheckpointError(f"Failed to load workflow checkpoint: {exc}") from exc
