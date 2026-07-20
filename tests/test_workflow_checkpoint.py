"""Unit tests for WorkflowCheckpointManager."""

import os
import shutil
import tempfile
from flock.storage.backend import FileStorageBackend
from flock.workflow.checkpoint import WorkflowCheckpointManager
from flock.workflow.models import WorkflowCheckpoint


def test_checkpoint_persists_to_backend() -> None:
    temp_dir = tempfile.mkdtemp()
    try:
        backend = FileStorageBackend(temp_dir)
        manager = WorkflowCheckpointManager(backend)

        chk = WorkflowCheckpoint(
            instance_id="inst-12",
            completed_nodes=["n1"],
            pending_nodes=["n2"],
        )

        manager.save_checkpoint(chk)
        loaded = manager.load_checkpoint("inst-12")

        assert loaded is not None
        assert loaded.completed_nodes == ["n1"]
        assert loaded.pending_nodes == ["n2"]
    finally:
        shutil.rmtree(temp_dir)
