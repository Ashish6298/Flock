"""Federation Exceptions."""

from flock.exceptions import FlockError

class FederationError(FlockError):
    """Base exception for all federation operations."""
    pass

class ClusterUnavailableError(FederationError):
    """Raised when federation target cluster is unreachable."""
    pass

class FederationRoutingError(FederationError):
    """Raised when cross-cluster task routing fails."""
    pass

class CrossClusterReplicationError(FederationError):
    """Raised when metadata replication fails."""
    pass

class FederationPolicyViolationError(FederationError):
    """Raised when scheduling violates global boundary policies."""
    pass

class GlobalSchedulingError(FederationError):
    """Raised when global task scheduling fails."""
    pass
