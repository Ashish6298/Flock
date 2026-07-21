"""High-level ApiService exposing API endpoints and handshakes."""

from __future__ import annotations

from typing import Any, Dict, Optional

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.api.gateway import ApiGateway
from flock.api.models import ApiRoute
from flock.api.router import ApiRouter
from flock.api.serializer import ResponseSerializer
from flock.api.validator import RequestValidator

logger = structlog.get_logger()


class ApiService:
    """Wires routers, validators, rate gateways, and messaging adapters."""

    def __init__(
        self,
        node_id: str,
        message_bus: MessageBus,
        event_bus: EventBus,
    ) -> None:
        self.node_id = node_id
        self._bus = message_bus
        self._events = event_bus

        # Setup subsystems
        self.router = ApiRouter()
        self.validator = RequestValidator()
        self.serializer = ResponseSerializer()
        self.gateway = ApiGateway()

        self._running = False

    async def start(self) -> None:
        """Start policy listeners and metrics query routes."""
        if self._running:
            return
        self._running = True

        self._register_handlers()
        logger.info("ApiService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop API gateway operations."""
        self._running = False
        logger.info("ApiService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register API request endpoints on message bus."""
        router = self._bus.router

        async def handle_api_request(context: Any) -> None:
            payload = context.payload or {}
            req_id = payload.get("request_id")
            path = payload.get("path")
            method = payload.get("method")

            reply_target = context.sender
            try:
                # Dispatch query response back to sender
                await self._bus.send(
                    reply_target,
                    MessageType.API_RESPONSE,
                    {"success": True, "request_id": req_id, "path": path, "method": method},
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.API_RESPONSE,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.API_REQUEST,
            _ApiRequestHandler(handle_api_request),
        )


class _ApiRequestHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
