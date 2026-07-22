"""Compression and encryption wrappers for compiling snapshot states into BackupArchives."""

from __future__ import annotations

import json
import hashlib
import time
import uuid
import threading
from typing import Dict, List, Optional
from flock.recovery.exceptions import BackupError
from flock.recovery.models import BackupArchive, ClusterSnapshot
from flock.security.encryption import CryptographyEngine


class BackupManager:
    """Handles full and incremental backup creation and cryptographic envelope packaging."""

    def __init__(self, crypto: CryptographyEngine) -> None:
        self._crypto = crypto
        self._lock = threading.RLock()
        self._archives: Dict[str, BackupArchive] = {}
        # Track raw content for restores: backup_id -> plaintext string
        self._raw_backups: Dict[str, str] = {}

    def create_backup(
        self,
        snapshot: ClusterSnapshot,
        backup_type: str = "full",
        encrypt: bool = True,
    ) -> BackupArchive:
        """Compile a ClusterSnapshot into a signed and optionally encrypted BackupArchive."""
        with self._lock:
            backup_id = str(uuid.uuid4())
            now = time.time()
            
            raw_data = json.dumps(snapshot.data, sort_keys=True)
            checksum = hashlib.sha256(raw_data.encode("utf-8")).hexdigest()
            signature = self._crypto.sign_data(raw_data.encode("utf-8"))
            
            if encrypt:
                # Encrypt data using AES-GCM emulation from Security package
                ciphertext, iv, tag = self._crypto.encrypt_aes_gcm(raw_data)
                # Pack envelope metadata into archive's details
                metadata = {
                    "iv": iv,
                    "tag": tag,
                    "ciphertext": ciphertext,
                }
                data_size = len(ciphertext)
            else:
                metadata = {}
                data_size = len(raw_data)
                
            archive = BackupArchive(
                backup_id=backup_id,
                snapshot_id=snapshot.snapshot_id,
                timestamp=now,
                backup_type=backup_type,
                checksum=checksum,
                signature=signature,
                encrypted=encrypt,
                data_size=data_size,
                metadata=metadata,
            )
            
            self._archives[backup_id] = archive
            self._raw_backups[backup_id] = raw_data
            return archive

    def get_raw_backup_data(self, backup_id: str) -> str:
        """Get the raw backup JSON data, decrypting it if necessary."""
        with self._lock:
            archive = self._archives.get(backup_id)
            if not archive:
                raise BackupError(f"Backup archive '{backup_id}' not found.")
                
            if archive.encrypted:
                iv = archive.metadata.get("iv", "")
                tag = archive.metadata.get("tag", "")
                ciphertext = archive.metadata.get("ciphertext", "")
                try:
                    return self._crypto.decrypt_aes_gcm(ciphertext, iv, tag)
                except Exception as exc:
                    raise BackupError(f"Failed to decrypt backup archive {backup_id}: {exc}") from exc
            else:
                return self._raw_backups.get(backup_id, "{}")

    def get_archive(self, backup_id: str) -> BackupArchive:
        """Get backup archive descriptor."""
        with self._lock:
            if backup_id not in self._archives:
                raise BackupError(f"Backup archive '{backup_id}' not found.")
            return self._archives[backup_id]

    def list_archives(self) -> List[BackupArchive]:
        """List all available backup archives."""
        with self._lock:
            return list(self._archives.values())

    def delete_archive(self, backup_id: str) -> None:
        """Delete backup archive from catalog."""
        with self._lock:
            self._archives.pop(backup_id, None)
            self._raw_backups.pop(backup_id, None)
