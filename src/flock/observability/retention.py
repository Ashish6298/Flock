"""Retention Manager – Phase 34.

Manages TTL-based expiry, compaction, archival, and cleanup of
in-memory telemetry records.  Each retention policy is associated
with a named store; cleanup is triggered explicitly via
:meth:`RetentionManager.run_cleanup` or on demand via
:meth:`RetentionManager.expire`.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple


class RetentionPolicy:
    """Configuration for a single retention policy.

    Attributes:
        name: Policy identifier.
        ttl_seconds: Maximum age of records in seconds.
        max_records: Maximum number of records to keep (``0`` = unlimited).
        archive_handler: Optional callable invoked with expired records
            before they are removed.
    """

    def __init__(
        self,
        name: str,
        ttl_seconds: float,
        max_records: int = 0,
        archive_handler: Optional[Callable[[List[Any]], None]] = None,
    ) -> None:
        """Initialise.

        Args:
            name: Policy identifier.
            ttl_seconds: Record lifetime in seconds.
            max_records: Capacity limit (``0`` = unlimited).
            archive_handler: Called with expired records for archival.
        """
        self.name: str = name
        self.ttl_seconds: float = ttl_seconds
        self.max_records: int = max_records
        self.archive_handler: Optional[Callable[[List[Any]], None]] = archive_handler


class RetentionStore:
    """Thread-safe timestamped record store with TTL eviction.

    Each record is stored as a ``(timestamp, record)`` tuple.  During
    cleanup, records older than the policy's TTL are removed; if
    ``max_records`` is set, the oldest excess records are also trimmed.

    Attributes:
        _policy: Controlling :class:`RetentionPolicy`.
        _records: List of ``(timestamp, record)`` pairs.
        _lock: Protects ``_records``.
    """

    def __init__(self, policy: RetentionPolicy) -> None:
        """Initialise.

        Args:
            policy: Governing retention policy.
        """
        self._policy: RetentionPolicy = policy
        self._records: List[Tuple[float, Any]] = []
        self._lock: threading.Lock = threading.Lock()

    def append(self, record: Any) -> None:
        """Append a record with the current timestamp.

        Args:
            record: The record to store.
        """
        now = time.time()
        with self._lock:
            self._records.append((now, record))

    def purge_expired(self) -> List[Any]:
        """Remove records older than the policy TTL.

        If an ``archive_handler`` is registered it is called with the
        list of expired records before they are removed.

        Returns:
            The expired records that were removed.
        """
        now = time.time()
        cutoff = now - self._policy.ttl_seconds
        with self._lock:
            expired = [r for ts, r in self._records if ts < cutoff]
            self._records = [(ts, r) for ts, r in self._records if ts >= cutoff]

        if expired and self._policy.archive_handler is not None:
            try:
                self._policy.archive_handler(expired)
            except Exception:
                pass

        return expired

    def enforce_capacity(self) -> List[Any]:
        """Remove oldest records exceeding ``max_records``.

        Returns:
            Records that were removed to enforce the capacity limit.
        """
        if self._policy.max_records <= 0:
            return []
        with self._lock:
            excess_count = max(0, len(self._records) - self._policy.max_records)
            if excess_count == 0:
                return []
            removed = [r for _, r in self._records[:excess_count]]
            self._records = self._records[excess_count:]
        return removed

    def all_records(self) -> List[Any]:
        """Return all current records without timestamps."""
        with self._lock:
            return [r for _, r in self._records]

    def count(self) -> int:
        """Return the number of stored records."""
        with self._lock:
            return len(self._records)

    def clear(self) -> None:
        """Remove all records."""
        with self._lock:
            self._records.clear()


class RetentionManager:
    """Manages multiple named retention stores with independent policies.

    Attributes:
        _lock: Protects the store registry.
        _stores: Mapping of policy name to :class:`RetentionStore`.
        _cleanup_count: Cumulative cleanup runs.
    """

    def __init__(self) -> None:
        """Initialise an empty retention manager."""
        self._lock: threading.RLock = threading.RLock()
        self._stores: Dict[str, RetentionStore] = {}
        self._cleanup_count: int = 0

    # ------------------------------------------------------------------
    # Policy / store management
    # ------------------------------------------------------------------

    def register_policy(self, policy: RetentionPolicy) -> None:
        """Register a retention policy and create its backing store.

        If a store already exists under the policy name it is replaced.

        Args:
            policy: The :class:`RetentionPolicy` to register.
        """
        with self._lock:
            self._stores[policy.name] = RetentionStore(policy)

    def get_store(self, name: str) -> Optional[RetentionStore]:
        """Return the retention store for a policy name or ``None``."""
        with self._lock:
            return self._stores.get(name)

    def list_policies(self) -> List[str]:
        """Return the names of all registered policies."""
        with self._lock:
            return list(self._stores.keys())

    def store_count(self, name: str) -> int:
        """Return the number of records in a named store.

        Args:
            name: Policy name.

        Returns:
            Record count, or ``0`` if the store is not registered.
        """
        with self._lock:
            store = self._stores.get(name)
        return store.count() if store is not None else 0

    # ------------------------------------------------------------------
    # Record management
    # ------------------------------------------------------------------

    def append(self, policy_name: str, record: Any) -> None:
        """Append a record to a named store.

        Args:
            policy_name: Target policy name.
            record: Record to append.

        Raises:
            KeyError: If ``policy_name`` is not registered.
        """
        with self._lock:
            store = self._stores.get(policy_name)
        if store is None:
            raise KeyError(f"Retention policy '{policy_name}' is not registered.")
        store.append(record)

    def get_records(self, policy_name: str) -> List[Any]:
        """Return all current records for a named store.

        Args:
            policy_name: Target policy name.

        Returns:
            List of records, or empty list if not registered.
        """
        with self._lock:
            store = self._stores.get(policy_name)
        return store.all_records() if store is not None else []

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def expire(self, policy_name: str) -> List[Any]:
        """Run TTL expiry for a single named store.

        Args:
            policy_name: Store to expire.

        Returns:
            List of expired records.
        """
        with self._lock:
            store = self._stores.get(policy_name)
        if store is None:
            return []
        return store.purge_expired()

    def run_cleanup(self) -> Dict[str, int]:
        """Run TTL expiry and capacity enforcement for all stores.

        Returns:
            Dict mapping policy name to the total number of records removed.
        """
        with self._lock:
            names = list(self._stores.keys())

        removed: Dict[str, int] = {}
        for name in names:
            with self._lock:
                store = self._stores.get(name)
            if store is None:
                continue
            expired = store.purge_expired()
            trimmed = store.enforce_capacity()
            removed[name] = len(expired) + len(trimmed)

        with self._lock:
            self._cleanup_count += 1

        return removed

    def cleanup_count(self) -> int:
        """Return cumulative number of cleanup runs."""
        with self._lock:
            return self._cleanup_count

    def clear_store(self, policy_name: str) -> None:
        """Remove all records from a named store."""
        with self._lock:
            store = self._stores.get(policy_name)
        if store:
            store.clear()
