"""Tests for MessageRouter routing and dynamic lookup."""

import pytest
from flock.messaging.router import MessageRouter
from flock.messaging.handlers import MessageHandler
from flock.messaging.models import MessageContext
from flock.messaging.exceptions import RoutingError

class SimpleHandler(MessageHandler):
    async def handle(self, context: MessageContext) -> None:
        context.response_payload = "handled"

def test_router_registration() -> None:
    router = MessageRouter()
    handler = SimpleHandler()
    
    router.register(10, handler)
    assert router.get_handler(10) == handler
    
    router.unregister(10)
    with pytest.raises(RoutingError):
        router.get_handler(10)

def test_router_fallback() -> None:
    router = MessageRouter()
    fallback = SimpleHandler()
    
    router.set_fallback(fallback)
    assert router.get_handler(999) == fallback
