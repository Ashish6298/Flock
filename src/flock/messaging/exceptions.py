"""Custom exceptions for the messaging subsystem."""

from flock.exceptions import FlockError

class MessagingError(FlockError):
    """Base exception for all messaging framework operations."""
    pass

class RoutingError(MessagingError):
    """Raised when a message cannot be routed to a registered handler."""
    pass

class MiddlewareError(MessagingError):
    """Raised when a middleware execution fails or aborts the request pipeline."""
    pass

class HandlerError(MessagingError):
    """Raised when a message handler raises an exception during execution."""
    pass

class TimeoutError(MessagingError):
    """Raised when a request-response transaction times out."""
    pass

class RequestCorrelationError(MessagingError):
    """Raised when a response cannot be matched to an active tracking request ID."""
    pass
