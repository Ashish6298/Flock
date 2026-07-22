"""Extension package updates manager and rollback handlers."""

from __future__ import annotations

import time
import threading
from typing import Dict, List, Optional
from flock.marketplace.exceptions import RollbackError, InstallationError
from flock.marketplace.models import InstallationReceipt, PackageManifest
from flock.marketplace.installer import PackageInstaller


class PackageUpdater:
    """Manages update channels and triggers rolling updates/upgrades operations."""

    def __init__(self, installer: PackageInstaller) -> None:
        self._installer = installer
        self._lock = threading.RLock()
        # package_id -> list of historic installed versions (for rollbacks)
        self._version_history: Dict[str, List[str]] = {}

    def upgrade_package(self, new_manifest: PackageManifest) -> InstallationReceipt:
        """Upgrade an existing package version, saving the previous version in the rollback catalog."""
        with self._lock:
            pid = new_manifest.package_id
            
            # Save history if already installed
            try:
                current_receipt = self._installer.get_receipt(pid)
                history = self._version_history.setdefault(pid, [])
                if current_receipt.installed_version not in history:
                    history.append(current_receipt.installed_version)
            except Exception:
                # Package not installed previously
                pass
                
            # Perform install
            return self._installer.install_package(new_manifest)

    def rollback_package(self, package_id: str) -> InstallationReceipt:
        """Rollback package version to the immediate preceding version history record.
        
        Raises:
            RollbackError: If no rollback history target version is found.
        """
        with self._lock:
            history = self._version_history.get(package_id, [])
            if not history:
                raise RollbackError(f"No rollback target version found for package '{package_id}'.")
                
            target_version = history.pop()
            
            # Update receipt to reflect rollback state
            current_receipt = self._installer.get_receipt(package_id)
            
            from flock.marketplace.models import InstallationReceipt
            import uuid
            
            new_receipt = InstallationReceipt(
                transaction_id=str(uuid.uuid4()),
                package_id=package_id,
                installed_version=target_version,
                installed_at=time.time(),
                status="rolled_back",
            )
            self._installer._receipts[package_id] = new_receipt
            return new_receipt
