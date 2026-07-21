"""Service Mesh Exceptions."""

from flock.exceptions import FlockError

class MeshError(FlockError):
    """Base exception for all mesh operations."""
    pass

class ServiceNotFoundError(MeshError):
    """Raised when service lookup references missing registrations."""
    pass

class MeshConfigurationError(MeshError):
    """Raised when mesh config variables fail validation."""
    pass

class RoutingPolicyError(MeshError):
    """Raised when path mapping rules are corrupted."""
    pass

class CircuitBreakerOpenError(MeshError):
    """Raised when target breaker limits failover calls."""
    pass

class ConnectionRejectedError(MeshError):
    """Raised when handshake connections fail parameters check."""
    pass

class CertificateValidationError(MeshError):
    """Raised when mutual TLS identities are invalid."""
    pass

class TrafficPolicyViolationError(MeshError):
    """Raised when access rules reject request flow."""
    pass

class RetryExhaustedError(MeshError):
    """Raised when call attempts hit the max retry ceiling."""
    pass

class MeshSynchronizationError(MeshError):
    """Raised when cluster nodes fail mesh state syncs."""
    pass

class NetworkPartitionError(MeshError):
    """Raised when topology splits isolate cluster components."""
    pass
