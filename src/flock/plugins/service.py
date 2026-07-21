"""High-level PluginService coordinating dynamic modules lifecycle."""

from __future__ import annotations

from typing import Any, Dict, Optional

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.plugins.loader import PluginLoader
from flock.plugins.models import PluginManifest
from flock.plugins.registry import PluginRegistry
from flock.plugins.resolver import PluginDependencyResolver
from flock.plugins.sandbox import PluginSandbox

logger = structlog.get_logger()


class PluginService:
    """Wires registries, dynamic class loaders, dependency solvers, and endpoints."""

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
        self.registry = PluginRegistry()
        self.loader = PluginLoader(self.registry, self._events)
        self.sandbox = PluginSandbox()
        self.resolver = PluginDependencyResolver()

        self._running = False

    async def start(self) -> None:
        """Start policy listeners and metrics query routes."""
        if self._running:
            return
        self._running = True

        self._register_handlers()
        logger.info("PluginService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop plugin service operations."""
        self._running = False
        logger.info("PluginService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register plugin sync handlers on message bus."""
        router = self._bus.router

        async def handle_plugin_install(context: Any) -> None:
            payload = context.payload or {}
            plug_id = payload.get("plugin_id")
            name = payload.get("name")
            version = payload.get("version")

            reply_target = context.sender
            try:
                # Add plugin descriptor to registry index
                new_manifest = PluginManifest(
                    plugin_id=str(plug_id or ""),
                    name=str(name or ""),
                    version=str(version or ""),
                    author="flock-core",
                )
                self.registry.register_plugin(new_manifest)

                await self._bus.send(
                    reply_target,
                    MessageType.PLUGIN_INSTALL_RESPONSE,
                    {"success": True, "plugin_id": plug_id},
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.PLUGIN_INSTALL_RESPONSE,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.PLUGIN_INSTALL_REQUEST,
            _PluginInstallHandler(handle_plugin_install),
        )


class _PluginInstallHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
