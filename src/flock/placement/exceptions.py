"""Custom exceptions for the distributed task placement subsystem."""

from flock.exceptions import FlockError

class PlacementError(FlockError):
    """Base exception for all placement operations."""
    pass

class PlacementConstraintError(PlacementError):
    """Raised when task capability constraints fail validation."""
    pass

class NoEligibleNodesError(PlacementError):
    """Raised when no healthy nodes satisfy the task capability constraints."""
    pass

class AssignmentRejectedError(PlacementError):
    """Raised when the selected worker target rejects the assignment payload."""
    pass

class PlacementRegistryError(PlacementError):
    """Raised on invalid placement registry operations or access errors."""
    pass
