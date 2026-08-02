"""Unit and integration tests for Plugin Packaging, Distribution & Marketplace Foundation."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import pytest

from flock.plugins.models import PluginPackage
from flock.plugins.registry import PluginRegistry
from flock.plugins.packaging import PluginPackagingEngine
from flock.plugins.exceptions import PluginPackageValidationError, PluginExportError, PluginImportError


@pytest.fixture
def temp_workspace() -> str:
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path)


@pytest.fixture
def mock_plugin_dir(temp_workspace: str) -> str:
    plugin_dir = os.path.join(temp_workspace, "mock-plugin")
    os.makedirs(plugin_dir, exist_ok=True)
    
    manifest = {
        "plugin_id": "test-plugin",
        "name": "Test Plugin",
        "version": "1.2.3",
        "sdk_version": "1.0.0",
        "author": "Tester",
        "dependencies": [],
        "capabilities": []
    }
    
    with open(os.path.join(plugin_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f)
        
    with open(os.path.join(plugin_dir, "main.py"), "w", encoding="utf-8") as f:
        f.write("# Plugin main code\n")
        
    return plugin_dir


def test_deterministic_packaging(mock_plugin_dir: str, temp_workspace: str) -> None:
    registry = PluginRegistry()
    engine = PluginPackagingEngine(registry, sdk_version="1.0.0")

    out_dir1 = os.path.join(temp_workspace, "out1")
    out_dir2 = os.path.join(temp_workspace, "out2")

    pkg1 = engine.build_package(mock_plugin_dir, out_dir1)
    pkg2 = engine.build_package(mock_plugin_dir, out_dir2)

    # Hashes and sizes must match deterministically
    assert pkg1.signature.sha256_hash == pkg2.signature.sha256_hash
    assert pkg1.archive.file_size_bytes == pkg2.archive.file_size_bytes
    assert pkg1.manifest.plugin_id == "test-plugin"


def test_validation_fails_for_missing_manifest(temp_workspace: str) -> None:
    registry = PluginRegistry()
    engine = PluginPackagingEngine(registry, sdk_version="1.0.0")

    empty_dir = os.path.join(temp_workspace, "empty")
    os.makedirs(empty_dir, exist_ok=True)

    with pytest.raises(PluginPackageValidationError):
        engine.build_package(empty_dir, os.path.join(temp_workspace, "out"))


def test_validation_detects_incompatible_sdk(mock_plugin_dir: str, temp_workspace: str) -> None:
    registry = PluginRegistry()
    # SDK target version is major version 2.0.0
    engine = PluginPackagingEngine(registry, sdk_version="2.0.0")

    pkg = engine.build_package(mock_plugin_dir, os.path.join(temp_workspace, "out"))
    val_res = engine.validate_package(pkg)
    assert val_res.success is False
    assert any("Incompatible SDK version" in err for err in val_res.errors)


def test_install_uninstall_workflow(mock_plugin_dir: str, temp_workspace: str) -> None:
    registry = PluginRegistry()
    engine = PluginPackagingEngine(registry, sdk_version="1.0.0")

    out_dir = os.path.join(temp_workspace, "out")
    pkg = engine.build_package(mock_plugin_dir, out_dir)

    install_root = os.path.join(temp_workspace, "install_root")
    record = engine.install_package(pkg, install_root)

    assert record.plugin_id == "test-plugin"
    assert record.status == "INSTALLED"
    assert registry.get_plugin("test-plugin") is not None

    # Check uninstallation
    success = engine.uninstall_package("test-plugin")
    assert success is True
    assert registry.get_plugin("test-plugin") is None

    # Check uninstallation history is kept
    history = registry.query_installation_history("test-plugin")
    assert len(history) == 1
    assert history[0].status == "UNINSTALLED"


def test_export_import_workflow(mock_plugin_dir: str, temp_workspace: str) -> None:
    registry = PluginRegistry()
    engine = PluginPackagingEngine(registry, sdk_version="1.0.0")

    out_dir = os.path.join(temp_workspace, "out")
    pkg = engine.build_package(mock_plugin_dir, out_dir)

    install_root = os.path.join(temp_workspace, "install_root")
    engine.install_package(pkg, install_root)

    export_path = os.path.join(temp_workspace, "exported.zip")
    engine.export_package("test-plugin", export_path)
    assert os.path.isfile(export_path)

    # Import package again
    imported_pkg = engine.import_package(export_path, os.path.join(temp_workspace, "imported_out"))
    assert imported_pkg.plugin_id == "test-plugin"


def test_check_updates(mock_plugin_dir: str, temp_workspace: str) -> None:
    registry = PluginRegistry()
    engine = PluginPackagingEngine(registry, sdk_version="1.0.0")

    out_dir = os.path.join(temp_workspace, "out")
    pkg = engine.build_package(mock_plugin_dir, out_dir)

    install_root = os.path.join(temp_workspace, "install_root")
    engine.install_package(pkg, install_root)

    # Current version is 1.2.3, version 1.2.4 should be an update
    assert engine.check_updates("test-plugin", "1.2.4") is True
    # Version 1.2.2 should not be an update
    assert engine.check_updates("test-plugin", "1.2.2") is False
