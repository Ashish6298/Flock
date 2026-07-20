"""Unit tests for RecoveryEngine."""

import os
import shutil
import tempfile
import time
from unittest.mock import MagicMock
import pytest
from flock.snapshot.storage import SnapshotStorage
from flock.storage.backend import FileStorageBackend
from flock.storage.engine import PersistentStorageEngine
from flock.storage.models import StorageConfiguration, RecoveryCheckpoint
from flock.storage.recovery import RecoveryEngine
from flock.statemachine.service import StateMachineService


def test_recovery_engine_rebuilds_state() -> None:
    temp_dir = tempfile.mkdtemp()
    try:
        backend = FileStorageBackend(temp_dir)
        config = StorageConfiguration(data_directory=temp_dir)
        engine = PersistentStorageEngine(backend, config)

        # Write FSM snapshot mock data to storage
        snap_data = b'{"state": {"score": 99}, "executed_commands": []}'
        engine.write_snapshot_data("snap-checksum", snap_data)

        # Write checkpoint
        checkpoint = RecoveryCheckpoint(
            snapshot_id="snap-checksum",
            last_included_index=2,
            last_included_term=1,
            wal_offset=0,
        )
        engine.write_checkpoint(checkpoint)

        # Append FSM commands to WAL (index 3 and 4)
        # WAL will automatically assign checksums
        engine.wal.append(index=3, term=1, command_id="c3", payload=b'{"command_id": "c3", "operation": "PUT", "key": "name", "value": "alice", "timestamp": 0.0}')
        engine.wal.append(index=4, term=1, command_id="c4", payload=b'{"command_id": "c4", "operation": "PUT", "key": "age", "value": 30, "timestamp": 0.0}')

        # Mock FSM Service & SnapshotStorage
        fsm = MagicMock(spec=StateMachineService)
        # Mock consensus log reference inside FSM mock structure
        fsm._consensus = MagicMock()
        fsm._consensus._log = MagicMock()

        snap_store = SnapshotStorage()

        recovery = RecoveryEngine(engine, fsm, snap_store)
        res = recovery.recover_node_state()

        assert res.success is True
        assert res.entries_replayed == 2

        # Verify FSM restore was called once with snapshot metadata & data
        fsm.restore_snapshot.assert_called_once()
        assert fsm.apply_committed_entry.call_count == 2
    finally:
        shutil.rmtree(temp_dir)
