"""Unit tests for PluginDiscovery."""

import json
import tempfile
from pathlib import Path
from flock.plugins.discovery import PluginDiscovery


def test_discovery_scans_and_finds_manifests() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a plugin directory layout
        plugin_dir = Path(tmpdir) / "test_plugin"
        plugin_dir.mkdir()

        manifest_data = {
            "plugin_id": "test-discovered-plugin",
            "name": "Discovered Plugin",
            "version": "1.0.0",
            "author": "Flock Team",
            "entry_point": "module:class",
            "sdk_version": "1.0.0",
        }

        with open(plugin_dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest_data, f)

        # Run discovery
        discovery = PluginDiscovery(search_paths=[tmpdir])
        discovered = discovery.discover_plugins()

        assert len(discovered) == 1
        assert discovered[0].plugin_id == "test-discovered-plugin"
        assert discovered[0].name == "Discovered Plugin"
