"""Orchestrator Exceptions."""

from flock.exceptions import FlockError

class OrchestratorError(FlockError):
    """Base exception for all orchestrator operations."""
    pass

class SchedulingConflictError(OrchestratorError):
    """Raised when task placement schedules conflict."""
    pass

class ScalingPolicyViolationError(OrchestratorError):
    """Raised when size boundaries violate configuration constraints."""
    pass

class MigrationRejectedError(OrchestratorError):
    """Raised when migration checks reject candidate nodes."""
    pass

class OptimizationFailureError(OrchestratorError):
    """Raised when load optimization algorithms fail."""
    pass
