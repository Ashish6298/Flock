"""Routing table mapping incoming message type specifiers to registered actions."""

import structlog
from typing import Dict, Optional
from flock.messaging.handlers import MessageHandler
from flock.messaging.exceptions import RoutingError

logger = structlog.get_logger()

class MessageRouter:
    """Registry routing message type IDs directly to distinct handler implementations."""

    def __init__(self) -> None:
        self._routes: Dict[int, MessageHandler] = {}
        self._fallback_handler: Optional[MessageHandler] = None

    def register(self, message_type: int, handler: MessageHandler) -> None:
        """Register a message handler for a specific message type."""
        if message_type in self._routes:
            logger.warn("Overwriting registered message type route", type_id=message_type)
        self._routes[message_type] = handler

    def unregister(self, message_type: int) -> None:
        """Remove route mapping from registry."""
        self._routes.pop(message_type, None)

    def set_fallback(self, handler: MessageHandler) -> None:
        """Define a fallback handler for unregistered message types."""
        self._fallback_handler = handler

    def get_handler(self, message_type: int) -> MessageHandler:
        """Resolve message handler or fallback.

        Raises:
            RoutingError: If message type is unregistered and no fallback exists.
        """
        handler = self._routes.get(message_type)
        if handler:
            return handler
        if self._fallback_handler:
            return self._fallback_handler
        raise RoutingError(f"No handler registered for message type: {message_type}")
