"""OrchestratorService orchestrating policies, scheduling, and autoscaling."""

from __future__ import annotations

from typing import Any, Dict, Optional

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.orchestrator.autoscaler import AutoScaler
from flock.orchestrator.models import ClusterPolicy
from flock.orchestrator.optimizer import OptimizationEngine
from flock.orchestrator.policy import PolicyEngine
from flock.orchestrator.scheduler import AutonomousScheduler

logger = structlog.get_logger()


class OrchestratorService:
    """Consolidates policies, schedules, optimization engines, and network hooks."""

    def __init__(
        self,
        node_id: str,
        message_bus: MessageBus,
        event_bus: EventBus,
        default_policy: ClusterPolicy,
    ) -> None:
        self.node_id = node_id
        self._bus = message_bus
        self._events = event_bus

        # Setup subsystems
        self.policy = PolicyEngine(default_policy)
        self.scheduler = AutonomousScheduler(self._events)
        self.optimizer = OptimizationEngine()
        self.autoscaler = AutoScaler()

        self._running = False

    async def start(self) -> None:
        """Start policy listeners and metrics query routes."""
        if self._running:
            return
        self._running = True

        self._register_handlers()
        logger.info("OrchestratorService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop orchestration controllers."""
        self._running = False
        logger.info("OrchestratorService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register orchestrator synchronization routes."""
        router = self._bus.router

        async def handle_policy_sync(context: Any) -> None:
            payload = context.payload or {}
            pol_id = payload.get("policy_id")
            strat = payload.get("strategy_name")
            target = payload.get("target_utilization", 70.0)

            reply_target = context.sender
            try:
                # Update Policy Engine
                new_policy = ClusterPolicy(
                    policy_id=str(pol_id or ""),
                    strategy_name=str(strat or ""),
                    target_utilization=float(target),
                )
                self.policy.update_policy(new_policy)

                await self._bus.send(
                    reply_target,
                    MessageType.ORCHESTRATOR_POLICY_ACK,
                    {"success": True, "policy_id": pol_id},
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.ORCHESTRATOR_POLICY_ACK,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.ORCHESTRATOR_POLICY_SYNC,
            _PolicySyncHandler(handle_policy_sync),
        )


class _PolicySyncHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
