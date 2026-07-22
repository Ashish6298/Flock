"""Typed exception hierarchy for the Fleet management and Governance control plane."""

from flock.exceptions import FlockError

class ControlPlaneError(FlockError):
    """Base exception for all control plane and fleet management operations."""
    pass

class FleetRegistrationError(ControlPlaneError):
    """Raised when fleet definition or registration fails."""
    pass

class ClusterEnrollmentError(ControlPlaneError):
    """Raised when registering or validating a cluster inside the fleet fails."""
    pass

class GovernancePolicyError(ControlPlaneError):
    """Raised when governance policy compliance checks or rules evaluation fail."""
    pass

class FleetUpgradeError(ControlPlaneError):
    """Raised when rolling upgrades coordinates fail or encounter conflicts."""
    pass

class MaintenanceWindowError(ControlPlaneError):
    """Raised when maintenance window schedules overlap or execution fails."""
    pass

class GlobalConfigurationError(ControlPlaneError):
    """Raised when fleet configuration schema validation fails."""
    pass
