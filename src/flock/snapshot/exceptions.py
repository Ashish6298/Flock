"""Exceptions for snapshot and compaction subsystems."""

from flock.exceptions import FlockError

class SnapshotError(FlockError):
    """Base exception for all snapshot operations."""
    pass

class SnapshotCreationError(SnapshotError):
    """Raised when generating a snapshot fails."""
    pass

class SnapshotRestoreError(SnapshotError):
    """Raised when restoring state machine from a snapshot fails."""
    pass

class SnapshotChecksumError(SnapshotError):
    """Raised when SHA-256 validation of snapshot bytes fails."""
    pass

class SnapshotTransferError(SnapshotError):
    """Raised when transfer of chunks fails or times out."""
    pass

class SnapshotCompactionError(SnapshotError):
    """Raised when log compaction/truncation fails."""
    pass

class SnapshotVersionMismatchError(SnapshotError):
    """Raised when a snapshot version is incompatible with current code."""
    pass

class SnapshotChunkValidationError(SnapshotError):
    """Raised when snapshot chunk validation (order/index) fails."""
    pass
