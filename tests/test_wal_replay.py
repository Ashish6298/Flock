"""Unit tests for WAL replay scenarios."""

import os
import shutil
import tempfile
from unittest.mock import MagicMock
from flock.snapshot.storage import SnapshotStorage
from flock.storage.backend import FileStorageBackend
from flock.storage.engine import PersistentStorageEngine
from flock.storage.models import StorageConfiguration
from flock.storage.recovery import RecoveryEngine
from flock.statemachine.service import StateMachineService


def test_wal_replay_reconstructs_missing_logs() -> None:
    temp_dir = tempfile.mkdtemp()
    try:
        backend = FileStorageBackend(temp_dir)
        config = StorageConfiguration(data_directory=temp_dir)
        engine = PersistentStorageEngine(backend, config)

        # Populate WAL
        engine.wal.append(index=1, term=1, command_id="c1", payload=b"payload-1")
        engine.wal.append(index=2, term=1, command_id="c2", payload=b"payload-2")

        fsm = MagicMock(spec=StateMachineService)
        fsm._consensus = MagicMock()
        fsm._consensus._log = MagicMock()
        
        snap_store = SnapshotStorage()

        recovery = RecoveryEngine(engine, fsm, snap_store)
        res = recovery.recover_node_state()

        assert res.success is True
        assert res.entries_replayed == 2
        assert fsm.apply_committed_entry.call_count == 2
    finally:
        shutil.rmtree(temp_dir)
