"""Base interfaces for Flock Plugins."""

from __future__ import annotations

from flock.plugins.models import PluginContext


class FlockPlugin:
    """Abstract base class that all plugins must implement."""

    def __init__(self, context: PluginContext) -> None:
        self.context = context

    async def initialize(self) -> None:
        """Called when the plugin is first loaded."""
        pass

    async def activate(self) -> None:
        """Called when the plugin is activated."""
        pass

    async def deactivate(self) -> None:
        """Called when the plugin is deactivated."""
        pass

    async def cleanup(self) -> None:
        """Called when the plugin is unloaded or shut down."""
        pass
