"""Telemetry Collector – Phase 34.

Asynchronous collector that aggregates metric snapshots, log batches,
and trace batches from registered producer callables into a unified
telemetry batch.  Producers are named Python callables; the collector
invokes them on demand and stores the resulting snapshot for query.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Dict, List, Optional

from flock.observability.exceptions import CollectorError


# Type alias: a producer returns a plain dict snapshot.
ProducerCallable = Callable[[], Dict[str, Any]]


class TelemetryBatch:
    """Snapshot collected from all registered producers.

    Attributes:
        batch_id: Unique identifier.
        collected_at: Unix epoch timestamp of collection.
        snapshots: Mapping of producer name to its snapshot dict.
        errors: Mapping of producer name to error string on failure.
    """

    __slots__ = ("batch_id", "collected_at", "snapshots", "errors")

    def __init__(
        self,
        batch_id: str,
        collected_at: float,
        snapshots: Dict[str, Dict[str, Any]],
        errors: Dict[str, str],
    ) -> None:
        self.batch_id = batch_id
        self.collected_at = collected_at
        self.snapshots = snapshots
        self.errors = errors

    def success_count(self) -> int:
        """Return the number of successful producer snapshots."""
        return len(self.snapshots)

    def error_count(self) -> int:
        """Return the number of failed producer calls."""
        return len(self.errors)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the batch to a plain dict."""
        return {
            "batch_id": self.batch_id,
            "collected_at": self.collected_at,
            "snapshots": self.snapshots,
            "errors": self.errors,
        }


class TelemetryCollector:
    """Thread-safe registry and executor for telemetry producers.

    Producers are registered as named callables that return a
    ``Dict[str, Any]`` snapshot.  Calling :meth:`collect` invokes all
    producers, captures their output (or any exception), and returns a
    :class:`TelemetryBatch`.

    Attributes:
        _lock: Reentrant lock protecting the producer registry.
        _producers: Mapping of producer name to callable.
        _batches: Recent batch history (bounded to ``max_history``).
        _max_history: Maximum number of batches retained.
    """

    def __init__(self, max_history: int = 100) -> None:
        """Initialise the collector.

        Args:
            max_history: Maximum number of historical batches to retain.
        """
        import uuid
        self._uuid = uuid
        self._lock: threading.RLock = threading.RLock()
        self._producers: Dict[str, ProducerCallable] = {}
        self._batches: List[TelemetryBatch] = []
        self._max_history: int = max_history

    # ------------------------------------------------------------------
    # Producer registration
    # ------------------------------------------------------------------

    def register(self, name: str, producer: ProducerCallable) -> None:
        """Register a named telemetry producer.

        Args:
            name: Unique producer name.
            producer: Callable returning a snapshot dict.
        """
        with self._lock:
            self._producers[name] = producer

    def unregister(self, name: str) -> None:
        """Remove a registered producer.

        Args:
            name: Producer to remove.

        Raises:
            CollectorError: If ``name`` is not registered.
        """
        with self._lock:
            if name not in self._producers:
                raise CollectorError(
                    f"Producer '{name}' is not registered."
                )
            del self._producers[name]

    def exists(self, name: str) -> bool:
        """Return ``True`` if a producer is registered under ``name``."""
        with self._lock:
            return name in self._producers

    def list_producers(self) -> List[str]:
        """Return names of all registered producers."""
        with self._lock:
            return list(self._producers.keys())

    def count(self) -> int:
        """Return the number of registered producers."""
        with self._lock:
            return len(self._producers)

    # ------------------------------------------------------------------
    # Collection
    # ------------------------------------------------------------------

    def collect(self) -> TelemetryBatch:
        """Invoke all producers and return a :class:`TelemetryBatch`.

        Each producer is called; exceptions are captured into the
        ``errors`` dict rather than propagated.

        Returns:
            A new :class:`TelemetryBatch` with all producer outputs.
        """
        with self._lock:
            producers = dict(self._producers)

        snapshots: Dict[str, Dict[str, Any]] = {}
        errors: Dict[str, str] = {}

        for name, producer in producers.items():
            try:
                snapshots[name] = producer()
            except Exception as exc:
                errors[name] = str(exc)

        batch = TelemetryBatch(
            batch_id=str(self._uuid.uuid4()),
            collected_at=time.time(),
            snapshots=snapshots,
            errors=errors,
        )

        with self._lock:
            self._batches.append(batch)
            if len(self._batches) > self._max_history:
                self._batches = self._batches[-self._max_history:]

        return batch

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def latest_batch(self) -> Optional[TelemetryBatch]:
        """Return the most recently collected batch or ``None``."""
        with self._lock:
            return self._batches[-1] if self._batches else None

    def get_history(self, limit: int = 10) -> List[TelemetryBatch]:
        """Return up to ``limit`` most recent batches.

        Args:
            limit: Maximum number of batches to return.

        Returns:
            List of :class:`TelemetryBatch` instances (newest last).
        """
        with self._lock:
            return list(self._batches[-limit:])

    def clear_history(self) -> None:
        """Remove all stored batch history."""
        with self._lock:
            self._batches.clear()

    def batch_count(self) -> int:
        """Return the number of batches in history."""
        with self._lock:
            return len(self._batches)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def clear_producers(self) -> None:
        """Remove all registered producers."""
        with self._lock:
            self._producers.clear()
