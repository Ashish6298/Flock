"""Custom exceptions for the heartbeat and failure detection subsystem."""

from flock.exceptions import FlockError

class HeartbeatError(FlockError):
    """Base exception for all heartbeat and failure detection operations."""
    pass

class HealthStateTransitionError(HeartbeatError):
    """Raised when an invalid health state transition is requested."""
    pass

class HeartbeatTimeoutError(HeartbeatError):
    """Raised when heartbeat request timed out without receiving pong reply."""
    pass

class HealthRegistryError(HeartbeatError):
    """Raised on invalid health registry synchronization or access operations."""
    pass
