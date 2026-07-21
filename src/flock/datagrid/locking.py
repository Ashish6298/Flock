"""Distributed Lock Manager."""

from __future__ import annotations

import time
import uuid
import threading
from typing import Dict, Optional

from flock.datagrid.exceptions import LockAcquisitionError
from flock.datagrid.models import LockLease


class DistributedLockManager:
    """Acquires lock keys leases and validates expirations."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # lock_key -> LockLease
        self._leases: Dict[str, LockLease] = {}

    def acquire_lock(self, key: str, lease_seconds: float) -> LockLease:
        """Acquire key lock. Raise exception if key lease is active.

        Raises:
            LockAcquisitionError: If lease has not expired.
        """
        now = time.time()
        with self._lock:
            current = self._leases.get(key)
            if current and now < current.expires_at:
                raise LockAcquisitionError(f"Lock '{key}' is active and held until {current.expires_at}.")

            lease_id = str(uuid.uuid4())
            lease = LockLease(lock_key=key, lease_id=lease_id, expires_at=now + lease_seconds)
            self._leases[key] = lease
            return lease

    def release_lock(self, key: str, lease_id: str) -> None:
        """Release key lock."""
        with self._lock:
            current = self._leases.get(key)
            if not current:
                return

            if current.lease_id == lease_id:
                self._leases.pop(key, None)
