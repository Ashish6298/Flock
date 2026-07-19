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
