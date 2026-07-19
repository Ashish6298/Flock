import pytest
from typing import List, Callable, Awaitable, Any
from flock.messaging.models import MessageContext, MessageMetadata
from flock.messaging.middleware import Middleware
from flock.messaging.bus import MessageBus
from flock.serialization.json import JsonSerializer
from flock.types import NodeInfo

class MockTransport:
    async def start(self) -> None: pass
    async def stop(self) -> None: pass
    async def send(self, target: NodeInfo, message: Any) -> None: pass
    def register_handler(self, handler: Callable[[NodeInfo, Any], Awaitable[None]]) -> None:
        self.handler = handler

@pytest.mark.asyncio
async def test_middleware_execution_order() -> None:
    transport = MockTransport()
    serializer = JsonSerializer()
    bus = MessageBus(transport, serializer)

    execution_trail: List[str] = []

    class TrailMiddleware(Middleware):
        def __init__(self, name: str) -> None:
            self.name = name
        async def __call__(
            self,
            context: MessageContext,
            next_call: Callable[[MessageContext], Awaitable[None]]
        ) -> None:
            execution_trail.append(f"pre-{self.name}")
            await next_call(context)
            execution_trail.append(f"post-{self.name}")

    bus.add_middleware(TrailMiddleware("one"))
    bus.add_middleware(TrailMiddleware("two"))

    # Mock inbound packet to trigger handler pipeline
    envelope = {
        "metadata": {
            "message_id": "test-123",
        },
        "body": "hello"
    }
    raw_payload = serializer.serialize(envelope)
    from flock.protocol.packet import Packet
    # Create packet wrapper containing the message type (1)
    packet = Packet(message_type=1, payload=raw_payload)
    raw_frame = packet.pack()

    # Route logic uses custom handler mock inside router
    from flock.messaging.handlers import MessageHandler
    class HandlerMock(MessageHandler):
        async def handle(self, context: MessageContext) -> None:
            execution_trail.append("handler")

    bus.router.register(1, HandlerMock())
    
    sender = NodeInfo(node_id="peer-1", host="127.0.0.1", port=9000)
    await transport.handler(sender, raw_frame)

    assert execution_trail == ["pre-one", "pre-two", "handler", "post-two", "post-one"]
