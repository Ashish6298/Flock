"""Custom exceptions for the worker runtime and execution engine subsystem."""

from flock.exceptions import FlockError

class ExecutionError(FlockError):
    """Base exception for all local runtime execution operations."""
    pass

class ExecutionStateError(ExecutionError):
    """Raised when an invalid local execution state transition is requested."""
    pass

class WorkerUnavailableError(ExecutionError):
    """Raised when no execution workers or threads are available to process a task."""
    pass

class TaskCancellationError(ExecutionError):
    """Raised when a task cancellation operation fails or is rejected."""
    pass

class ExecutorInitializationError(ExecutionError):
    """Raised when concrete executor pool backend setups fail."""
    pass
