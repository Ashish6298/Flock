"""Unit tests for PluginValidator."""

import pytest
from flock.plugins.models import PluginManifest
from flock.plugins.validation import PluginValidator
from flock.plugins.exceptions import PluginValidationError, PluginCompatibilityError, PluginDependencyError


def test_validate_manifest_success() -> None:
    manifest = PluginManifest(
        plugin_id="my-valid-plugin",
        name="Valid Plugin",
        version="1.0.0",
        author="Flock Author",
        entry_point="module:class",
    )
    # Should not raise any exceptions
    PluginValidator.validate_manifest(manifest)


def test_validate_manifest_empty_id() -> None:
    manifest = PluginManifest(
        plugin_id="",
        name="Valid Plugin",
        version="1.0.0",
        author="Flock Author",
        entry_point="module:class",
    )
    with pytest.raises(PluginValidationError, match="Plugin ID cannot be empty"):
        PluginValidator.validate_manifest(manifest)


def test_validate_manifest_reserved_namespace() -> None:
    manifest = PluginManifest(
        plugin_id="flock.reserved",
        name="Reserved Plugin",
        version="1.0.0",
        author="Flock Author",
        entry_point="module:class",
    )
    with pytest.raises(PluginValidationError, match="reserved for core modules"):
        PluginValidator.validate_manifest(manifest)


def test_validate_manifest_invalid_semver() -> None:
    manifest = PluginManifest(
        plugin_id="my-plugin",
        name="Valid Plugin",
        version="invalid-version",
        author="Flock Author",
        entry_point="module:class",
    )
    with pytest.raises(PluginValidationError, match="not a valid semantic version"):
        PluginValidator.validate_manifest(manifest)


def test_validate_sdk_compatibility() -> None:
    # Compatible
    manifest = PluginManifest(
        plugin_id="my-plugin",
        name="Valid Plugin",
        version="1.0.0",
        author="Flock Author",
        sdk_version="1.2.0",
        entry_point="module:class",
    )
    PluginValidator.validate_sdk_compatibility(manifest, "1.5.0")

    # Incompatible
    with pytest.raises(PluginCompatibilityError, match="requires SDK version"):
        PluginValidator.validate_sdk_compatibility(manifest, "2.0.0")


def test_validate_dependencies() -> None:
    manifest = PluginManifest(
        plugin_id="my-plugin",
        name="Valid Plugin",
        version="1.0.0",
        author="Flock Author",
        dependencies=["dep1", "dep2"],
        entry_point="module:class",
    )
    # Success
    PluginValidator.validate_dependencies(manifest, {"dep1", "dep2", "dep3"})

    # Missing dep2
    with pytest.raises(PluginDependencyError, match="Missing required dependencies"):
        PluginValidator.validate_dependencies(manifest, {"dep1"})
