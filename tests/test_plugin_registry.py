"""Unit tests for PluginRegistry."""

import pytest
from flock.plugins.exceptions import PluginAlreadyInstalledError
from flock.plugins.models import PluginManifest
from flock.plugins.registry import PluginRegistry


def test_plugin_registry_add_and_list() -> None:
    registry = PluginRegistry()
    manifest = PluginManifest(
        plugin_id="plugin-1",
        name="telemetry-exporter",
        version="1.0.0",
        author="flock",
    )

    registry.register_plugin(manifest)
    assert registry.get_plugin("plugin-1") == manifest
    assert len(registry.list_plugins()) == 1

    # Duplicate register throws PluginAlreadyInstalledError
    with pytest.raises(PluginAlreadyInstalledError):
        registry.register_plugin(manifest)

    registry.unregister_plugin("plugin-1")
    assert registry.get_plugin("plugin-1") is None
