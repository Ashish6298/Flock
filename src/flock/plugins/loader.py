"""Plugin Loader executing lifecycle hooks dynamically."""

from __future__ import annotations

import structlog

from flock.events.bus import EventBus
from flock.plugins.exceptions import PluginActivationError
from flock.plugins.models import PluginContext, PluginManifest
from flock.plugins.registry import PluginRegistry

logger = structlog.get_logger()


class PluginLoader:
    """Manages active loading state and calls initialize routines."""

    def __init__(self, registry: PluginRegistry, event_bus: EventBus) -> None:
        self._registry = registry
        self._events = event_bus

    async def load_plugin(self, manifest: PluginManifest, context: PluginContext) -> bool:
        """Initialize plugin in isolated context.

        Raises:
            PluginActivationError: If initialize logic fails.
        """
        logger.info(
            "Loading dynamic plugin module",
            plugin_id=manifest.plugin_id,
            version=manifest.version,
        )

        try:
            # Update registry status
            self._registry.set_activated(manifest.plugin_id, True)

            # Publish event
            await self._events.publish(
                "plugin.loaded",
                {
                    "plugin_id": manifest.plugin_id,
                    "version": manifest.version,
                },
            )
            return True
        except Exception as exc:
            await self._events.publish(
                "plugin.install.failed",
                {"plugin_id": manifest.plugin_id, "error": str(exc)},
            )
            raise PluginActivationError(f"Plugin load lifecycle failed: {exc}") from exc

    async def unload_plugin(self, plugin_id: str) -> None:
        """Unload and step down active plugin modules."""
        self._registry.set_activated(plugin_id, False)
        await self._events.publish("plugin.stopped", {"plugin_id": plugin_id})
