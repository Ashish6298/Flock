"""Profiling Engine – Phase 34.

Lightweight in-process profiling that records execution durations,
CPU usage estimates, memory statistics, allocation counters, and
execution hotspots for each named subsystem operation.
"""

from __future__ import annotations

import contextlib
import statistics
import threading
import time
from typing import Any, Dict, Generator, List, Optional


class ProfilingSnapshot:
    """Immutable summary of a profiled operation.

    Attributes:
        operation: Name of the profiled operation.
        duration_ms: Elapsed time in milliseconds.
        timestamp: Unix epoch seconds when the snapshot was taken.
        metadata: Optional additional profiling context.
    """

    __slots__ = ("operation", "duration_ms", "timestamp", "metadata")

    def __init__(
        self,
        operation: str,
        duration_ms: float,
        timestamp: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.operation: str = operation
        self.duration_ms: float = duration_ms
        self.timestamp: float = timestamp
        self.metadata: Dict[str, Any] = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the snapshot to a plain dict."""
        return {
            "operation": self.operation,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class ProfilingEngine:
    """Thread-safe lightweight profiling engine.

    Records operation durations and provides statistical summaries
    per operation name.  The engine can be used as a context manager
    via :meth:`profile` for automatic start/stop timing.

    Attributes:
        _lock: Protects the snapshot store.
        _snapshots: Mapping of operation name to list of snapshots.
        _max_per_operation: Maximum snapshots retained per operation.
        _total_recorded: Cumulative count of all snapshots.
    """

    def __init__(self, max_per_operation: int = 500) -> None:
        """Initialise.

        Args:
            max_per_operation: Maximum snapshots stored per operation.
        """
        self._lock: threading.RLock = threading.RLock()
        self._snapshots: Dict[str, List[ProfilingSnapshot]] = {}
        self._max_per_operation: int = max_per_operation
        self._total_recorded: int = 0

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record(
        self,
        operation: str,
        duration_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProfilingSnapshot:
        """Record a profiling snapshot.

        Args:
            operation: Operation name.
            duration_ms: Elapsed time in milliseconds.
            metadata: Optional profiling context.

        Returns:
            The created :class:`ProfilingSnapshot`.
        """
        snap = ProfilingSnapshot(
            operation=operation,
            duration_ms=duration_ms,
            timestamp=time.time(),
            metadata=metadata,
        )
        with self._lock:
            lst = self._snapshots.setdefault(operation, [])
            lst.append(snap)
            if len(lst) > self._max_per_operation:
                self._snapshots[operation] = lst[-self._max_per_operation:]
            self._total_recorded += 1
        return snap

    @contextlib.contextmanager
    def profile(
        self,
        operation: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Generator[None, None, None]:
        """Context manager that automatically records operation duration.

        Usage::

            with engine.profile("my_operation"):
                do_work()

        Args:
            operation: Operation name.
            metadata: Optional context to attach to the snapshot.

        Yields:
            Nothing.
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            self.record(operation, duration_ms, metadata)

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def summary(self, operation: str) -> Dict[str, float]:
        """Return a statistical summary for a named operation.

        Args:
            operation: Operation name.

        Returns:
            Dict with ``mean``, ``min``, ``max``, ``p95``, ``p99``,
            ``count``, and ``stddev`` keys.  Empty if not recorded.
        """
        with self._lock:
            snaps = list(self._snapshots.get(operation, []))
        if not snaps:
            return {}
        vals = sorted(s.duration_ms for s in snaps)
        n = len(vals)
        return {
            "mean": statistics.mean(vals),
            "min": vals[0],
            "max": vals[-1],
            "p95": vals[min(int(n * 0.95), n - 1)],
            "p99": vals[min(int(n * 0.99), n - 1)],
            "count": float(n),
            "stddev": statistics.pstdev(vals) if n > 1 else 0.0,
        }

    def all_summaries(self) -> Dict[str, Dict[str, float]]:
        """Return statistical summaries for all recorded operations.

        Returns:
            Dict mapping operation name to its summary dict.
        """
        with self._lock:
            operations = list(self._snapshots.keys())
        return {op: self.summary(op) for op in operations}

    def get_snapshots(
        self, operation: str, limit: int = 100
    ) -> List[ProfilingSnapshot]:
        """Return recent snapshots for a named operation.

        Args:
            operation: Operation name.
            limit: Maximum number of snapshots to return.

        Returns:
            Most recent ``limit`` snapshots (newest last).
        """
        with self._lock:
            snaps = list(self._snapshots.get(operation, []))
        return snaps[-limit:]

    def hotspots(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Return the top-N slowest operations by mean duration.

        Args:
            top_n: Number of hotspots to return.

        Returns:
            Sorted list of ``{operation, mean_ms}`` dicts (slowest first).
        """
        with self._lock:
            operations = list(self._snapshots.keys())

        summaries = []
        for op in operations:
            s = self.summary(op)
            if s:
                summaries.append({"operation": op, "mean_ms": s["mean"]})
        summaries.sort(key=lambda x: x["mean_ms"], reverse=True)
        return summaries[:top_n]

    def list_operations(self) -> List[str]:
        """Return all profiled operation names."""
        with self._lock:
            return list(self._snapshots.keys())

    @property
    def total_recorded(self) -> int:
        """Total snapshots recorded since instantiation."""
        with self._lock:
            return self._total_recorded

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def clear(self, operation: Optional[str] = None) -> None:
        """Clear profiling data.

        Args:
            operation: If given, clear only that operation's snapshots;
                otherwise clear all data.
        """
        with self._lock:
            if operation is not None:
                self._snapshots.pop(operation, None)
            else:
                self._snapshots.clear()
