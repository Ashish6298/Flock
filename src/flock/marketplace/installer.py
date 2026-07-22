"""Extension package installation manager with transactional states."""

from __future__ import annotations

import time
import uuid
import threading
from typing import Dict, List, Optional
from flock.marketplace.exceptions import InstallationError
from flock.marketplace.models import InstallationReceipt, PackageManifest


class PackageInstaller:
    """Installs extension packages and updates transactional receipts catalogs."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # package_id -> InstallationReceipt
        self._receipts: Dict[str, InstallationReceipt] = {}

    def install_package(self, manifest: PackageManifest) -> InstallationReceipt:
        """Simulate transactional package unpacking and load operations."""
        with self._lock:
            # We record transaction receipts
            tx_id = str(uuid.uuid4())
            receipt = InstallationReceipt(
                transaction_id=tx_id,
                package_id=manifest.package_id,
                installed_version=manifest.version,
                installed_at=time.time(),
                status="active",
            )
            self._receipts[manifest.package_id] = receipt
            return receipt

    def uninstall_package(self, package_id: str) -> None:
        """Disenrolls extension and removes installation states."""
        with self._lock:
            if package_id not in self._receipts:
                raise InstallationError(f"Package '{package_id}' is not installed.")
            del self._receipts[package_id]

    def get_receipt(self, package_id: str) -> InstallationReceipt:
        """Get receipt metadata details."""
        with self._lock:
            if package_id not in self._receipts:
                raise InstallationError(f"Package '{package_id}' is not installed.")
            return self._receipts[package_id]

    def list_installed_receipts(self) -> List[InstallationReceipt]:
        """List all active installation receipts."""
        with self._lock:
            return list(self._receipts.values())
