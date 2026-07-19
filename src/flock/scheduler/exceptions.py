"""Custom exceptions for the distributed task scheduler subsystem."""

from flock.exceptions import FlockError

class SchedulerError(FlockError):
    """Base exception for all scheduler operations."""
    pass

class TaskValidationError(SchedulerError):
    """Raised when task definitions or constraints fail validation."""
    pass

class InvalidTaskStateTransitionError(SchedulerError):
    """Raised when an invalid task state transition is requested."""
    pass

class QueueCapacityError(SchedulerError):
    """Raised when the scheduling queue is full."""
    pass

class TaskRegistryError(SchedulerError):
    """Raised on invalid task registry synchronization or access operations."""
    pass
