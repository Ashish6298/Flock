"""Ecosystem package validation rules (compatibility and licenses verification)."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional
from flock.marketplace.exceptions import CompatibilityError, LicenseValidationError
from flock.marketplace.models import PackageManifest


class MarketplaceValidator:
    """Validates platform versions compatibility checks and commercial licenses verification."""

    def __init__(self, platform_version: str, active_features: List[str]) -> None:
        self.platform_version = platform_version
        self.active_features = active_features
        self._lock = threading.RLock()
        self._valid_licenses: Dict[str, str] = {}  # package_id -> license_key

    def register_valid_license(self, package_id: str, license_key: str) -> None:
        with self._lock:
            self._valid_licenses[package_id] = license_key

    def validate_package_compatibility(self, manifest: PackageManifest) -> bool:
        """Validate if the package requires features active in the current target cluster.
        
        Raises:
            CompatibilityError: If required features are missing.
        """
        with self._lock:
            for feat in manifest.required_features:
                if feat not in self.active_features:
                    raise CompatibilityError(f"Required feature '{feat}' is not active on this cluster.")
            return True

    def validate_package_license(self, manifest: PackageManifest) -> bool:
        """Validate license key parameter inside package manifest.
        
        Raises:
            LicenseValidationError: If validation fails or key is missing for commercial extensions.
        """
        with self._lock:
            if manifest.license_key is None:
                return True  # Open source/free extension
                
            expected = self._valid_licenses.get(manifest.package_id)
            if not expected or expected != manifest.license_key:
                raise LicenseValidationError(f"Invalid license key for package '{manifest.package_id}'.")
                
            return True
class SemanticVersionManager:
    """Helper class managing release updates and version validation."""

    @staticmethod
    def is_valid_semver(version: str) -> bool:
        """Returns True if the version string is a valid semver major.minor.patch format."""
        import re
        return bool(re.match(r"^\d+\.\d+\.\d+$", version))
