"""Functions Subsystem Exceptions."""

from flock.exceptions import FlockError

class FunctionError(FlockError):
    """Base exception for all function operations."""
    pass

class FunctionNotFoundError(FunctionError):
    """Raised when request references missing function ID."""
    pass

class FunctionValidationError(FunctionError):
    """Raised when handler specifications fail check limits."""
    pass

class InvocationFailedError(FunctionError):
    """Raised when call execution pipeline fails to yield output."""
    pass

class RuntimeExecutionError(FunctionError):
    """Raised when user code throws an exception during evaluation."""
    pass

class ScalePolicyError(FunctionError):
    """Raised when autoscaling parameters fail checks."""
    pass

class TriggerSyncError(FunctionError):
    """Raised when sync triggers mapping fails."""
    pass
