"""High-level MeshService orchestrating Service Mesh networking."""

from __future__ import annotations

from typing import Any, Dict, Optional

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.mesh.breaker import CircuitBreakerEngine
from flock.mesh.balancer import LoadBalancingEngine
from flock.mesh.models import MeshService
from flock.mesh.registry import ServiceRegistry
from flock.mesh.router import TrafficRouter

logger = structlog.get_logger()


class MeshServiceEngine:
    """Wires registries, load balancers, traffic routers, and discovery endpoints."""

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
        self.registry = ServiceRegistry()
        self.router = TrafficRouter()
        self.breaker = CircuitBreakerEngine()
        self.balancer = LoadBalancingEngine()

        self._running = False

    async def start(self) -> None:
        """Start policy listeners and metrics query routes."""
        if self._running:
            return
        self._running = True

        self._register_handlers()
        logger.info("MeshService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop mesh operations."""
        self._running = False
        logger.info("MeshService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register discovery sync endpoints on message bus."""
        router = self._bus.router

        async def handle_service_register(context: Any) -> None:
            payload = context.payload or {}
            srv_id = payload.get("service_id")
            name = payload.get("name")

            reply_target = context.sender
            try:
                new_service = MeshService(
                    service_id=str(srv_id or ""),
                    name=str(name or ""),
                    endpoints=[],
                )
                self.registry.register_service(new_service)

                await self._bus.send(
                    reply_target,
                    MessageType.SERVICE_DISCOVERY_RESPONSE,
                    {"success": True, "service_id": srv_id},
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.SERVICE_DISCOVERY_RESPONSE,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.SERVICE_REGISTER,
            _ServiceRegisterHandler(handle_service_register),
        )


class _ServiceRegisterHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
