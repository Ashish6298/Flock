"""High-level DeploymentService exposing orchestration routes."""

from __future__ import annotations

from typing import Any, Dict, Optional

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.deployment.controller import DeploymentController
from flock.deployment.models import DeploymentDefinition
from flock.deployment.registry import DeploymentRegistry

logger = structlog.get_logger()


class DeploymentService:
    """Wires controllers, registry records, and network listeners."""

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
        self.registry = DeploymentRegistry()
        self.controller = DeploymentController(self.registry, self._events)

        self._running = False

    async def start(self) -> None:
        """Start policy listeners and metrics query routes."""
        if self._running:
            return
        self._running = True

        self._register_handlers()
        logger.info("DeploymentService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop deployment operations."""
        self._running = False
        logger.info("DeploymentService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register deployment query sync routes on message bus."""
        router = self._bus.router

        async def handle_deployment_create(context: Any) -> None:
            payload = context.payload or {}
            dep_id = payload.get("deployment_id")
            name = payload.get("name")
            image = payload.get("image")

            reply_target = context.sender
            try:
                new_dep = DeploymentDefinition(
                    deployment_id=str(dep_id or ""),
                    name=str(name or ""),
                    image=str(image or ""),
                    replicas=1,
                )
                await self.controller.execute_rolling_update(new_dep)

                await self._bus.send(
                    reply_target,
                    MessageType.DEPLOYMENT_STATUS,
                    {"success": True, "deployment_id": dep_id},
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.DEPLOYMENT_STATUS,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.DEPLOYMENT_CREATE,
            _DeploymentCreateHandler(handle_deployment_create),
        )


class _DeploymentCreateHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
