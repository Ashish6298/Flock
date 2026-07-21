"""Plugin Registry tracking installations metadata."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from flock.plugins.exceptions import PluginAlreadyInstalledError, PluginNotFoundError
from flock.plugins.models import PluginManifest


class PluginRegistry:
    """Thread-safe index registry for dynamic manifests."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # plugin_id -> PluginManifest
        self._plugins: Dict[str, PluginManifest] = {}
        self._activated: Dict[str, bool] = {}

    def register_plugin(self, manifest: PluginManifest) -> None:
        """Add plugin metadata descriptor.

        Raises:
            PluginAlreadyInstalledError: If plugin ID is already registered.
        """
        with self._lock:
            if manifest.plugin_id in self._plugins:
                raise PluginAlreadyInstalledError(f"Plugin '{manifest.plugin_id}' already registered.")
            self._plugins[manifest.plugin_id] = manifest
            self._activated[manifest.plugin_id] = False

    def unregister_plugin(self, plugin_id: str) -> None:
        """Remove plugin metadata descriptor."""
        with self._lock:
            self._plugins.pop(plugin_id, None)
            self._activated.pop(plugin_id, None)

    def get_plugin(self, plugin_id: str) -> Optional[PluginManifest]:
        """Fetch plugin manifest descriptor."""
        with self._lock:
            return self._plugins.get(plugin_id)

    def list_plugins(self) -> List[PluginManifest]:
        """List all registered manifests."""
        with self._lock:
            return list(self._plugins.values())

    def set_activated(self, plugin_id: str, active: bool) -> None:
        """Update activated flag.

        Raises:
            PluginNotFoundError: If plugin ID is missing.
        """
        with self._lock:
            if plugin_id not in self._plugins:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' not found.")
            self._activated[plugin_id] = active

    def is_activated(self, plugin_id: str) -> bool:
        """Check active status."""
        with self._lock:
            return self._activated.get(plugin_id, False)
