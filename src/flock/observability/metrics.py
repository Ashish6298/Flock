"""Metrics Engine – Phase 34.

Provides an extended metrics engine that builds on the existing
:class:`~flock.observability.registry.MetricsRegistry` from Phase 16.
Adds moving averages, throughput calculations, latency distributions,
percentile summaries, rolling-window aggregates, and cluster-wide
metric views without breaking existing API contracts.
"""

from __future__ import annotations

import statistics
import threading
import time
from collections import deque
from typing import Deque, Dict, List, Optional, Tuple


class MovingAverage:
    """Thread-safe exponential moving average calculator.

    Attributes:
        _alpha: Smoothing factor in ``(0, 1]``.
        _value: Current EMA value.
        _lock: Protects ``_value``.
    """

    def __init__(self, alpha: float = 0.1) -> None:
        """Initialise.

        Args:
            alpha: Smoothing factor.  Smaller values give more weight to
                historical data; larger values react faster to changes.
        """
        if not 0.0 < alpha <= 1.0:
            raise ValueError("alpha must be in (0, 1]")
        self._alpha: float = alpha
        self._value: Optional[float] = None
        self._lock: threading.Lock = threading.Lock()

    def update(self, value: float) -> float:
        """Update the EMA with a new observation.

        Args:
            value: Latest observation.

        Returns:
            Updated EMA value.
        """
        with self._lock:
            if self._value is None:
                self._value = value
            else:
                self._value = self._alpha * value + (1.0 - self._alpha) * self._value
            return self._value

    @property
    def value(self) -> float:
        """Current EMA value (``0.0`` if no observations yet)."""
        with self._lock:
            return self._value if self._value is not None else 0.0


class RollingWindow:
    """Thread-safe fixed-size ring buffer for rolling-window statistics.

    Attributes:
        _maxlen: Maximum number of samples retained.
        _samples: Deque holding the samples.
        _lock: Protects ``_samples``.
    """

    def __init__(self, maxlen: int = 100) -> None:
        """Initialise.

        Args:
            maxlen: Maximum number of samples in the window.
        """
        self._maxlen: int = maxlen
        self._samples: Deque[Tuple[float, float]] = deque(maxlen=maxlen)
        self._lock: threading.Lock = threading.Lock()

    def record(self, value: float) -> None:
        """Add a sample to the window.

        Args:
            value: Numeric observation.
        """
        with self._lock:
            self._samples.append((time.time(), value))

    def values(self) -> List[float]:
        """Return a snapshot of all values in the window."""
        with self._lock:
            return [v for _, v in self._samples]

    def mean(self) -> float:
        """Return the mean of the current window."""
        vals = self.values()
        return statistics.mean(vals) if vals else 0.0

    def stddev(self) -> float:
        """Return the population standard deviation of the window."""
        vals = self.values()
        return statistics.pstdev(vals) if len(vals) > 1 else 0.0

    def percentile(self, p: float) -> float:
        """Return the *p*-th percentile of the current window.

        Args:
            p: Percentile in ``[0, 100]``.

        Returns:
            Percentile value.
        """
        vals = sorted(self.values())
        if not vals:
            return 0.0
        idx = max(0, int(len(vals) * p / 100.0) - 1)
        return vals[min(idx, len(vals) - 1)]

    def count(self) -> int:
        """Return the current number of samples in the window."""
        with self._lock:
            return len(self._samples)

    def clear(self) -> None:
        """Remove all samples from the window."""
        with self._lock:
            self._samples.clear()


class ThroughputCounter:
    """Counts events per second over a sliding window.

    Attributes:
        _window_seconds: Duration of the sliding window.
        _events: Deque of event timestamps.
        _lock: Protects ``_events``.
    """

    def __init__(self, window_seconds: float = 60.0) -> None:
        """Initialise.

        Args:
            window_seconds: Size of the sliding window in seconds.
        """
        self._window_seconds: float = window_seconds
        self._events: Deque[float] = deque()
        self._lock: threading.Lock = threading.Lock()

    def record(self, count: int = 1) -> None:
        """Record one or more events at the current timestamp.

        Args:
            count: Number of events to record.
        """
        now = time.time()
        with self._lock:
            for _ in range(count):
                self._events.append(now)

    def rate(self) -> float:
        """Return events per second over the sliding window.

        Returns:
            Rate in events/second.  ``0.0`` if no events in window.
        """
        now = time.time()
        cutoff = now - self._window_seconds
        with self._lock:
            while self._events and self._events[0] < cutoff:
                self._events.popleft()
            count = len(self._events)
        return count / self._window_seconds if self._window_seconds > 0 else 0.0

    def total(self) -> int:
        """Return the total number of events still in the window."""
        now = time.time()
        cutoff = now - self._window_seconds
        with self._lock:
            while self._events and self._events[0] < cutoff:
                self._events.popleft()
            return len(self._events)

    def reset(self) -> None:
        """Clear all recorded events."""
        with self._lock:
            self._events.clear()


class LatencyTracker:
    """Records and summarises operation latencies.

    Combines a :class:`RollingWindow` for recent latencies with
    counters for p50, p90, p95, and p99 percentiles.

    Attributes:
        _window: Rolling sample buffer.
        _total_count: Total number of observations recorded.
        _lock: Protects ``_total_count``.
    """

    def __init__(self, maxlen: int = 1000) -> None:
        """Initialise.

        Args:
            maxlen: Rolling window capacity.
        """
        self._window: RollingWindow = RollingWindow(maxlen=maxlen)
        self._total_count: int = 0
        self._lock: threading.Lock = threading.Lock()

    def record(self, latency_ms: float) -> None:
        """Record a latency observation in milliseconds.

        Args:
            latency_ms: Latency in milliseconds.
        """
        self._window.record(latency_ms)
        with self._lock:
            self._total_count += 1

    def summary(self) -> Dict[str, float]:
        """Return a percentile summary of recorded latencies.

        Returns:
            Dict with keys ``mean``, ``p50``, ``p90``, ``p95``, ``p99``,
            ``min``, ``max``, and ``count``.
        """
        vals = sorted(self._window.values())
        if not vals:
            return {
                "mean": 0.0, "p50": 0.0, "p90": 0.0,
                "p95": 0.0, "p99": 0.0, "min": 0.0, "max": 0.0,
                "count": 0.0,
            }
        n = len(vals)
        return {
            "mean": statistics.mean(vals),
            "p50": vals[int(n * 0.50)],
            "p90": vals[int(n * 0.90)],
            "p95": vals[int(n * 0.95)],
            "p99": vals[min(int(n * 0.99), n - 1)],
            "min": vals[0],
            "max": vals[-1],
            "count": float(n),
        }

    def total_count(self) -> int:
        """Return total observations since creation."""
        with self._lock:
            return self._total_count

    def clear(self) -> None:
        """Clear rolling window (total_count is preserved)."""
        self._window.clear()


class MetricsEngine:
    """Extended metrics engine providing per-named metric instruments.

    Combines :class:`MovingAverage`, :class:`RollingWindow`,
    :class:`ThroughputCounter`, and :class:`LatencyTracker` instances
    under named keys so callers can record and query rich metric
    semantics without managing individual tracker instances.

    Attributes:
        _lock: Protects all dict stores.
        _averages: Named EMA trackers.
        _windows: Named rolling windows.
        _throughputs: Named throughput counters.
        _latencies: Named latency trackers.
    """

    def __init__(self) -> None:
        """Initialise an empty metrics engine."""
        self._lock: threading.RLock = threading.RLock()
        self._averages: Dict[str, MovingAverage] = {}
        self._windows: Dict[str, RollingWindow] = {}
        self._throughputs: Dict[str, ThroughputCounter] = {}
        self._latencies: Dict[str, LatencyTracker] = {}

    # ------------------------------------------------------------------
    # EMA
    # ------------------------------------------------------------------

    def update_ema(self, name: str, value: float, alpha: float = 0.1) -> float:
        """Update the exponential moving average for a named metric.

        Args:
            name: Metric name.
            value: New observation.
            alpha: Smoothing factor (used only on first registration).

        Returns:
            Updated EMA value.
        """
        with self._lock:
            if name not in self._averages:
                self._averages[name] = MovingAverage(alpha=alpha)
        return self._averages[name].update(value)

    def get_ema(self, name: str) -> float:
        """Return current EMA for a metric or ``0.0``."""
        with self._lock:
            return self._averages[name].value if name in self._averages else 0.0

    # ------------------------------------------------------------------
    # Rolling window
    # ------------------------------------------------------------------

    def record_window(
        self, name: str, value: float, maxlen: int = 100
    ) -> None:
        """Record a value in a named rolling window.

        Args:
            name: Window name.
            value: Observation.
            maxlen: Capacity (used only on first registration).
        """
        with self._lock:
            if name not in self._windows:
                self._windows[name] = RollingWindow(maxlen=maxlen)
        self._windows[name].record(value)

    def window_summary(self, name: str) -> Dict[str, float]:
        """Return statistics for a named rolling window."""
        with self._lock:
            w = self._windows.get(name)
        if w is None:
            return {"mean": 0.0, "stddev": 0.0, "count": 0.0}
        return {
            "mean": w.mean(),
            "stddev": w.stddev(),
            "p95": w.percentile(95.0),
            "count": float(w.count()),
        }

    # ------------------------------------------------------------------
    # Throughput
    # ------------------------------------------------------------------

    def record_event(
        self,
        name: str,
        count: int = 1,
        window_seconds: float = 60.0,
    ) -> None:
        """Record one or more events in a named throughput counter.

        Args:
            name: Counter name.
            count: Number of events.
            window_seconds: Sliding window duration (first registration).
        """
        with self._lock:
            if name not in self._throughputs:
                self._throughputs[name] = ThroughputCounter(window_seconds)
        self._throughputs[name].record(count)

    def get_rate(self, name: str) -> float:
        """Return events/second for a named throughput counter."""
        with self._lock:
            c = self._throughputs.get(name)
        return c.rate() if c is not None else 0.0

    # ------------------------------------------------------------------
    # Latency
    # ------------------------------------------------------------------

    def record_latency(
        self, name: str, latency_ms: float, maxlen: int = 1000
    ) -> None:
        """Record a latency measurement in a named tracker.

        Args:
            name: Tracker name.
            latency_ms: Latency in milliseconds.
            maxlen: Rolling window capacity (first registration).
        """
        with self._lock:
            if name not in self._latencies:
                self._latencies[name] = LatencyTracker(maxlen=maxlen)
        self._latencies[name].record(latency_ms)

    def latency_summary(self, name: str) -> Dict[str, float]:
        """Return percentile summary for a named latency tracker."""
        with self._lock:
            lt = self._latencies.get(name)
        return lt.summary() if lt is not None else {}

    # ------------------------------------------------------------------
    # Bulk snapshot
    # ------------------------------------------------------------------

    def snapshot(self) -> Dict[str, Dict[str, float]]:
        """Return a flat snapshot of all tracked metric summaries.

        Returns:
            Dict mapping metric names to their summary dicts.
        """
        result: Dict[str, Dict[str, float]] = {}
        with self._lock:
            ema_names = list(self._averages.keys())
            win_names = list(self._windows.keys())
            thr_names = list(self._throughputs.keys())
            lat_names = list(self._latencies.keys())

        for n in ema_names:
            result[f"ema.{n}"] = {"value": self.get_ema(n)}
        for n in win_names:
            result[f"window.{n}"] = self.window_summary(n)
        for n in thr_names:
            result[f"rate.{n}"] = {"rate": self.get_rate(n)}
        for n in lat_names:
            result[f"latency.{n}"] = self.latency_summary(n)
        return result

    def clear_all(self) -> None:
        """Clear all tracked instruments."""
        with self._lock:
            self._averages.clear()
            self._windows.clear()
            self._throughputs.clear()
            self._latencies.clear()
