"""High-level PolicyService orchestrating policy compilation, evaluation, and synchronization."""

from __future__ import annotations

import time
import threading
from typing import Any, Dict, Optional, List

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.policy.coordinator import PolicyCoordinator
from flock.policy.models import PolicyDefinition

logger = structlog.get_logger()


class PolicyService:
    """Coordinates policy creation, evaluation queries, and compliance syncs on MessageBus."""

    def __init__(
        self,
        message_bus: MessageBus,
        event_bus: EventBus,
    ) -> None:
        self._bus = message_bus
        self._events = event_bus
        self._lock = threading.RLock()

        self.coordinator = PolicyCoordinator()
        self._running = False

    async def start(self) -> None:
        """Start the policy service and register MessageBus query listeners."""
        with self._lock:
            if self._running:
                return
            self._running = True

        self._register_handlers()
        
        await self._events.publish(
            "policy.initialized",
            {
                "timestamp": time.time(),
            }
        )
        logger.info("PolicyService started")

    async def stop(self) -> None:
        """Stop policy operations."""
        with self._lock:
            if not self._running:
                return
            self._running = False

        await self._events.publish(
            "policy.service.synchronized",
            {
                "timestamp": time.time(),
            }
        )
        logger.info("PolicyService stopped")

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register query verification endpoints on MessageBus."""
        router = self._bus.router

        async def handle_policy_create(context: Any) -> None:
            payload = context.payload or {}
            raw_payload = payload.get("raw_policy")
            
            reply_target = context.sender
            try:
                # 1. Compile policy
                policy = self.coordinator.compiler.compile_policy(raw_payload or "")
                
                # 2. Save in repository
                self.coordinator.repository.store_policy(policy)
                
                await self._events.publish(
                    "policy.created",
                    {"policy_id": policy.policy_id, "timestamp": time.time()}
                )
                
                await self._bus.send(
                    reply_target,
                    MessageType.POLICY_HEALTH_REPORT,
                    {"success": True, "policy_id": policy.policy_id},
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.POLICY_HEALTH_REPORT,
                    {"success": False, "error": str(exc)},
                )

        async def handle_policy_evaluation(context: Any) -> None:
            payload = context.payload or {}
            policy_id = payload.get("policy_id")
            attributes = payload.get("attributes", {})
            
            reply_target = context.sender
            try:
                policy = self.coordinator.repository.get_policy(policy_id or "")
                results = self.coordinator.engine.evaluate_policy_rules(policy, attributes)
                
                # Check overall pass status
                all_passed = all(status for _, status, _ in results)
                self.coordinator.metrics.record_evaluation(all_passed)
                
                await self._events.publish(
                    "policy.evaluated",
                    {"policy_id": policy_id, "passed": all_passed, "timestamp": time.time()}
                )
                
                serialized_results = []
                for rule, status, rem in results:
                    serialized_results.append({
                        "rule_name": rule.name,
                        "passed": status,
                        "remediation": rem
                    })
                    
                await self._bus.send(
                    reply_target,
                    MessageType.POLICY_HEALTH_REPORT,
                    {"success": True, "passed": all_passed, "results": serialized_results},
                )
            except Exception as exc:
                self.coordinator.metrics.record_failure()
                await self._bus.send(
                    reply_target,
                    MessageType.POLICY_HEALTH_REPORT,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.POLICY_CREATE,
            _PolicyQueryHandler(handle_policy_create),
        )
        router.register(
            MessageType.POLICY_EVALUATION_REQUEST,
            _PolicyQueryHandler(handle_policy_evaluation),
        )


class _PolicyQueryHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
