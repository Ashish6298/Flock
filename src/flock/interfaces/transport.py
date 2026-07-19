"""Transport interface protocol."""

from typing import Protocol, Any, Callable, Awaitable
from flock.types import NodeInfo

class Transport(Protocol):
    """Protocol defining network transport interactions."""

    async def start(self) -> None:
        """Start listening/accepting connections on the configured address."""
        ...

    async def stop(self) -> None:
        """Stop the transport and close all open sockets/connections."""
        ...

    async def send(self, target: NodeInfo, message: Any) -> None:
        """Send a message asynchronously to a target NodeInfo.

        Raises:
            TransportError: If sending the message fails.
        """
        ...

    def register_handler(self, handler: Callable[[NodeInfo, Any], Awaitable[None]]) -> None:
        """Register a callback for incoming messages."""
        ...
