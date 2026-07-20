"""High-level FederationService coordinating cluster connections."""

from __future__ import annotations

from typing import Any, Dict, Optional

import structlog

from flock.events.bus import EventBus
from flock.federation.models import FederationCluster
from flock.federation.registry import FederationRegistry
from flock.federation.replication import CrossClusterReplicationEngine
from flock.federation.routing import GlobalRoutingEngine
from flock.federation.scheduler import GlobalScheduler
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType

logger = structlog.get_logger()


class FederationService:
    """Combines registries, schedulers, and network endpoints."""

    def __init__(
        self,
        local_cluster_id: str,
        message_bus: MessageBus,
        event_bus: EventBus,
    ) -> None:
        self.local_cluster_id = local_cluster_id
        self._bus = message_bus
        self._events = event_bus

        # Setup subsystems
        self.registry = FederationRegistry()
        self.routing_engine = GlobalRoutingEngine()
        self.scheduler = GlobalScheduler(self._events)
        self.replicator = CrossClusterReplicationEngine(self._events)

        self._running = False

    async def start(self) -> None:
        """Start policy listeners and metrics query routes."""
        if self._running:
            return
        self._running = True

        self._register_handlers()
        logger.info("FederationService started", local_cluster_id=self.local_cluster_id)

    async def stop(self) -> None:
        """Stop federation service operations."""
        self._running = False
        logger.info("FederationService stopped", local_cluster_id=self.local_cluster_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register federation join query routes on message bus."""
        router = self._bus.router

        async def handle_federation_join(context: Any) -> None:
            payload = context.payload or {}
            cluster_id = payload.get("cluster_id")
            name = payload.get("name")
            endpoints = payload.get("endpoints", [])
            capacity = payload.get("capacity_score", 1.0)

            reply_target = context.sender
            try:
                # Add cluster to registry catalog
                new_cluster = FederationCluster(
                    cluster_id=str(cluster_id or ""),
                    name=str(name or ""),
                    endpoints=list(endpoints),
                    is_healthy=True,
                    capacity_score=float(capacity),
                )
                self.registry.register_cluster(new_cluster)

                await self._bus.send(
                    reply_target,
                    MessageType.FEDERATION_JOIN_RESPONSE,
                    {"success": True, "local_cluster_id": self.local_cluster_id},
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.FEDERATION_JOIN_RESPONSE,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.FEDERATION_JOIN_REQUEST,
            _FedJoinHandler(handle_federation_join),
        )


class _FedJoinHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
