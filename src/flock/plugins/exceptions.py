"""Plugin Subsystem Exceptions."""

from flock.exceptions import FlockError

class PluginError(FlockError):
    """Base exception for all plugin operations."""
    pass

class PluginNotFoundError(PluginError):
    """Raised when plugin ID is missing from registry."""
    pass

class PluginAlreadyInstalledError(PluginError):
    """Raised when registering an already registered plugin ID."""
    pass

class PluginDependencyError(PluginError):
    """Raised when dependencies are unresolved or circular dependencies exist."""
    pass

class PluginCompatibilityError(PluginError):
    """Raised when plugin version mismatches framework bounds."""
    pass

class PluginValidationError(PluginError):
    """Raised when plugin manifest formatting is invalid."""
    pass

class PluginSignatureError(PluginError):
    """Raised when plugin SHA-256 integrity validation fails."""
    pass

class PluginActivationError(PluginError):
    """Raised when dynamic loading initialization fails."""
    pass

class PluginSandboxError(PluginError):
    """Raised when plugins violate context execution limits."""
    pass

class PluginConfigurationError(PluginError):
    """Raised when plugin configuration schema checks fail."""
    pass

class PluginExecutionError(PluginError):
    """Raised when plugin execution blocks encounter errors."""
    pass
