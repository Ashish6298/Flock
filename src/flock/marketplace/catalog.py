"""Marketplace catalog registry and index search searches."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional
from flock.marketplace.exceptions import PackagePublishError
from flock.marketplace.models import PackageManifest


class MarketplaceCatalog:
    """Consolidated registry catalog mapping packages by categories and indexing manifests."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # package_id -> PackageManifest
        self._manifests: Dict[str, PackageManifest] = {}

    def register_manifest(self, manifest: PackageManifest) -> None:
        """Register an extension package manifest inside the catalog registry."""
        with self._lock:
            self._manifests[manifest.package_id] = manifest

    def get_manifest(self, package_id: str) -> PackageManifest:
        """Get registered package manifest metadata."""
        with self._lock:
            if package_id not in self._manifests:
                raise PackagePublishError(f"Package '{package_id}' not found in registry.")
            return self._manifests[package_id]

    def list_manifests(self) -> List[PackageManifest]:
        """List all active manifests."""
        with self._lock:
            return list(self._manifests.values())

    def unregister_manifest(self, package_id: str) -> None:
        """Remove a package manifest from registries catalog."""
        with self._lock:
            if package_id not in self._manifests:
                raise PackagePublishError(f"Package '{package_id}' not found.")
            del self._manifests[package_id]
