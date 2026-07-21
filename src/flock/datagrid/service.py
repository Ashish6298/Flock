"""High-level DataGridService exposing database routes."""

from __future__ import annotations

from typing import Any

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.datagrid.cache import DistributedCacheEngine
from flock.datagrid.kvstore import KeyValueEngine
from flock.datagrid.locking import DistributedLockManager
from flock.datagrid.objectstore import ObjectStorageEngine
from flock.datagrid.registry import DataGridRegistry

logger = structlog.get_logger()


class DataGridService:
    """Wires registries, kv engines, cache, locks, and service endpoints."""

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
        self.registry = DataGridRegistry()
        self.cache = DistributedCacheEngine()
        self.kv = KeyValueEngine()
        self.object_store = ObjectStorageEngine()
        self.lock_manager = DistributedLockManager()

        self._running = False

    async def start(self) -> None:
        """Start policy listeners and sync query routes."""
        if self._running:
            return
        self._running = True

        self._register_handlers()
        logger.info("DataGridService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop datagrid operations."""
        self._running = False
        logger.info("DataGridService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register datagrid sync handlers on message bus."""
        router = self._bus.router

        async def handle_datagrid_put(context: Any) -> None:
            payload = context.payload or {}
            key = payload.get("key")
            value = payload.get("value")

            reply_target = context.sender
            try:
                rec = self.kv.put(str(key or ""), value)
                await self._bus.send(
                    reply_target,
                    MessageType.DATAGRID_HEALTH_REPORT,  # Reply with status sync
                    {"success": True, "key": key, "version": rec.version},
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.DATAGRID_HEALTH_REPORT,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.DATAGRID_PUT,
            _DataGridPutHandler(handle_datagrid_put),
        )


class _DataGridPutHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
