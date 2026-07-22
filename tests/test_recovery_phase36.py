"""Unit tests for Phase 36 Enterprise Disaster Recovery, Backup, Snapshot & Business Continuity Subsystem."""

import time
import pytest
from unittest.mock import MagicMock, AsyncMock

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.protocol.packet import MessageType
from flock.security.encryption import CryptographyEngine
from flock.recovery.exceptions import (
    RecoveryError,
    SnapshotError,
    BackupError,
    RestoreError,
    CheckpointError,
    IntegrityError,
    RetentionError,
    ContinuityError,
)
from flock.recovery.models import (
    ClusterSnapshot,
    BackupArchive,
    CheckpointDescriptor,
    RetentionPolicy,
)
from flock.recovery.snapshot import SnapshotManager
from flock.recovery.backup import BackupManager
from flock.recovery.restore import RestoreManager
from flock.recovery.checkpoint import CheckpointManager
from flock.recovery.retention import RetentionManager
from flock.recovery.integrity import IntegrityVerifier
from flock.recovery.catalog import RecoveryCatalog
from flock.recovery.policy_manager import RecoveryPolicyManager
from flock.recovery.continuity import BusinessContinuityPlanner
from flock.recovery.metrics import RecoveryMetricsTracker
from flock.recovery.coordinator import RecoveryCoordinator
from flock.recovery.disaster_service import DisasterRecoveryService


# -----------------------------------------------------------------------------
# Snapshot Manager Tests
# -----------------------------------------------------------------------------

def test_snapshot_creation() -> None:
    mgr = SnapshotManager()
    state = {"users": {"alice": 25}, "count": 10}
    snap = mgr.create_snapshot(state, metadata={"author": "admin"})
    
    assert snap.snapshot_id is not None
    assert snap.state_hash is not None
    assert snap.metadata["author"] == "admin"
    assert snap.data["count"] == 10
    
    # Retrieve
    retrieved = mgr.get_snapshot(snap.snapshot_id)
    assert retrieved.state_hash == snap.state_hash
    
    # Delete
    mgr.delete_snapshot(snap.snapshot_id)
    with pytest.raises(SnapshotError):
        mgr.get_snapshot(snap.snapshot_id)


# -----------------------------------------------------------------------------
# Backup & Restore Tests
# -----------------------------------------------------------------------------

def test_backup_and_restore_workflow() -> None:
    crypto = CryptographyEngine(b"backup_and_restore_secret_16bytes")
    snap_mgr = SnapshotManager()
    backup_mgr = BackupManager(crypto)
    restore_mgr = RestoreManager(backup_mgr, crypto)
    
    state = {"config": {"nodes": 3}, "version": 1}
    snap = snap_mgr.create_snapshot(state)
    
    # Encrypted Backup
    archive = backup_mgr.create_backup(snap, backup_type="full", encrypt=True)
    assert archive.encrypted is True
    
    # Restore
    restored_state = restore_mgr.restore_backup(archive.backup_id)
    assert restored_state == state
    assert restore_mgr.get_last_restore_time(archive.backup_id) > 0.0


def test_restore_tampered_backup_raises_integrity_error() -> None:
    crypto = CryptographyEngine(b"backup_and_restore_secret_16bytes")
    snap_mgr = SnapshotManager()
    backup_mgr = BackupManager(crypto)
    restore_mgr = RestoreManager(backup_mgr, crypto)
    
    snap = snap_mgr.create_snapshot({"a": 1})
    archive = backup_mgr.create_backup(snap, encrypt=False)
    
    # Corrupt raw data in backup manager mock
    backup_mgr._raw_backups[archive.backup_id] = '{"a": 2}'
    
    with pytest.raises(RestoreError, match="integrity"):
        restore_mgr.restore_backup(archive.backup_id)


# -----------------------------------------------------------------------------
# Checkpoint Tests
# -----------------------------------------------------------------------------

def test_checkpoint_lifecycle() -> None:
    crypto = CryptographyEngine(b"checkpoint_secret_key_16bytes")
    mgr = CheckpointManager(crypto)
    
    chk = mgr.create_checkpoint("coordinator-1", "snap-12345")
    assert chk.sequence_number == 1
    assert chk.coordinator_node_id == "coordinator-1"
    
    assert mgr.validate_checkpoint(chk) is True
    
    # Tampering test
    tampered_chk = CheckpointDescriptor(
        checkpoint_id=chk.checkpoint_id,
        sequence_number=chk.sequence_number,
        timestamp=chk.timestamp,
        coordinator_node_id="tampered-node",
        snapshot_id=chk.snapshot_id,
        integrity_signature=chk.integrity_signature,
    )
    with pytest.raises(CheckpointError):
        mgr.validate_checkpoint(tampered_chk)


# -----------------------------------------------------------------------------
# Retention Policy Tests
# -----------------------------------------------------------------------------

def test_backup_retention_enforcement() -> None:
    crypto = CryptographyEngine(b"retention_secret_key_16bytes")
    snap_mgr = SnapshotManager()
    backup_mgr = BackupManager(crypto)
    ret_mgr = RetentionManager(backup_mgr)
    
    # Create 3 archives
    for i in range(3):
        snap = snap_mgr.create_snapshot({f"key-{i}": i})
        backup_mgr.create_backup(snap, encrypt=False)
        time.sleep(0.01)
        
    policy = RetentionPolicy(policy_id="p1", max_backups_retained=2, ttl_seconds=3600.0)
    
    evicted_ids = []
    deleted = ret_mgr.enforce_retention(policy, eviction_callback=lambda bid: evicted_ids.append(bid))
    
    assert len(deleted) == 1
    assert len(evicted_ids) == 1
    assert len(backup_mgr.list_archives()) == 2


# -----------------------------------------------------------------------------
# Business Continuity & Failover Tests
# -----------------------------------------------------------------------------

def test_business_continuity_failover() -> None:
    planner = BusinessContinuityPlanner("node-1")
    
    # Initiate failover
    planner.initiate_failover("node-2", "Leader node-1 disconnected")
    status = planner.get_failover_status()
    assert status["failover_in_progress"] is True
    assert status["active_plan"] == "failover-to-node-2"
    
    # Initiate again should raise error
    with pytest.raises(ContinuityError):
        planner.initiate_failover("node-3", "Leader split brain")
        
    # Complete failover
    planner.complete_failover()
    status_completed = planner.get_failover_status()
    assert status_completed["failover_in_progress"] is False
    assert status_completed["history"][-1]["status"] == "completed"


# -----------------------------------------------------------------------------
# Recovery Service Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_recovery_service_integration() -> None:
    bus = MagicMock(spec=MessageBus)
    bus.router = MagicMock()
    bus.send = AsyncMock()
    
    events = EventBus()
    event_list = []
    
    async def on_init(data: dict) -> None: # type: ignore[type-arg]
        event_list.append(data)
        
    events.subscribe("recovery.initialized", on_init)
    
    crypto = CryptographyEngine(b"recovery_service_secret_16bytes")
    service = DisasterRecoveryService("node-1", crypto, bus, events)
    
    await service.start()
    assert service._running is True
    assert len(event_list) == 1
    
    # Verify MessageBus registrations
    assert service._bus.router.register.call_count == 2
    
    await service.stop()
    assert service._running is False
