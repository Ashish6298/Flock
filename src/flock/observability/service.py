"""ObservabilityService orchestrating metrics, tracing, and health checks."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.observability.aggregator import TelemetryAggregator
from flock.observability.exporter import TelemetryExporter
from flock.observability.health import HealthMonitor
from flock.observability.registry import MetricsRegistry
from flock.observability.tracing import TracingEngine

logger = structlog.get_logger()


class ObservabilityService:
    """Combines metrics registry, tracing engine, health monitor, and network queries."""

    def __init__(
        self,
        node_id: str,
        message_bus: MessageBus,
        event_bus: EventBus,
    ) -> None:
        self.node_id = node_id
        self._bus = message_bus
        self._events = event_bus

        self.registry = MetricsRegistry()
        self.aggregator = TelemetryAggregator(self.registry, self._events)
        self.tracing = TracingEngine(self._events)
        self.health_monitor = HealthMonitor(node_id, self.registry, self._events)
        self.exporter = TelemetryExporter()

        self._running = False

    async def start(self) -> None:
        """Start aggregator registration hooks and query listeners."""
        if self._running:
            return
        self._running = True

        # Activate aggregator hooks
        self.aggregator.start()

        # Wire handlers
        self._register_handlers()
        logger.info("ObservabilityService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop ObservabilityService loops."""
        self._running = False
        logger.info("ObservabilityService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register metric retrieval query endpoints."""
        router = self._bus.router

        async def handle_metrics_request(context: Any) -> None:
            metrics = self.registry.list_metrics()
            serialized = [m.model_dump() for m in metrics]
            reply_target = context.sender
            await self._bus.send(
                reply_target,
                MessageType.METRICS_RESPONSE,
                {"metrics": serialized},
            )

        router.register(
            MessageType.METRICS_REQUEST,
            _MetricsQueryHandler(handle_metrics_request),
        )


class _MetricsQueryHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
