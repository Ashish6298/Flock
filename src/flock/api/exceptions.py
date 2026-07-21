"""API Gateway Exceptions."""

from flock.exceptions import FlockError

class ApiErrorBase(FlockError):
    """Base exception for all api gateway operations."""
    pass

class RouteNotFoundError(ApiErrorBase):
    """Raised when request references missing HTTP endpoint routes."""
    pass

class ApiAuthenticationError(ApiErrorBase):
    """Raised when client API key or token verification fails."""
    pass

class ApiAuthorizationError(ApiErrorBase):
    """Raised when role permission limits block API operations."""
    pass

class VersionMismatchError(ApiErrorBase):
    """Raised when endpoint version header mismatches active policies."""
    pass

class InvalidRequestError(ApiErrorBase):
    """Raised when schema bounds or payload properties are invalid."""
    pass

class RateLimitExceededError(ApiErrorBase):
    """Raised when requests frequency exceeds throttling boundaries."""
    pass

class SerializationError(ApiErrorBase):
    """Raised when parsing or formatting output fails."""
    pass

class GatewayUnavailableError(ApiErrorBase):
    """Raised when internal subsystem dispatch gates are stopped."""
    pass
