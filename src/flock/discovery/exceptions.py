"""Custom exceptions for the peer discovery subsystem."""

from flock.exceptions import FlockError

class DiscoveryError(FlockError):
    """Base exception for all discovery operations."""
    pass

class DiscoveryTimeoutError(DiscoveryError):
    """Raised when a discovery request times out waiting for responses."""
    pass

class RegistrySyncError(DiscoveryError):
    """Raised when peer registry state operations fail or conflict."""
    pass

class InvalidDiscoveryMessageError(DiscoveryError):
    """Raised when a malformed or incompatible discovery packet is received."""
    pass
