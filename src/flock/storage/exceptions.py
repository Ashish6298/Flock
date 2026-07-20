"""Storage exceptions."""

from flock.exceptions import FlockError

class StorageError(FlockError):
    """Base exception for all storage operations."""
    pass

class WALCorruptionError(StorageError):
    """Raised when WAL entry log block checksum validation fails."""
    pass

class StorageRecoveryError(StorageError):
    """Raised when node startup recovery replay fails."""
    pass

class StorageIntegrityError(StorageError):
    """Raised when mismatch is detected between WAL, snapshot indices, or metadata."""
    pass

class StorageBackendError(StorageError):
    """Raised when disk write/read/rename operations fail."""
    pass

class CheckpointMismatchError(StorageError):
    """Raised when snapshot metadata checklist fails verification."""
    pass

class SegmentRotationError(StorageError):
    """Raised when WAL log file rotation fails."""
    pass

class ReplayValidationError(StorageError):
    """Raised when replayed transaction list fails sanity checks."""
    pass

class PersistenceFailureError(StorageError):
    """Raised when fsync or atomic persistence fails."""
    pass
