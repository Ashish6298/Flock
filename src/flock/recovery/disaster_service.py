"""High-level disaster recovery service exposing backup, snapshot, and failover coordination APIs."""

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
from flock.recovery.coordinator import RecoveryCoordinator
from flock.recovery.models import RetentionPolicy

logger = structlog.get_logger()


class DisasterRecoveryService:
    """Coordinates cluster failovers, backup requests, snapshot creation, and restoration tasks on MessageBus."""

    def __init__(
        self,
        node_id: str,
        crypto: CryptographyEngine,
        message_bus: MessageBus,
        event_bus: EventBus,
    ) -> None:
        self.node_id = node_id
        self._bus = message_bus
        self._events = event_bus
        self._lock = threading.RLock()

        self.coordinator = RecoveryCoordinator(node_id, crypto)
        self._running = False

    async def start(self) -> None:
        """Start the recovery service and register message handlers."""
        with self._lock:
            if self._running:
                return
            self._running = True

        self._register_handlers()
        
        await self._events.publish(
            "recovery.initialized",
            {
                "node_id": self.node_id,
                "timestamp": time.time(),
            }
        )
        logger.info("DisasterRecoveryService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop recovery operations."""
        with self._lock:
            if not self._running:
                return
            self._running = False

        await self._events.publish(
            "recovery.service.synchronized",
            {
                "node_id": self.node_id,
                "timestamp": time.time(),
            }
        )
        logger.info("DisasterRecoveryService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register query verification endpoints on MessageBus."""
        router = self._bus.router

        async def handle_backup_request(context: Any) -> None:
            payload = context.payload or {}
            state_data = payload.get("state_data", {})
            policy_data = payload.get("policy", {})
            
            reply_target = context.sender
            try:
                # Register policy if provided in payload
                policy_id = "default"
                if policy_data:
                    policy_id = policy_data.get("policy_id", "default")
                    policy = RetentionPolicy(
                        policy_id=policy_id,
                        max_backups_retained=policy_data.get("max_backups_retained", 10),
                        ttl_seconds=policy_data.get("ttl_seconds", 86400.0),
                        archive_on_eviction=policy_data.get("archive_on_eviction", False),
                    )
                    self.coordinator.policy.register_policy(policy)
                
                await self._events.publish(
                    "backup.started",
                    {"node_id": self.node_id, "timestamp": time.time()}
                )
                
                archive = self.coordinator.run_backup_cycle(state_data, policy_id)
                
                await self._events.publish(
                    "backup.completed",
                    {"backup_id": archive.backup_id, "timestamp": time.time()}
                )
                
                await self._bus.send(
                    reply_target,
                    MessageType.RECOVERY_STATUS,
                    {"success": True, "backup_id": archive.backup_id},
                )
            except Exception as exc:
                await self._events.publish(
                    "backup.failed",
                    {"node_id": self.node_id, "error": str(exc), "timestamp": time.time()}
                )
                await self._bus.send(
                    reply_target,
                    MessageType.RECOVERY_STATUS,
                    {"success": False, "error": str(exc)},
                )

        async def handle_restore_request(context: Any) -> None:
            payload = context.payload or {}
            backup_id = payload.get("backup_id")
            
            reply_target = context.sender
            try:
                await self._events.publish(
                    "restore.started",
                    {"backup_id": backup_id, "timestamp": time.time()}
                )
                
                state = self.coordinator.run_restore_cycle(backup_id or "")
                
                await self._events.publish(
                    "restore.completed",
                    {"backup_id": backup_id, "timestamp": time.time()}
                )
                
                await self._bus.send(
                    reply_target,
                    MessageType.RECOVERY_STATUS,
                    {"success": True, "state_data": state},
                )
            except Exception as exc:
                await self._events.publish(
                    "restore.failed",
                    {"backup_id": backup_id, "error": str(exc), "timestamp": time.time()}
                )
                await self._bus.send(
                    reply_target,
                    MessageType.RECOVERY_STATUS,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.BACKUP_REQUEST,
            _DisasterRecoveryQueryHandler(handle_backup_request),
        )
        router.register(
            MessageType.RESTORE_OPERATION,
            _DisasterRecoveryQueryHandler(handle_restore_request),
        )


class _DisasterRecoveryQueryHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
