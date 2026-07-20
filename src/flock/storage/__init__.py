"""Init for storage package."""

from flock.storage.exceptions import (
    StorageError,
    WALCorruptionError,
    StorageRecoveryError,
    StorageIntegrityError,
    StorageBackendError,
    CheckpointMismatchError,
    SegmentRotationError,
    ReplayValidationError,
    PersistenceFailureError,
)
from flock.storage.models import (
    WALEntry,
    WALSegment,
    StorageMetadata,
    RecoveryCheckpoint,
    PersistentState,
    StorageStatistics,
    WALReplayResult,
    StorageConfiguration,
    StorageHealthReport,
)
from flock.storage.backend import StorageBackend, FileStorageBackend
from flock.storage.wal import WriteAheadLog
from flock.storage.engine import PersistentStorageEngine
from flock.storage.recovery import RecoveryEngine
from flock.storage.service import StorageService

__all__ = [
    "StorageError",
    "WALCorruptionError",
    "StorageRecoveryError",
    "StorageIntegrityError",
    "StorageBackendError",
    "CheckpointMismatchError",
    "SegmentRotationError",
    "ReplayValidationError",
    "PersistenceFailureError",
    "WALEntry",
    "WALSegment",
    "StorageMetadata",
    "RecoveryCheckpoint",
    "PersistentState",
    "StorageStatistics",
    "WALReplayResult",
    "StorageConfiguration",
    "StorageHealthReport",
    "StorageBackend",
    "FileStorageBackend",
    "WriteAheadLog",
    "PersistentStorageEngine",
    "RecoveryEngine",
    "StorageService",
]
