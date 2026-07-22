"""Restore workflows, target state application, and execution validation."""

from __future__ import annotations

import json
import hashlib
import time
import threading
from typing import Dict, Any
from flock.recovery.exceptions import RestoreError
from flock.recovery.models import BackupArchive
from flock.recovery.backup import BackupManager
from flock.security.encryption import CryptographyEngine


class RestoreManager:
    """Orchestrates validation checks and reinstates cluster state machine from backups."""

    def __init__(self, backup_manager: BackupManager, crypto: CryptographyEngine) -> None:
        self._backup_mgr = backup_manager
        self._crypto = crypto
        self._lock = threading.RLock()
        self._restored_history: Dict[str, float] = {}

    def restore_backup(self, backup_id: str) -> Dict[str, Any]:
        """Verify archive integrity, decrypt, and return the restored state data dict.
        
        Raises:
            RestoreError: If checksum validation or signature checks fail.
        """
        with self._lock:
            archive = self._backup_mgr.get_archive(backup_id)
            
            # 1. Retrieve and decrypt raw data
            try:
                raw_data = self._backup_mgr.get_raw_backup_data(backup_id)
            except Exception as exc:
                raise RestoreError(f"Restoration read/decryption failed: {exc}") from exc
                
            # 2. Checksum validation
            current_checksum = hashlib.sha256(raw_data.encode("utf-8")).hexdigest()
            if current_checksum != archive.checksum:
                raise RestoreError("Checksum integrity mismatch detected.")
                
            # 3. Signature validation
            try:
                self._crypto.verify_signature(raw_data.encode("utf-8"), archive.signature)
            except Exception as exc:
                raise RestoreError(f"Digital signature validation failed: {exc}") from exc
                
            # 4. Reconstruct state
            try:
                state_data: Dict[str, Any] = json.loads(raw_data)
            except Exception as exc:
                raise RestoreError(f"Restored JSON state parsing failed: {exc}") from exc
                
            self._restored_history[backup_id] = time.time()
            return state_data

    def get_last_restore_time(self, backup_id: str) -> float:
        """Get timestamp when backup was restored, or 0.0."""
        with self._lock:
            return self._restored_history.get(backup_id, 0.0)
