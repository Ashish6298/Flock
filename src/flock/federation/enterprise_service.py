"""High-level EnterpriseFederationService coordinating cross-region workloads and secure handshakes."""

from __future__ import annotations

import time
import threading
from typing import Any, Dict, Optional

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.security.encryption import CryptographyEngine
from flock.federation.models import FederationCluster, FederationPolicy
from flock.federation.coordinator import FederationCoordinator

logger = structlog.get_logger()


class EnterpriseFederationService:
    """Manages secure cross-cluster topology exchanges, routing policy sync, and federation metrics reports."""

    def __init__(
        self,
        local_cluster_id: str,
        crypto: CryptographyEngine,
        message_bus: MessageBus,
        event_bus: EventBus,
    ) -> None:
        self.local_cluster_id = local_cluster_id
        self._bus = message_bus
        self._events = event_bus
        self._lock = threading.RLock()

        self.coordinator = FederationCoordinator(local_cluster_id, crypto)
        self._running = False

    async def start(self) -> None:
        """Start the federation service and register MessageBus query listeners."""
        with self._lock:
            if self._running:
                return
            self._running = True

        self._register_handlers()
        
        await self._events.publish(
            "federation.initialized",
            {
                "local_cluster_id": self.local_cluster_id,
                "timestamp": time.time(),
            }
        )
        logger.info("EnterpriseFederationService started", local_cluster_id=self.local_cluster_id)

    async def stop(self) -> None:
        """Stop federation operations."""
        with self._lock:
            if not self._running:
                return
            self._running = False

        await self._events.publish(
            "federation.service.synchronized",
            {
                "local_cluster_id": self.local_cluster_id,
                "timestamp": time.time(),
            }
        )
        logger.info("EnterpriseFederationService stopped", local_cluster_id=self.local_cluster_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register query verification endpoints on MessageBus."""
        router = self._bus.router

        async def handle_federation_join_request(context: Any) -> None:
            payload = context.payload or {}
            remote_id = payload.get("cluster_id")
            sig = payload.get("signature")
            cert = payload.get("certificate_pem")
            
            reply_target = context.sender
            try:
                # 1. Establish trust relationship
                trust = self.coordinator.handshake.verify_handshake_response(
                    remote_cluster_id=remote_id or "",
                    signature=sig or "",
                    certificate_pem=cert or "",
                )
                self.coordinator.trust.register_trust(trust)
                
                # 2. Register cluster
                cluster = FederationCluster(
                    cluster_id=remote_id or "",
                    name=payload.get("name", "remote-cluster"),
                    endpoints=payload.get("endpoints", []),
                    is_healthy=True,
                    capacity_score=float(payload.get("capacity_score", 1.0)),
                )
                self.coordinator.registry.register_cluster(cluster)
                self.coordinator.topology.register_cluster(cluster)
                self.coordinator.health.set_cluster_health(cluster.cluster_id, True)
                
                await self._events.publish(
                    "federation.cluster.joined",
                    {"cluster_id": remote_id, "timestamp": time.time()}
                )
                
                await self._bus.send(
                    reply_target,
                    MessageType.FEDERATION_HEALTH_REPORT,
                    {"success": True, "trust_signature": trust.signature},
                )
            except Exception as exc:
                await self._events.publish(
                    "federation.remote.execution.failed",
                    {"error": str(exc), "timestamp": time.time()}
                )
                await self._bus.send(
                    reply_target,
                    MessageType.FEDERATION_HEALTH_REPORT,
                    {"success": False, "error": str(exc)},
                )

        async def handle_policy_sync(context: Any) -> None:
            payload = context.payload or {}
            policy_data = payload.get("policy", {})
            
            reply_target = context.sender
            try:
                policy = FederationPolicy(
                    policy_id=policy_data.get("policy_id", "default"),
                    target_clusters=policy_data.get("target_clusters", []),
                    allowed_actions=policy_data.get("allowed_actions", []),
                    max_cross_region_latency_ms=float(policy_data.get("max_cross_region_latency_ms", 300.0)),
                )
                self.coordinator.policy.register_policy(policy)
                
                await self._events.publish(
                    "federation.policy.synchronized",
                    {"policy_id": policy.policy_id, "timestamp": time.time()}
                )
                
                await self._bus.send(
                    reply_target,
                    MessageType.FEDERATION_HEALTH_REPORT,
                    {"success": True},
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.FEDERATION_HEALTH_REPORT,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.FEDERATION_JOIN,
            _FedQueryHandler(handle_federation_join_request),
        )
        router.register(
            MessageType.FEDERATION_POLICY_SYNC,
            _FedQueryHandler(handle_policy_sync),
        )


class _FedQueryHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
