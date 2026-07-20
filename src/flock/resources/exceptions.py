"""Resource Management Exceptions."""

from flock.exceptions import FlockError

class ResourceError(FlockError):
    """Base exception for all resource management operations."""
    pass

class ResourceExhaustionError(ResourceError):
    """Raised when available memory or cores limits are reached."""
    pass

class AllocationConflictError(ResourceError):
    """Raised when concurrent allocations target the same reservations."""
    pass

class QuotaViolationError(ResourceError):
    """Raised when request exceeds role or service resource quota limit."""
    pass

class ReservationExpiredError(ResourceError):
    """Raised when lease or reservation expiry block prevents operation."""
    pass

class BalancingFailureError(ResourceError):
    """Raised when workload balancing heuristics fail execution."""
    pass

class InvalidResourceSpecificationError(ResourceError):
    """Raised when metric labels or profile requests are malformed."""
    pass

class AdmissionFailureError(ResourceError):
    """Raised when admission controller rules deny task placement."""
    pass
