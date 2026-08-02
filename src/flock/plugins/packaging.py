"""Plugin Packaging & Distribution Engine.

Provides deterministic package creation, manifest generation, ZIP archive packing,
SHA-256 integrity hashing, installation validation, and import/export capabilities.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import threading
import zipfile
from typing import List, Optional

import structlog

from flock.plugins.exceptions import (
    PluginExportError,
    PluginImportError,
    PluginInstallationError,
    PluginPackageValidationError,
)
from flock.plugins.models import (
    PluginArchive,
    PluginInstallationRecord,
    PluginManifest,
    PluginPackage,
    PluginPackageManifest,
    PluginPackageMetadata,
    PluginPackageValidationResult,
    PluginSignature,
)
from flock.plugins.registry import PluginRegistry

logger = structlog.get_logger()


class PluginPackagingEngine:
    """Handles building deterministic plugin packages, exporting/importing ZIP archives, and installation."""

    def __init__(self, registry: PluginRegistry, sdk_version: str = "1.0.0") -> None:
        self._registry = registry
        self._sdk_version = sdk_version
        self._lock = threading.RLock()

    def build_package(
        self,
        plugin_dir: str,
        output_dir: str,
        license_type: str = "MIT",
        operating_systems: Optional[List[str]] = None,
    ) -> PluginPackage:
        """Deterministically packs a plugin directory into a ZIP archive and outputs a PluginPackage."""
        if not os.path.isdir(plugin_dir):
            raise PluginPackageValidationError(f"Plugin directory '{plugin_dir}' does not exist.")

        manifest_path = os.path.join(plugin_dir, "manifest.json")
        if not os.path.isfile(manifest_path):
            raise PluginPackageValidationError(f"Plugin manifest file '{manifest_path}' is missing.")

        # Read manifest to resolve ID and version
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
            plugin_id = manifest_data["plugin_id"]
            version = manifest_data["version"]
        except Exception as exc:
            raise PluginPackageValidationError(f"Failed to read/parse plugin manifest: {exc}") from exc

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        archive_name = f"{plugin_id}-{version}.zip"
        archive_path = os.path.join(output_dir, archive_name)

        # Collect and sort files deterministically
        file_list: List[str] = []
        for root, _, files in os.walk(plugin_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, plugin_dir)
                file_list.append(rel_path)
        file_list.sort()  # Guarantee deterministic file list ordering

        # Construct zip archive deterministically
        # Using fixed zip entry times (epoch 0) and ordering to ensure deterministic SHA-256
        if os.path.exists(archive_path):
            os.remove(archive_path)

        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for rel_path in file_list:
                full_path = os.path.join(plugin_dir, rel_path)
                # Overwrite ZipInfo object with deterministic modification date/time (1980-01-01)
                zinfo = zipfile.ZipInfo(rel_path)
                zinfo.date_time = (1980, 1, 1, 0, 0, 0)
                zinfo.compress_type = zipfile.ZIP_DEFLATED
                with open(full_path, "rb") as f:
                    zf.writestr(zinfo, f.read())

        # Generate checksum hashes
        # 1. Manifest hash
        with open(manifest_path, "rb") as f:
            manifest_hash = hashlib.sha256(f.read()).hexdigest()

        # 2. Archive hash
        archive_hasher = hashlib.sha256()
        with open(archive_path, "rb") as f:
            while chunk := f.read(8192):
                archive_hasher.update(chunk)
        archive_hash = archive_hasher.hexdigest()

        file_size = os.path.getsize(archive_path)

        # Build structural model outputs
        pkg_manifest = PluginPackageManifest(
            plugin_id=plugin_id,
            version=version,
            manifest_checksum=manifest_hash,
            packaged_files=file_list,
        )
        metadata = PluginPackageMetadata(
            plugin_id=plugin_id,
            min_sdk_version=manifest_data.get("sdk_version", self._sdk_version),
            operating_systems=operating_systems or ["any"],
            license=license_type,
        )
        signature = PluginSignature(
            sha256_hash=archive_hash,
        )
        archive = PluginArchive(
            archive_path=archive_path,
            checksum=archive_hash,
            file_size_bytes=file_size,
        )

        return PluginPackage(
            plugin_id=plugin_id,
            manifest=pkg_manifest,
            metadata=metadata,
            signature=signature,
            archive=archive,
        )

    def validate_package(self, package: PluginPackage) -> PluginPackageValidationResult:
        """Evaluates plugin package archive structure, manifest checks, SDK match, and checksum matching."""
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Check archive file exists
        if not os.path.isfile(package.archive.archive_path):
            errors.append(f"Archive file '{package.archive.archive_path}' does not exist.")
            return PluginPackageValidationResult(success=False, errors=errors, warnings=warnings)

        # 2. Check archive checksum match
        archive_hasher = hashlib.sha256()
        try:
            with open(package.archive.archive_path, "rb") as f:
                while chunk := f.read(8192):
                    archive_hasher.update(chunk)
            real_hash = archive_hasher.hexdigest()
        except Exception as exc:
            errors.append(f"Failed to calculate archive checksum: {exc}")
            return PluginPackageValidationResult(success=False, errors=errors, warnings=warnings)

        if real_hash != package.signature.sha256_hash or real_hash != package.archive.checksum:
            errors.append(f"Archive checksum validation failed. Expected '{package.archive.checksum}', found '{real_hash}'.")

        # 3. Read manifest from ZIP and validate structure
        try:
            with zipfile.ZipFile(package.archive.archive_path, "r") as zf:
                manifest_content = zf.read("manifest.json")
                manifest_data = json.loads(manifest_content.decode("utf-8"))
        except Exception as exc:
            errors.append(f"Failed to read/parse manifest.json from ZIP archive: {exc}")
            return PluginPackageValidationResult(success=False, errors=errors, warnings=warnings)

        # Validate plugin ID and version format rules
        plugin_id = manifest_data.get("plugin_id", "")
        version = manifest_data.get("version", "")
        if not plugin_id or not re.match(r"^[a-zA-Z0-9_\-\.]+$", plugin_id):
            errors.append(f"Invalid plugin_id format in package manifest: '{plugin_id}'.")
        if not version or not re.match(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$", version):
            errors.append(f"Invalid version format in package manifest: '{version}'.")

        # SDK major version validation check
        req_sdk = manifest_data.get("sdk_version", "1.0.0")
        if req_sdk.split(".")[0] != self._sdk_version.split(".")[0]:
            errors.append(f"Incompatible SDK version. Requires '{req_sdk}' but target is '{self._sdk_version}'.")

        # Check duplicate package collision in registry
        existing = self._registry.get_plugin(package.plugin_id)
        if existing is not None and existing.version == package.manifest.version:
            warnings.append(f"Plugin package '{package.plugin_id}' v{package.manifest.version} already exists in registry.")

        success = len(errors) == 0
        return PluginPackageValidationResult(success=success, errors=errors, warnings=warnings)

    def install_package(self, package: PluginPackage, install_root_dir: str) -> PluginInstallationRecord:
        """Validates package integrity and extracts content to target installation directories."""
        # 1. Run validation
        val_res = self.validate_package(package)
        if not val_res.success:
            raise PluginPackageValidationError(f"Package validation failed: {', '.join(val_res.errors)}")

        # 2. Extract files
        plugin_install_dir = os.path.join(install_root_dir, package.plugin_id)
        if os.path.exists(plugin_install_dir):
            shutil.rmtree(plugin_install_dir)
        os.makedirs(plugin_install_dir, exist_ok=True)

        try:
            with zipfile.ZipFile(package.archive.archive_path, "r") as zf:
                zf.extractall(plugin_install_dir)
        except Exception as exc:
            raise PluginInstallationError(f"Extraction failed: {exc}") from exc

        # 3. Read extracted manifest and register plugin metadata
        manifest_path = os.path.join(plugin_install_dir, "manifest.json")
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
            
            # Construct standard manifest
            manifest = PluginManifest(
                plugin_id=manifest_data["plugin_id"],
                name=manifest_data["name"],
                version=manifest_data["version"],
                author=manifest_data.get("author", "unknown"),
                sdk_version=manifest_data.get("sdk_version", self._sdk_version),
                dependencies=manifest_data.get("dependencies", []),
                optional_dependencies=manifest_data.get("optional_dependencies", []),
                capabilities=manifest_data.get("capabilities", []),
                entry_point=manifest_data.get("entry_point"),
            )
            # Register in registry index
            self._registry.register_plugin(manifest)
        except Exception as exc:
            raise PluginInstallationError(f"Failed to register installed plugin: {exc}") from exc

        # 4. Save installation record
        record = PluginInstallationRecord(
            plugin_id=package.plugin_id,
            installed_version=package.manifest.version,
            archive_checksum=package.archive.checksum,
            install_path=plugin_install_dir,
            status="INSTALLED",
        )
        
        self._registry.record_package_installation(record, package)
        logger.info(
            "Plugin package installed successfully",
            plugin_id=package.plugin_id,
            version=package.manifest.version,
            install_path=plugin_install_dir,
        )
        return record

    def uninstall_package(self, plugin_id: str) -> bool:
        """Removes extracted content directories and updates the registry."""
        with self._lock:
            # Query record from registry
            records = self._registry.query_installation_history(plugin_id)
            if not records:
                return False

            latest_record = records[-1]
            if latest_record.status == "UNINSTALLED":
                return False

            # Delete files
            if os.path.exists(latest_record.install_path):
                try:
                    shutil.rmtree(latest_record.install_path)
                except Exception as exc:
                    logger.error("Failed to clean up install path during uninstallation", path=latest_record.install_path, error=str(exc))

            # Remove plugin metadata
            self._registry.unregister_plugin(plugin_id)
            self._registry.record_package_uninstallation(plugin_id)
            return True

    def export_package(self, plugin_id: str, export_target_path: str) -> None:
        """Exports the active installed package archive to an external path."""
        with self._lock:
            pkg = self._registry.query_installed_package(plugin_id)
            if pkg is None:
                raise PluginExportError(f"No installed package found for plugin '{plugin_id}'.")

            src_path = pkg.archive.archive_path
            if not os.path.isfile(src_path):
                raise PluginExportError(f"Source package archive '{src_path}' is missing.")

            try:
                shutil.copy2(src_path, export_target_path)
            except Exception as exc:
                raise PluginExportError(f"Failed to export archive to '{export_target_path}': {exc}") from exc

    def import_package(self, import_source_path: str, output_dir: str) -> PluginPackage:
        """Imports an external ZIP archive package, validating integrity and structure."""
        if not os.path.isfile(import_source_path):
            raise PluginImportError(f"Import source file '{import_source_path}' does not exist.")

        # Read manifest inside zip to extract details
        try:
            with zipfile.ZipFile(import_source_path, "r") as zf:
                manifest_content = zf.read("manifest.json")
                manifest_data = json.loads(manifest_content.decode("utf-8"))
            plugin_id = manifest_data["plugin_id"]
            version = manifest_data["version"]
        except Exception as exc:
            raise PluginImportError(f"Failed to parse manifest inside ZIP: {exc}") from exc

        # Copy archive to output_dir
        os.makedirs(output_dir, exist_ok=True)
        archive_name = f"{plugin_id}-{version}.zip"
        archive_path = os.path.join(output_dir, archive_name)

        try:
            shutil.copy2(import_source_path, archive_path)
        except Exception as exc:
            raise PluginImportError(f"Failed to copy archive to destination output: {exc}") from exc

        # Calculate hashes
        archive_hasher = hashlib.sha256()
        with open(archive_path, "rb") as f:
            while chunk := f.read(8192):
                archive_hasher.update(chunk)
        archive_hash = archive_hasher.hexdigest()

        file_size = os.path.getsize(archive_path)

        pkg_manifest = PluginPackageManifest(
            plugin_id=plugin_id,
            version=version,
            manifest_checksum="",  # Can be calculated if extracted, omitted for simplicity
            packaged_files=[],
        )
        metadata = PluginPackageMetadata(
            plugin_id=plugin_id,
            min_sdk_version=manifest_data.get("sdk_version", self._sdk_version),
        )
        signature = PluginSignature(
            sha256_hash=archive_hash,
        )
        archive = PluginArchive(
            archive_path=archive_path,
            checksum=archive_hash,
            file_size_bytes=file_size,
        )

        return PluginPackage(
            plugin_id=plugin_id,
            manifest=pkg_manifest,
            metadata=metadata,
            signature=signature,
            archive=archive,
        )

    def check_updates(self, plugin_id: str, new_version: str) -> bool:
        """Determines if the given version is newer than the currently installed plugin version."""
        with self._lock:
            existing = self._registry.get_plugin(plugin_id)
            if existing is None:
                return True
            
            # Simple major.minor.patch numeric check
            def parse(v: str) -> tuple[int, int, int]:
                parts = v.split("-", 1)[0].split(".")
                return int(parts[0]), int(parts[1]), int(parts[2])

            try:
                curr_t = parse(existing.version)
                new_t = parse(new_version)
                return new_t > curr_t
            except Exception:
                return new_version != existing.version
