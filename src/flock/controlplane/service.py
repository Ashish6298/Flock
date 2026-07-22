"""High-level ControlPlaneService orchestrating fleet enrollments, configurations sync, and governance."""

from __future__ import annotations

import time
import threading
from typing import Any, Dict, Optional

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.controlplane.coordinator import ControlPlaneCoordinator
from flock.controlplane.models import EnrolledCluster, GovernancePolicy

logger = structlog.get_logger()


class ControlPlaneService:
    """Coordinates fleet enrollment, global configuration propagation, and features sync on MessageBus."""

    def __init__(
        self,
        node_id: str,
        message_bus: MessageBus,
        event_bus: EventBus,
    ) -> None:
        self.node_id = node_id
        self._bus = message_bus
        self._events = event_bus
        self._lock = threading.RLock()

        self.coordinator = ControlPlaneCoordinator(node_id)
        self._running = False

    async def start(self) -> None:
        """Start the control plane service and register MessageBus query listeners."""
        with self._lock:
            if self._running:
                return
            self._running = True

        self._register_handlers()
        
        await self._events.publish(
            "controlplane.initialized",
            {
                "node_id": self.node_id,
                "timestamp": time.time(),
            }
        )
        logger.info("ControlPlaneService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop control plane operations."""
        with self._lock:
            if not self._running:
                return
            self._running = False

        await self._events.publish(
            "controlplane.service.synchronized",
            {
                "node_id": self.node_id,
                "timestamp": time.time(),
            }
        )
        logger.info("ControlPlaneService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register query verification endpoints on MessageBus."""
        router = self._bus.router

        async def handle_cluster_enrollment(context: Any) -> None:
            payload = context.payload or {}
            cluster_id = payload.get("cluster_id")
            fleet_id = payload.get("fleet_id")
            name = payload.get("name", "enrolled-cluster")
            version = payload.get("version", "0.0.1")
            labels = payload.get("labels", {})
            features = payload.get("features_active", [])
            
            reply_target = context.sender
            try:
                cluster = EnrolledCluster(
                    cluster_id=cluster_id or "",
                    fleet_id=fleet_id or "",
                    name=name,
                    version=version,
                    labels=labels,
                    features_active=features,
                    last_seen=time.time(),
                )
                self.coordinator.clusters.enroll_cluster(cluster)
                self.coordinator.inventory.index_cluster_labels(cluster.cluster_id, cluster.labels)
                
                await self._events.publish(
                    "cluster.enrolled",
                    {"cluster_id": cluster_id, "timestamp": time.time()}
                )
                
                # Check governance compliance
                compliant = self.coordinator.governance.evaluate_compliance(cluster.cluster_id, cluster.version)
                
                await self._bus.send(
                    reply_target,
                    MessageType.CONTROL_PLANE_HEALTH,
                    {"success": True, "compliant": compliant},
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.CONTROL_PLANE_HEALTH,
                    {"success": False, "error": str(exc)},
                )

        async def handle_governance_sync(context: Any) -> None:
            payload = context.payload or {}
            policy_data = payload.get("policy", {})
            
            reply_target = context.sender
            try:
                policy = GovernancePolicy(
                    policy_id=policy_data.get("policy_id", "default"),
                    rule_name=policy_data.get("rule_name", "rule"),
                    action_type=policy_data.get("action_type", "audit"),
                    parameters=policy_data.get("parameters", {}),
                )
                self.coordinator.governance.register_policy(policy)
                
                await self._events.publish(
                    "governance.policy.applied",
                    {"policy_id": policy.policy_id, "timestamp": time.time()}
                )
                
                await self._bus.send(
                    reply_target,
                    MessageType.CONTROL_PLANE_HEALTH,
                    {"success": True},
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.CONTROL_PLANE_HEALTH,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.CLUSTER_ENROLLMENT,
            _CpQueryHandler(handle_cluster_enrollment),
        )
        router.register(
            MessageType.GOVERNANCE_SYNC,
            _CpQueryHandler(handle_governance_sync),
        )


class _CpQueryHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
