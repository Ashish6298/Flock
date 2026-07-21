"""Unit tests for PluginLoader."""

import pytest
from flock.events.bus import EventBus
from flock.plugins.loader import PluginLoader
from flock.plugins.models import PluginContext, PluginManifest
from flock.plugins.registry import PluginRegistry


@pytest.mark.asyncio
async def test_loader_executes_lifecycle_events() -> None:
    events = EventBus()
    registry = PluginRegistry()
    loader = PluginLoader(registry, events)

    manifest = PluginManifest(
        plugin_id="plugin-2",
        name="test-plugin",
        version="2.0.0",
        author="flock",
    )
    registry.register_plugin(manifest)

    ctx = PluginContext(plugin_id="plugin-2", data_directory="/tmp/plugin-2")

    loaded = await loader.load_plugin(manifest, ctx)
    assert loaded is True
    assert registry.is_activated("plugin-2") is True

    await loader.unload_plugin("plugin-2")
    assert registry.is_activated("plugin-2") is False
