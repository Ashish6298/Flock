"""Disaster Recovery coordinator engine orchestrating snapshots, backups, restores, and failovers."""

from __future__ import annotations

import time
import threading
from typing import Dict, List, Optional, Any
from flock.recovery.exceptions import RecoveryError
from flock.recovery.models import ClusterSnapshot, BackupArchive, CheckpointDescriptor, RetentionPolicy
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
from flock.security.encryption import CryptographyEngine


class RecoveryCoordinator:
    """Orchestrates backup schedules, snapshots catalogs, integrity checks, and node restorations."""

    def __init__(
        self,
        node_id: str,
        crypto: CryptographyEngine,
    ) -> None:
        self.node_id = node_id
        self._lock = threading.RLock()
        
        # Subsystem engines initialization
        self.snapshot = SnapshotManager()
        self.backup = BackupManager(crypto)
        self.restore = RestoreManager(self.backup, crypto)
        self.checkpoint = CheckpointManager(crypto)
        self.retention = RetentionManager(self.backup)
        self.integrity = IntegrityVerifier(self.backup, crypto)
        self.catalog = RecoveryCatalog()
        self.policy = RecoveryPolicyManager()
        self.continuity = BusinessContinuityPlanner(node_id)
        self.metrics = RecoveryMetricsTracker()

    def run_backup_cycle(self, state_data: Dict[str, Any], policy_id: str) -> BackupArchive:
        """Run a full workflow cycle: create snapshot, write backup, enforce retention cataloging."""
        with self._lock:
            # 1. Take Snapshot
            self.metrics.record_snapshot()
            snapshot = self.snapshot.create_snapshot(state_data)
            self.catalog.register_snapshot(snapshot)
            
            # 2. Write Backup
            archive = self.backup.create_backup(snapshot, backup_type="full", encrypt=True)
            self.catalog.register_backup(archive)
            self.metrics.record_backup(archive.timestamp)
            
            # 3. Enforce Retention
            policy = self.policy.get_policy(policy_id)
            if policy:
                self.retention.enforce_retention(policy)
                
            return archive

    def run_restore_cycle(self, backup_id: str) -> Dict[str, Any]:
        """Validate integrity signature, decrypt, and reinstate state machine data."""
        with self._lock:
            # Check Integrity
            self.integrity.verify_archive_integrity(backup_id)
            
            # Perform Restore
            state = self.restore.restore_backup(backup_id)
            self.metrics.record_restore(time.time())
            
            return state
