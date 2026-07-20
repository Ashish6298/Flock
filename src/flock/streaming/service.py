"""High-level StreamingService coordinating publisher and subscriber engines."""

from __future__ import annotations

from typing import Any, Dict, Optional

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.storage.backend import StorageBackend
from flock.streaming.backpressure import BackpressureController
from flock.streaming.models import Topic
from flock.streaming.publisher import PublisherEngine
from flock.streaming.registry import TopicRegistry
from flock.streaming.storage import StreamStorage
from flock.streaming.subscriber import SubscriberEngine

logger = structlog.get_logger()


class StreamingService:
    """Wires registries, publishers, subscribers, rate controllers, and sync endpoints."""

    def __init__(
        self,
        node_id: str,
        storage_backend: StorageBackend,
        message_bus: MessageBus,
        event_bus: EventBus,
    ) -> None:
        self.node_id = node_id
        self._storage = storage_backend
        self._bus = message_bus
        self._events = event_bus

        # Setup subsystems
        self.registry = TopicRegistry()
        self.storage = StreamStorage(self._storage)
        self.publisher = PublisherEngine(self.registry, self.storage, self._events)
        self.subscriber = SubscriberEngine(self.storage, self._events)
        self.backpressure = BackpressureController()

        self._running = False

    async def start(self) -> None:
        """Start policy listeners and metrics query routes."""
        if self._running:
            return
        self._running = True

        self._register_handlers()
        logger.info("StreamingService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop streaming service operations."""
        self._running = False
        logger.info("StreamingService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register topic configuration query routes on message bus."""
        router = self._bus.router

        async def handle_topic_create(context: Any) -> None:
            payload = context.payload or {}
            top_id = payload.get("topic_id")
            name = payload.get("name")
            partitions = payload.get("partitions_count", 1)

            reply_target = context.sender
            try:
                # Add topic definition parameters to registry
                new_topic = Topic(
                    topic_id=str(top_id or ""),
                    name=str(name or ""),
                    partitions_count=int(partitions),
                )
                self.registry.create_topic(new_topic)

                await self._bus.send(
                    reply_target,
                    MessageType.EVENT_ACK,
                    {"success": True, "topic_id": top_id},
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.EVENT_ACK,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.TOPIC_CREATE,
            _TopicCreateHandler(handle_topic_create),
        )


class _TopicCreateHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
