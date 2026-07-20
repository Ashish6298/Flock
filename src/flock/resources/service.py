"""High-level ResourceManagementService coordinating allocations and balancing."""

from __future__ import annotations

from typing import Any, Dict, Optional

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.resources.admission import AdmissionController
from flock.resources.allocator import ResourceAllocator
from flock.resources.balancer import ResourceBalancer
from flock.resources.capacity import CapacityPlanner
from flock.resources.loadbalancer import LeastUtilizedStrategy, LoadBalancingEngine
from flock.resources.registry import ResourceRegistry

logger = structlog.get_logger()


class ResourceManagementService:
    """Combines resource registry, allocator, balancer, and network handles."""

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
        self.registry = ResourceRegistry()
        self.allocator = ResourceAllocator(self.registry)
        self.load_balancer = LoadBalancingEngine(LeastUtilizedStrategy())
        self.capacity_planner = CapacityPlanner()
        self.admission_controller = AdmissionController()
        self.balancer = ResourceBalancer()

        self._running = False

    async def start(self) -> None:
        """Start resource registry endpoints and listeners."""
        if self._running:
            return
        self._running = True

        self._register_handlers()
        logger.info("ResourceManagementService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop resource service registry endpoints."""
        self._running = False
        logger.info("ResourceManagementService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register allocation query routes on message bus."""
        router = self._bus.router

        async def handle_allocation_query(context: Any) -> None:
            payload = context.payload or {}
            req_id = payload.get("request_id")
            req_res = payload.get("resources", {})

            reply_target = context.sender
            try:
                # Execute allocation booking
                res = self.allocator.allocate(str(req_id or ""), req_res)
                
                await self._bus.send(
                    reply_target,
                    MessageType.ALLOCATION_RESPONSE,
                    res.model_dump(),
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.ALLOCATION_RESPONSE,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.ALLOCATION_REQUEST,
            _AllocQueryHandler(handle_allocation_query),
        )


class _AllocQueryHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
