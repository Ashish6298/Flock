"""Plugin Validation Engine."""

from __future__ import annotations

import re
from typing import Set, List
from flock.plugins.models import PluginManifest
from flock.plugins.exceptions import PluginValidationError, PluginCompatibilityError, PluginDependencyError


class PluginValidator:
    """Validates plugin manifests, semantic versions, dependencies, and namespaces."""

    @staticmethod
    def validate_manifest(manifest: PluginManifest) -> None:
        """Validates basic manifest layout and format.

        Raises:
            PluginValidationError: If validation fails.
        """
        if not manifest.plugin_id or not manifest.plugin_id.strip():
            raise PluginValidationError("Plugin ID cannot be empty.")

        # Check identifier format (alphanumeric, dots, underscores, dashes)
        if not re.match(r"^[a-zA-Z0-9_\-\.]+$", manifest.plugin_id):
            raise PluginValidationError(
                f"Invalid plugin ID '{manifest.plugin_id}'. Only alphanumeric, dots, dashes, and underscores allowed."
            )

        # Check reserved namespaces
        if manifest.plugin_id.startswith("flock."):
            raise PluginValidationError("The 'flock.' namespace is reserved for core modules.")

        if not manifest.name or not manifest.name.strip():
            raise PluginValidationError("Plugin name cannot be empty.")

        if not manifest.version or not manifest.version.strip():
            raise PluginValidationError("Plugin version cannot be empty.")

        # Simple semver check
        if not re.match(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$", manifest.version):
            raise PluginValidationError(
                f"Version '{manifest.version}' is not a valid semantic version (X.Y.Z)."
            )

    @staticmethod
    def validate_sdk_compatibility(manifest: PluginManifest, target_sdk_version: str) -> None:
        """Validates plugin SDK version compatibility.

        Raises:
            PluginCompatibilityError: If SDK version is incompatible.
        """
        # For simplicity, we check if major version matches or if the target is compatible
        # E.g. plugin_sdk="1.x", target_sdk="1.2.0"
        plugin_major = manifest.sdk_version.split(".")[0]
        target_major = target_sdk_version.split(".")[0]

        if plugin_major != target_major:
            raise PluginCompatibilityError(
                f"Plugin requires SDK version '{manifest.sdk_version}' but target is '{target_sdk_version}'."
            )

    @staticmethod
    def validate_dependencies(manifest: PluginManifest, available_plugin_ids: Set[str]) -> None:
        """Validates that all dependencies declared by the plugin are available.

        Raises:
            PluginDependencyError: If a dependency is missing.
        """
        missing: List[str] = []
        for dep in manifest.dependencies:
            if dep not in available_plugin_ids:
                missing.append(dep)

        if missing:
            raise PluginDependencyError(
                f"Missing required dependencies for '{manifest.plugin_id}': {', '.join(missing)}"
            )
