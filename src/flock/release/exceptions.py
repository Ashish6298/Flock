"""Typed exceptions for platform-wide release candidate verification and startup coordination."""

from flock.exceptions import FlockError

class ReleaseError(FlockError):
    """Base exception for all release lifecycle and coordination errors."""
    pass

class DependencyVerificationError(ReleaseError):
    """Raised when subsystem dependencies validation fails."""
    pass

class ConfigurationValidationError(ReleaseError):
    """Raised when startup config checks fail."""
    pass

class SubsystemLifecycleError(ReleaseError):
    """Raised when orchestrating subsystem startup/shutdown sequences fails."""
    pass

class ReadinessAssessmentError(ReleaseError):
    """Raised when release candidate compliance or health score is below threshold."""
    pass
