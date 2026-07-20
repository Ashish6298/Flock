"""Workflow Exceptions."""

from flock.exceptions import FlockError

class WorkflowError(FlockError):
    """Base exception for all workflow operations."""
    pass

class WorkflowValidationError(WorkflowError):
    """Raised when DAG properties fail validation checks."""
    pass

class CircularDependencyError(WorkflowError):
    """Raised when a loop is detected inside DAG edges."""
    pass

class WorkflowExecutionError(WorkflowError):
    """Raised when a task stage execution fails."""
    pass

class WorkflowCheckpointError(WorkflowError):
    """Raised when snapshot serialization or flush fails."""
    pass

class DependencyResolutionError(WorkflowError):
    """Raised when topological ordering cannot resolve target stages."""
    pass

class WorkflowRecoveryError(WorkflowError):
    """Raised when checkpoint restoration fails."""
    pass
