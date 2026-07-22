"""Integrity verification engine validating checksums and cryptographic signatures."""

from __future__ import annotations

import hashlib
import threading
from typing import Dict
from flock.recovery.exceptions import IntegrityError
from flock.recovery.models import BackupArchive
from flock.recovery.backup import BackupManager
from flock.security.encryption import CryptographyEngine


class IntegrityVerifier:
    """Verifies that backups have not been corrupted or tampered with."""

    def __init__(self, backup_manager: BackupManager, crypto: CryptographyEngine) -> None:
        self._backup_mgr = backup_manager
        self._crypto = crypto

    def verify_archive_integrity(self, backup_id: str) -> bool:
        """Validate SHA-256 checksum and digital signature of a backup archive.
        
        Raises:
            IntegrityError: If checksum validation or signature checks fail.
        """
        archive = self._backup_mgr.get_archive(backup_id)
        
        try:
            raw_data = self._backup_mgr.get_raw_backup_data(backup_id)
        except Exception as exc:
            raise IntegrityError(f"Failed to read backup data for integrity verification: {exc}") from exc
            
        # 1. Verify Checksum
        calculated = hashlib.sha256(raw_data.encode("utf-8")).hexdigest()
        if calculated != archive.checksum:
            raise IntegrityError(f"Checksum verification failed for backup {backup_id}.")
            
        # 2. Verify Digital Signature
        try:
            self._crypto.verify_signature(raw_data.encode("utf-8"), archive.signature)
        except Exception as exc:
            raise IntegrityError(f"Cryptographic signature check failed for backup {backup_id}: {exc}") from exc
            
        return True
