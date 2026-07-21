"""High-level FunctionService exposing serverless routes."""

from __future__ import annotations

from typing import Any, Dict, Optional

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.functions.invocation import InvocationEngine
from flock.functions.models import FunctionDefinition, InvocationRequest
from flock.functions.registry import FunctionRegistry
from flock.functions.runtime import RuntimeEngine

logger = structlog.get_logger()


class FunctionService:
    """Wires registries, code executors, triggers, and endpoints."""

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
        self.registry = FunctionRegistry()
        self.runtime = RuntimeEngine()
        self.invoker = InvocationEngine(self.registry, self.runtime)

        self._running = False

    async def start(self) -> None:
        """Start policy listeners and metrics query routes."""
        if self._running:
            return
        self._running = True

        self._register_handlers()
        logger.info("FunctionService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop function operations."""
        self._running = False
        logger.info("FunctionService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register function sync handlers on message bus."""
        router = self._bus.router

        async def handle_function_register(context: Any) -> None:
            payload = context.payload or {}
            func_id = payload.get("function_id")
            name = payload.get("name")
            code = payload.get("handler_code")

            reply_target = context.sender
            try:
                new_func = FunctionDefinition(
                    function_id=str(func_id or ""),
                    name=str(name or ""),
                    handler_code=str(code or ""),
                )
                self.registry.register_function(new_func)

                await self._bus.send(
                    reply_target,
                    MessageType.FUNCTION_RESULT,
                    {"success": True, "function_id": func_id},
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.FUNCTION_RESULT,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.FUNCTION_REGISTER,
            _FunctionRegisterHandler(handle_function_register),
        )


class _FunctionRegisterHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
