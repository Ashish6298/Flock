"""Custom exceptions for the cluster membership subsystem."""

from flock.exceptions import FlockError

class MembershipError(FlockError):
    """Base exception for all membership operations."""
    pass

class MembershipStateError(MembershipError):
    """Raised when an invalid membership state transition is requested."""
    pass

class DuplicateMembershipError(MembershipError):
    """Raised when registering a node that already exists in the authoritative registry."""
    pass

class SnapshotValidationError(MembershipError):
    """Raised when a membership snapshot structure or payload fails validation checks."""
    pass

class MembershipTimeoutError(MembershipError):
    """Raised when joining or synchronization operations time out."""
    pass
