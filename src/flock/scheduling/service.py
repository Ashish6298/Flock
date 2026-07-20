"""High-level SchedulingService coordinating client requests."""

from __future__ import annotations

from typing import Any, Dict, Optional

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.scheduling.cron import CronEngine
from flock.scheduling.models import ScheduleDefinition
from flock.scheduling.registry import ScheduleRegistry
from flock.scheduling.scheduler import SchedulingEngine
from flock.scheduling.trigger import EventTriggerEngine

logger = structlog.get_logger()


class SchedulingService:
    """Wires scheduler registers, cron parsers, trigger events, and messaging loops."""

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
        self.registry = ScheduleRegistry()
        self.cron = CronEngine()
        self.trigger = EventTriggerEngine(self._events)
        self.engine = SchedulingEngine(self._events)

        self._running = False

    async def start(self) -> None:
        """Start policy listeners and metrics query routes."""
        if self._running:
            return
        self._running = True

        self._register_handlers()
        logger.info("SchedulingService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop scheduler service operations."""
        self._running = False
        logger.info("SchedulingService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register scheduler synchronization endpoints on message bus."""
        router = self._bus.router

        async def handle_schedule_create(context: Any) -> None:
            payload = context.payload or {}
            sch_id = payload.get("schedule_id")
            cron_expr = payload.get("cron_expression")

            reply_target = context.sender
            try:
                # Add schedule properties to registry
                new_sch = ScheduleDefinition(
                    schedule_id=str(sch_id or ""),
                    cron_expression=str(cron_expr or ""),
                    task_payload=b"",
                )
                self.registry.add_schedule(new_sch)

                await self._bus.send(
                    reply_target,
                    MessageType.SCHEDULE_EXECUTION_START,
                    {"success": True, "schedule_id": sch_id},
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.SCHEDULE_EXECUTION_START,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.SCHEDULE_CREATE,
            _SchCreateHandler(handle_schedule_create),
        )


class _SchCreateHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
