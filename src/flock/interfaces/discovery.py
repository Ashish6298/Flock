"""Discovery interface protocol."""

from typing import Protocol, Set, Callable, Awaitable
from flock.types import NodeInfo

class Discovery(Protocol):
    """Protocol for handling node auto-discovery in a decentralized cluster."""

    async def start(self) -> None:
        """Start the discovery service (e.g. broadcasting, querying peers)."""
        ...

    async def stop(self) -> None:
        """Stop the discovery service."""
        ...

    async def get_peers(self) -> Set[NodeInfo]:
        """Retrieve the current set of discovered active peers."""
        ...

    def register_join_handler(self, handler: Callable[[NodeInfo], Awaitable[None]]) -> None:
        """Register callback for when a new node is discovered."""
        ...

    def register_leave_handler(self, handler: Callable[[NodeInfo], Awaitable[None]]) -> None:
        """Register callback for when a node leaves or is considered dead."""
        ...
