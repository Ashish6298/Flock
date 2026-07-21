"""Aggregation Engine – Phase 34.

Provides rolling-window statistical summaries, anomaly baselines,
trend analysis, rate calculations, and historical snapshots for
telemetry data accumulated from the metrics registry and the
extended :class:`~flock.observability.metrics.MetricsEngine`.
"""

from __future__ import annotations

import statistics
import threading
import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional, Tuple


class WindowedAggregation:
    """Accumulates numeric samples in a time-bounded sliding window.

    Attributes:
        _window_seconds: Retention duration in seconds.
        _samples: Deque of ``(timestamp, value)`` tuples.
        _lock: Protects ``_samples``.
    """

    def __init__(self, window_seconds: float = 300.0) -> None:
        """Initialise.

        Args:
            window_seconds: Sliding window duration.
        """
        self._window_seconds: float = window_seconds
        self._samples: Deque[Tuple[float, float]] = deque()
        self._lock: threading.Lock = threading.Lock()

    def _purge_old(self, now: float) -> None:
        """Remove samples older than the window boundary."""
        cutoff = now - self._window_seconds
        while self._samples and self._samples[0][0] < cutoff:
            self._samples.popleft()

    def add(self, value: float) -> None:
        """Add a new sample with the current timestamp."""
        now = time.time()
        with self._lock:
            self._purge_old(now)
            self._samples.append((now, value))

    def values(self) -> List[float]:
        """Return a snapshot of values in the current window."""
        now = time.time()
        with self._lock:
            self._purge_old(now)
            return [v for _, v in self._samples]

    def summary(self) -> Dict[str, float]:
        """Return mean, stddev, min, max, count for the window."""
        vals = self.values()
        if not vals:
            return {
                "mean": 0.0, "stddev": 0.0,
                "min": 0.0, "max": 0.0, "count": 0.0,
            }
        return {
            "mean": statistics.mean(vals),
            "stddev": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
            "min": min(vals),
            "max": max(vals),
            "count": float(len(vals)),
        }

    def rate_per_second(self) -> float:
        """Return the sample ingestion rate within the window."""
        vals = self.values()
        return len(vals) / self._window_seconds if self._window_seconds > 0 else 0.0

    def clear(self) -> None:
        """Remove all samples."""
        with self._lock:
            self._samples.clear()


class AnomalyBaseline:
    """Computes a rolling mean+stddev baseline for anomaly detection.

    A value is considered anomalous when it deviates more than
    ``sigma_threshold`` standard deviations from the rolling mean.

    Attributes:
        _baseline: Underlying :class:`WindowedAggregation`.
        _sigma: Anomaly threshold in standard deviations.
    """

    def __init__(
        self, window_seconds: float = 300.0, sigma_threshold: float = 3.0
    ) -> None:
        """Initialise.

        Args:
            window_seconds: Baseline window duration.
            sigma_threshold: Number of standard deviations for anomaly.
        """
        self._baseline: WindowedAggregation = WindowedAggregation(
            window_seconds=window_seconds
        )
        self._sigma: float = sigma_threshold

    def observe(self, value: float) -> None:
        """Add a value to the baseline."""
        self._baseline.add(value)

    def is_anomalous(self, value: float) -> bool:
        """Return ``True`` if ``value`` is anomalous given the baseline.

        Args:
            value: Value to evaluate.

        Returns:
            ``True`` if the value is more than ``sigma_threshold``
            standard deviations from the rolling mean.
        """
        s = self._baseline.summary()
        if s["count"] < 2.0:
            return False
        mean = s["mean"]
        stddev = s["stddev"]
        if stddev == 0.0:
            return False
        return abs(value - mean) > self._sigma * stddev

    def deviation_score(self, value: float) -> float:
        """Return the z-score of ``value`` against the baseline.

        Args:
            value: Value to score.

        Returns:
            Z-score (signed deviation in standard deviations), or
            ``0.0`` if baseline has fewer than 2 samples.
        """
        s = self._baseline.summary()
        if s["count"] < 2.0 or s["stddev"] == 0.0:
            return 0.0
        return (value - s["mean"]) / s["stddev"]


class TrendAnalyzer:
    """Detects increasing or decreasing trends in a value series.

    Uses a simple linear regression slope over the most recent samples.

    Attributes:
        _window: Sliding sample window.
    """

    def __init__(self, window_seconds: float = 300.0) -> None:
        self._window: WindowedAggregation = WindowedAggregation(window_seconds)

    def record(self, value: float) -> None:
        """Add a sample."""
        self._window.add(value)

    def slope(self) -> float:
        """Return the linear regression slope of the current window.

        A positive slope indicates an increasing trend; negative indicates
        a decreasing trend.

        Returns:
            Slope value, or ``0.0`` if fewer than 2 samples are available.
        """
        vals = self._window.values()
        n = len(vals)
        if n < 2:
            return 0.0
        xs = list(range(n))
        x_mean = statistics.mean(xs)
        y_mean = statistics.mean(vals)
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, vals))
        denominator = sum((x - x_mean) ** 2 for x in xs)
        return numerator / denominator if denominator != 0 else 0.0

    def is_increasing(self, threshold: float = 0.01) -> bool:
        """Return ``True`` if the slope is above ``threshold``."""
        return self.slope() > threshold

    def is_decreasing(self, threshold: float = 0.01) -> bool:
        """Return ``True`` if the slope is below ``-threshold``."""
        return self.slope() < -threshold


class AggregationEngine:
    """Per-metric aggregation registry combining windowed stats and anomaly detection.

    Attributes:
        _lock: Protects all inner stores.
        _windows: Named :class:`WindowedAggregation` instances.
        _baselines: Named :class:`AnomalyBaseline` instances.
        _trends: Named :class:`TrendAnalyzer` instances.
        _snapshots: Historical snapshots list.
        _max_snapshots: Bound on snapshot history.
    """

    def __init__(
        self,
        window_seconds: float = 300.0,
        max_snapshots: int = 50,
    ) -> None:
        """Initialise.

        Args:
            window_seconds: Default sliding window duration.
            max_snapshots: Maximum historical snapshots retained.
        """
        self._window_seconds: float = window_seconds
        self._lock: threading.RLock = threading.RLock()
        self._windows: Dict[str, WindowedAggregation] = {}
        self._baselines: Dict[str, AnomalyBaseline] = {}
        self._trends: Dict[str, TrendAnalyzer] = {}
        self._snapshots: List[Dict[str, Any]] = []
        self._max_snapshots: int = max_snapshots

    # ------------------------------------------------------------------
    # Observation
    # ------------------------------------------------------------------

    def observe(self, name: str, value: float) -> None:
        """Record a new observation for a named metric.

        Registers the metric automatically on first observation.

        Args:
            name: Metric name.
            value: Numeric observation.
        """
        with self._lock:
            if name not in self._windows:
                self._windows[name] = WindowedAggregation(self._window_seconds)
                self._baselines[name] = AnomalyBaseline(self._window_seconds)
                self._trends[name] = TrendAnalyzer(self._window_seconds)
            w = self._windows[name]
            b = self._baselines[name]
            tr = self._trends[name]

        w.add(value)
        b.observe(value)
        tr.record(value)

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def summary(self, name: str) -> Dict[str, Any]:
        """Return a full statistical summary for a named metric.

        Args:
            name: Metric name.

        Returns:
            Dict with windowed stats, anomaly flag, z-score, and slope.
        """
        with self._lock:
            w = self._windows.get(name)
            b = self._baselines.get(name)
            tr = self._trends.get(name)

        if w is None:
            return {}

        vals = w.values()
        latest = vals[-1] if vals else 0.0
        s = w.summary()
        return {
            **s,
            "latest": latest,
            "rate_per_second": w.rate_per_second(),
            "is_anomalous": b.is_anomalous(latest) if b else False,
            "deviation_score": b.deviation_score(latest) if b else 0.0,
            "trend_slope": tr.slope() if tr else 0.0,
            "is_increasing": tr.is_increasing() if tr else False,
            "is_decreasing": tr.is_decreasing() if tr else False,
        }

    def list_metrics(self) -> List[str]:
        """Return names of all tracked metrics."""
        with self._lock:
            return list(self._windows.keys())

    def is_anomalous(self, name: str, value: float) -> bool:
        """Test whether ``value`` is anomalous for the named metric.

        Args:
            name: Metric name.
            value: Value to evaluate.

        Returns:
            ``True`` if anomalous, ``False`` if not tracked or baseline too small.
        """
        with self._lock:
            b = self._baselines.get(name)
        return b.is_anomalous(value) if b else False

    # ------------------------------------------------------------------
    # Snapshot management
    # ------------------------------------------------------------------

    def take_snapshot(self) -> Dict[str, Any]:
        """Capture and store the current summary for all metrics.

        Returns:
            Snapshot dict keyed by metric name.
        """
        snapshot: Dict[str, Any] = {
            "captured_at": time.time(),
            "metrics": {
                name: self.summary(name) for name in self.list_metrics()
            },
        }
        with self._lock:
            self._snapshots.append(snapshot)
            if len(self._snapshots) > self._max_snapshots:
                self._snapshots = self._snapshots[-self._max_snapshots:]
        return snapshot

    def get_snapshots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return the most recent snapshots.

        Args:
            limit: Maximum number of snapshots.

        Returns:
            List of snapshot dicts (most recent last).
        """
        with self._lock:
            return list(self._snapshots[-limit:])

    def clear(self) -> None:
        """Clear all tracked metrics and snapshots."""
        with self._lock:
            self._windows.clear()
            self._baselines.clear()
            self._trends.clear()
            self._snapshots.clear()
