"""Unit tests for PluginLoader."""

import pytest
from flock.events.bus import EventBus
from flock.plugins.loader import PluginLoader
from flock.plugins.models import PluginContext, PluginManifest
from flock.plugins.registry import PluginRegistry
from flock.plugins.base import FlockPlugin
from flock.plugins.exceptions import PluginValidationError, PluginCompatibilityError, PluginActivationError


class DummyTestPlugin(FlockPlugin):
    """A dummy plugin class for unit tests."""

    def __init__(self, context: PluginContext) -> None:
        super().__init__(context)
        self.initialized = False
        self.activated = False
        self.deactivated = False
        self.cleaned_up = False

    async def initialize(self) -> None:
        self.initialized = True

    async def activate(self) -> None:
        self.activated = True

    async def deactivate(self) -> None:
        self.deactivated = True

    async def cleanup(self) -> None:
        self.cleaned_up = True


@pytest.mark.asyncio
async def test_loader_executes_lifecycle_events() -> None:
    events = EventBus()
    registry = PluginRegistry()
    loader = PluginLoader(registry, events, sdk_version="1.2.0")

    manifest = PluginManifest(
        plugin_id="plugin-2",
        name="test-plugin",
        version="2.0.0",
        author="flock",
        sdk_version="1.2.0",
        entry_point="tests.test_plugin_loader:DummyTestPlugin",
    )
    registry.register_plugin(manifest)

    ctx = PluginContext(plugin_id="plugin-2", data_directory="/tmp/plugin-2")

    loaded = await loader.load_plugin(manifest, ctx)
    assert loaded is True
    assert registry.is_activated("plugin-2") is True

    # Retrieve and check instance state
    instance = loader.get_instance("plugin-2")
    assert instance is not None
    assert getattr(instance, "initialized") is True
    assert getattr(instance, "activated") is True

    await loader.unload_plugin("plugin-2")
    assert registry.is_activated("plugin-2") is False
    assert getattr(instance, "deactivated") is True
    assert getattr(instance, "cleaned_up") is True


@pytest.mark.asyncio
async def test_loader_validation_errors() -> None:
    events = EventBus()
    registry = PluginRegistry()
    loader = PluginLoader(registry, events, sdk_version="1.2.0")
    ctx = PluginContext(plugin_id="plugin-err", data_directory="/tmp/err")

    # Missing entry_point
    manifest_no_entry = PluginManifest(
        plugin_id="plugin-no-entry",
        name="test-plugin",
        version="2.0.0",
        author="flock",
        sdk_version="1.2.0",
    )
    with pytest.raises(PluginValidationError, match="must specify an entry_point"):
        await loader.load_plugin(manifest_no_entry, ctx)

    # Incompatible SDK
    manifest_incompat = PluginManifest(
        plugin_id="plugin-incompat",
        name="test-plugin",
        version="2.0.0",
        author="flock",
        sdk_version="2.0.0",
        entry_point="tests.test_plugin_loader:DummyTestPlugin",
    )
    with pytest.raises(PluginCompatibilityError):
        await loader.load_plugin(manifest_incompat, ctx)
