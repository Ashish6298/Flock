"""Streaming Exceptions."""

from flock.exceptions import FlockError

class StreamingError(FlockError):
    """Base exception for all streaming operations."""
    pass

class TopicNotFoundError(StreamingError):
    """Raised when request references missing topics."""
    pass

class DuplicateSubscriptionError(StreamingError):
    """Raised when client is already subscribed to topic."""
    pass

class ConsumerGroupError(StreamingError):
    """Raised when consumer group rebalancing or lease validation fails."""
    pass

class OffsetOutOfRangeError(StreamingError):
    """Raised when requested read offset exceeds partition boundaries."""
    pass

class BackpressureLimitExceededError(StreamingError):
    """Raised when target message rates exceed controller limits."""
    pass

class MessageOrderingError(StreamingError):
    """Raised when partition sequencing violates strictly monotonic sequences."""
    pass
