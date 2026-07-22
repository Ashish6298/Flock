"""Custom exceptions for the distributed retry and recovery subsystem."""

from flock.exceptions import FlockError

class RecoveryError(FlockError):
    """Base exception for all task retry and recovery operations."""
    pass

class RetryLimitExceededError(RecoveryError):
    """Raised when maximum task retry attempts are exhausted."""
    pass

class RecoveryTimeoutError(RecoveryError):
    """Raised when a task failover recovery operation times out."""
    pass

class RecoveryPolicyViolationError(RecoveryError):
    """Raised when recovery decisions violate configured constraints."""
    pass

class DuplicateRecoveryError(RecoveryError):
    """Raised when starting recovery on an already active recovery task."""
    pass

class RecoveryStateError(RecoveryError):
    """Raised when illegal recovery state transitions are requested."""
    pass

class UnrecoverableTaskError(RecoveryError):
    """Raised when a task is determined to be non-retryable."""
    pass

class SnapshotError(RecoveryError):
    """Raised when cluster state snapshot creation, deletion, or validation fails."""
    pass

class BackupError(RecoveryError):
    """Raised when writing, compression, or cataloging of backups fails."""
    pass

class RestoreError(RecoveryError):
    """Raised when cluster or node state restoration fails."""
    pass

class CheckpointError(RecoveryError):
    """Raised when distributed checkpoints fail validation or synchronization."""
    pass

class IntegrityError(RecoveryError):
    """Raised when backup data checksum or digital signature verification fails."""
    pass

class RetentionError(RecoveryError):
    """Raised when retention policy execution or cleanup fails."""
    pass

class ContinuityError(RecoveryError):
    """Raised when failover orchestration or business continuity plans fail."""
    pass

