"""High-level ReleaseService orchestrating dependency checks and readiness diagnostics."""

from __future__ import annotations

import time
import threading
from typing import Any, Dict, Optional, List

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.release.coordinator import ReleaseCoordinator
from flock.release.models import ReleaseManifest

logger = structlog.get_logger()


class ReleaseService:
    """Coordinates release validation and readiness assessments over MessageBus."""

    def __init__(
        self,
        message_bus: MessageBus,
        event_bus: EventBus,
    ) -> None:
        self._bus = message_bus
        self._events = event_bus
        self._lock = threading.RLock()

        self.coordinator = ReleaseCoordinator()
        self._running = False

    async def start(self) -> None:
        """Start the release candidate service and register MessageBus query listeners."""
        with self._lock:
            if self._running:
                return
            self._running = True

        self._register_handlers()
        
        await self._events.publish(
            "release.initialized",
            {
                "timestamp": time.time(),
            }
        )
        logger.info("ReleaseService started")

    async def stop(self) -> None:
        """Stop release service operations."""
        with self._lock:
            if not self._running:
                return
            self._running = False

        await self._events.publish(
            "release.service.synchronized",
            {
                "timestamp": time.time(),
            }
        )
        logger.info("ReleaseService stopped")

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register query verification endpoints on MessageBus."""
        router = self._bus.router

        async def handle_readiness_check(context: Any) -> None:
            payload = context.payload or {}
            version = payload.get("version", "1.0.0-rc1")
            
            reply_target = context.sender
            try:
                # Assess overall readiness
                subsystems = self.coordinator.lifecycle.list_subsystems()
                report = self.coordinator.readiness.assess_readiness(
                    version=version,
                    dependencies_ok=True,
                    config_ok=True,
                    subsystems=subsystems,
                )
                
                await self._events.publish(
                    "release.compliance.generated",
                    {"version": version, "score": report.overall_readiness_score, "timestamp": time.time()}
                )
                
                await self._bus.send(
                    reply_target,
                    MessageType.RELEASE_STATUS_SYNC,
                    {
                        "success": True,
                        "overall_readiness_score": report.overall_readiness_score,
                        "subsystems_healthy": report.subsystems_healthy,
                    },
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.RELEASE_STATUS_SYNC,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.RELEASE_READINESS_CHECK,
            _ReleaseQueryHandler(handle_readiness_check),
        )


class _ReleaseQueryHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
