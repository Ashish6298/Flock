"""Base exceptions hierarchy for the Flock framework."""

class FlockError(Exception):
    """Base exception for all Flock framework errors."""
    pass

class TransportError(FlockError):
    """Raised when a networking/transport operation fails."""
    pass

class SerializationError(FlockError):
    """Raised when serializing or deserializing a message fails."""
    pass

class DiscoveryError(FlockError):
    """Raised when a node discovery operation fails."""
    pass

class ValidationError(FlockError):
    """Raised when configuration or input validation fails."""
    pass
