"""Custom exceptions for the distributed result collection and completion subsystem."""

from flock.exceptions import FlockError

class ResultCollectionError(FlockError):
    """Base exception for all result collection operations."""
    pass

class ResultSerializationError(ResultCollectionError):
    """Raised when result payload serialization or deserialization fails."""
    pass

class DuplicateResultError(ResultCollectionError):
    """Raised when registering a task result that has already been registered."""
    pass

class UnknownResultError(ResultCollectionError):
    """Raised when requesting task results that are not registered."""
    pass

class InvalidResultStateError(ResultCollectionError):
    """Raised when result state transitions are illegal."""
    pass

class ChecksumMismatchError(ResultCollectionError):
    """Raised when payload hash validation checks fail."""
    pass

class ResultTimeoutError(ResultCollectionError):
    """Raised when waiting for a task completion result times out."""
    pass
