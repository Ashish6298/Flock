"""Init for recovery package. Exposes all recovery, snapshot, backup, restore, and business continuity interfaces."""

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
    RecoveryMetricsReport,
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

__all__ = [
    # Exceptions
    "RecoveryError",
    "SnapshotError",
    "BackupError",
    "RestoreError",
    "CheckpointError",
    "IntegrityError",
    "RetentionError",
    "ContinuityError",
    
    # Models
    "ClusterSnapshot",
    "BackupArchive",
    "CheckpointDescriptor",
    "RetentionPolicy",
    "RecoveryMetricsReport",
    
    # Engines & Managers
    "SnapshotManager",
    "BackupManager",
    "RestoreManager",
    "CheckpointManager",
    "RetentionManager",
    "IntegrityVerifier",
    "RecoveryCatalog",
    "RecoveryPolicyManager",
    "BusinessContinuityPlanner",
    "RecoveryMetricsTracker",
    "RecoveryCoordinator",
    "DisasterRecoveryService",
]
