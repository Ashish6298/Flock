"""Middleware execution definitions and execution pipeline structures."""

from typing import Protocol, Callable, Awaitable, Any
from flock.messaging.models import MessageContext

class Middleware(Protocol):
    """Protocol representing a single interceptor in the message processing chain."""

    async def __call__(
        self,
        context: MessageContext,
        next_call: Callable[[MessageContext], Awaitable[None]]
    ) -> None:
        """Process incoming/outgoing message frames inside context and propagate to next_call."""
        ...
