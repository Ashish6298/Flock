"""Abstract handler definitions for resolving network actions."""

from abc import ABC, abstractmethod
from flock.messaging.models import MessageContext

class MessageHandler(ABC):
    """Abstract Base Class for defining network action handlers in the Flock cluster."""

    @abstractmethod
    async def handle(self, context: MessageContext) -> None:
        """Handle incoming routed message. Mutate context to set response payload."""
        pass
