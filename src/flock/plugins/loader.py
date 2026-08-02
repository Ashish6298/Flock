"""Plugin Loader executing lifecycle hooks dynamically."""

from __future__ import annotations

import importlib
import structlog
from typing import Dict

from flock.events.bus import EventBus
from flock.plugins.exceptions import PluginActivationError, PluginValidationError, PluginCompatibilityError
from flock.plugins.models import PluginContext, PluginManifest
from flock.plugins.registry import PluginRegistry
from flock.plugins.validation import PluginValidator
from flock.plugins.base import FlockPlugin

logger = structlog.get_logger()


class PluginLoader:
    """Manages active loading state and calls initialize routines."""

    def __init__(self, registry: PluginRegistry, event_bus: EventBus, sdk_version: str = "1.0.0") -> None:
        self._registry = registry
        self._events = event_bus
        self._sdk_version = sdk_version
        self._instances: Dict[str, FlockPlugin] = {}

    async def load_plugin(self, manifest: PluginManifest, context: PluginContext) -> bool:
        """Initialize and activate plugin in isolated context.

        Raises:
            PluginValidationError: If manifest check fails.
            PluginCompatibilityError: If SDK version is incompatible.
            PluginActivationError: If initialize/activate logic fails.
        """
        logger.info(
            "Loading dynamic plugin module",
            plugin_id=manifest.plugin_id,
            version=manifest.version,
        )

        try:
            # 1. Validate manifest and SDK compatibility
            PluginValidator.validate_manifest(manifest)
            PluginValidator.validate_sdk_compatibility(manifest, self._sdk_version)

            if not manifest.entry_point:
                raise PluginValidationError("Plugin manifest must specify an entry_point.")

            # 2. Dynamic Import
            if ":" not in manifest.entry_point:
                raise PluginValidationError(
                    f"Invalid entry_point format '{manifest.entry_point}'. Expected 'module:class'."
                )

            module_name, class_name = manifest.entry_point.split(":", 1)
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, class_name, None)

            if not plugin_class:
                raise PluginActivationError(
                    f"Class '{class_name}' not found in module '{module_name}'."
                )

            if not issubclass(plugin_class, FlockPlugin):
                raise PluginValidationError(
                    f"Plugin class '{class_name}' must inherit from FlockPlugin."
                )

            # 3. Instantiate Plugin
            plugin_instance = plugin_class(context)

            # 4. Call initialize lifecycle hook
            await plugin_instance.initialize()

            # 5. Call activate lifecycle hook
            await plugin_instance.activate()

            # Save instance reference
            self._instances[manifest.plugin_id] = plugin_instance

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

        except (PluginValidationError, PluginCompatibilityError) as exc:
            await self._events.publish(
                "plugin.install.failed",
                {"plugin_id": manifest.plugin_id, "error": str(exc)},
            )
            raise
        except Exception as exc:
            await self._events.publish(
                "plugin.install.failed",
                {"plugin_id": manifest.plugin_id, "error": str(exc)},
            )
            raise PluginActivationError(f"Plugin load lifecycle failed: {exc}") from exc

    async def unload_plugin(self, plugin_id: str) -> None:
        """Unload and step down active plugin modules."""
        plugin_instance = self._instances.get(plugin_id)
        if plugin_instance:
            try:
                await plugin_instance.deactivate()
                await plugin_instance.cleanup()
            except Exception as exc:
                logger.error(
                    "Error during plugin cleanup",
                    plugin_id=plugin_id,
                    error=str(exc),
                )
            finally:
                self._instances.pop(plugin_id, None)

        self._registry.set_activated(plugin_id, False)
        await self._events.publish("plugin.stopped", {"plugin_id": plugin_id})

    def get_instance(self, plugin_id: str) -> FlockPlugin | None:
        """Get running plugin instance."""
        return self._instances.get(plugin_id)
