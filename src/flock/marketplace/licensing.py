"""Commercial extensions licensing keys validators."""

from __future__ import annotations

import threading
from typing import Dict, Optional


class LicenseManager:
    """Manages active license key files and validates customer entitlement scopes."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # package_id -> license_key
        self._keys: Dict[str, str] = {}

    def register_license(self, package_id: str, license_key: str) -> None:
        """Register a license key for validation checking."""
        with self._lock:
            self._keys[package_id] = license_key

    def validate_license(self, package_id: str, license_key: str) -> bool:
        """Verify license key matches active registrations."""
        with self._lock:
            val = self._keys.get(package_id)
            return val is not None and val == license_key

    def revoke_license(self, package_id: str) -> None:
        """Revoke a license."""
        with self._lock:
            self._keys.pop(package_id, None)
