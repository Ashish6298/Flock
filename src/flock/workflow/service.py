"""High-level WorkflowService coordinating submissions and handshakes."""

from __future__ import annotations

from typing import Any, Dict, Optional

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.storage.backend import StorageBackend
from flock.workflow.checkpoint import WorkflowCheckpointManager
from flock.workflow.executor import WorkflowExecutor
from flock.workflow.graph import WorkflowGraphEngine
from flock.workflow.models import WorkflowDefinition
from flock.workflow.planner import WorkflowPlanner

logger = structlog.get_logger()


class WorkflowService:
    """Consolidates schedulers, planners, execution stages, and network routes."""

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
        self.graph_engine = WorkflowGraphEngine()
        self.planner = WorkflowPlanner(self.graph_engine)
        self.checkpoint_manager = WorkflowCheckpointManager(self._storage)
        self.executor = WorkflowExecutor(self._events, self.checkpoint_manager)

        self._running = False

    async def start(self) -> None:
        """Start policy listeners and metrics query routes."""
        if self._running:
            return
        self._running = True

        self._register_handlers()
        logger.info("WorkflowService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop workflow service operations."""
        self._running = False
        logger.info("WorkflowService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register workflow sync endpoints on message bus."""
        router = self._bus.router

        async def handle_workflow_submit(context: Any) -> None:
            payload = context.payload or {}
            wf_id = payload.get("workflow_id")

            reply_target = context.sender
            try:
                # Dispatched handshake validation
                await self._bus.send(
                    reply_target,
                    MessageType.WORKFLOW_ACCEPTED,
                    {"success": True, "workflow_id": wf_id},
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.WORKFLOW_ACCEPTED,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.WORKFLOW_SUBMIT,
            _WfSubmitHandler(handle_workflow_submit),
        )


class _WfSubmitHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
