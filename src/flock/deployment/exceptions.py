"""Deployment Subsystem Exceptions."""

from flock.exceptions import FlockError

class DeploymentError(FlockError):
    """Base exception for all deployment operations."""
    pass

class DeploymentNotFoundError(DeploymentError):
    """Raised when deployment target ID is missing from registry."""
    pass

class DeploymentConfigurationError(DeploymentError):
    """Raised when spec properties contain invalid layout mappings."""
    pass

class DeploymentValidationError(DeploymentError):
    """Raised when deployment schema validation fails."""
    pass

class RolloutFailedError(DeploymentError):
    """Raised when upgrade checks hit failure thresholds."""
    pass

class RollbackFailedError(DeploymentError):
    """Raised when restoring past stable versions fails."""
    pass

class EnvironmentSyncError(DeploymentError):
    """Raised when cluster nodes fail env state syncs."""
    pass

class InfrastructureExportError(DeploymentError):
    """Raised when exporter engines write parameters fail."""
    pass
