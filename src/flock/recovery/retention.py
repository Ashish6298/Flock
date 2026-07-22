"""Enforces TTL limits and maximum backup counts on cataloged files."""

from __future__ import annotations

import time
import threading
from typing import List, Callable, Optional
from flock.recovery.models import BackupArchive, RetentionPolicy
from flock.recovery.backup import BackupManager


class RetentionManager:
    """Enforces configurable backup retention policies."""

    def __init__(self, backup_manager: BackupManager) -> None:
        self._backup_mgr = backup_manager
        self._lock = threading.RLock()

    def enforce_retention(self, policy: RetentionPolicy, eviction_callback: Optional[Callable[[str], None]] = None) -> List[str]:
        """Evict backups exceeding TTL or count limits. Returns list of deleted backup IDs."""
        with self._lock:
            archives = self._backup_mgr.list_archives()
            if not archives:
                return []
                
            now = time.time()
            deleted: List[str] = []
            
            # Sort by timestamp (oldest first)
            sorted_archives = sorted(archives, key=lambda a: a.timestamp)
            
            # 1. Enforce TTL policy
            cutoff = now - policy.ttl_seconds
            for archive in sorted_archives:
                if archive.timestamp < cutoff:
                    deleted.append(archive.backup_id)
                    self._backup_mgr.delete_archive(archive.backup_id)
                    if eviction_callback:
                        eviction_callback(archive.backup_id)
                        
            # Refresh remaining archives
            remaining = [a for a in sorted_archives if a.backup_id not in deleted]
            
            # 2. Enforce Max Backups Count policy
            if policy.max_backups_retained > 0 and len(remaining) > policy.max_backups_retained:
                excess_count = len(remaining) - policy.max_backups_retained
                # Delete oldest excess ones
                for i in range(excess_count):
                    archive = remaining[i]
                    deleted.append(archive.backup_id)
                    self._backup_mgr.delete_archive(archive.backup_id)
                    if eviction_callback:
                        eviction_callback(archive.backup_id)
                        
            return deleted
