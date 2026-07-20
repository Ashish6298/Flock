"""Unit tests for workflow recovery logic."""

import os
import shutil
import tempfile
import pytest
from flock.storage.backend import FileStorageBackend
from flock.workflow.checkpoint import WorkflowCheckpointManager
from flock.workflow.models import WorkflowCheckpoint


def test_checkpoint_restores_state() -> None:
    temp_dir = tempfile.mkdtemp()
    try:
        backend = FileStorageBackend(temp_dir)
        manager = WorkflowCheckpointManager(backend)

        chk = WorkflowCheckpoint(
            instance_id="wf-inst-9",
            completed_nodes=["step-1"],
            pending_nodes=["step-2", "step-3"],
        )

        manager.save_checkpoint(chk)
        restored = manager.load_checkpoint("wf-inst-9")

        assert restored is not None
        assert len(restored.completed_nodes) == 1
        assert "step-1" in restored.completed_nodes
    finally:
        shutil.rmtree(temp_dir)
