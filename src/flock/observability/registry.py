"""Metrics Registry implementation."""

from __future__ import annotations

import threading
import time
from typing import Dict, List, Optional

from flock.observability.exceptions import InvalidMetricError
from flock.observability.models import MetricType, MetricValue


class MetricsRegistry:
    """Thread-safe catalog managing counters, gauges, histograms, and timers."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # In-memory metrics stores: metric_key -> float or list values
        self._values: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._types: Dict[str, MetricType] = {}
        self._labels: Dict[str, Dict[str, str]] = {}

    def register(self, name: str, mtype: MetricType, labels: Optional[Dict[str, str]] = None) -> None:
        """Register a new metric name into the registry catalog."""
        with self._lock:
            if name in self._types:
                if self._types[name] != mtype:
                    raise InvalidMetricError(
                        f"Metric '{name}' already registered with type {self._types[name]} (requested: {mtype})."
                    )
                return

            self._types[name] = mtype
            self._labels[name] = labels or {}

            if mtype in (MetricType.COUNTER, MetricType.GAUGE):
                self._values[name] = 0.0
            elif mtype in (MetricType.HISTOGRAM, MetricType.SUMMARY, MetricType.TIMER):
                self._histograms[name] = []

    def increment(self, name: str, amount: float = 1.0) -> None:
        """Increment a counter value."""
        with self._lock:
            self._verify_type(name, MetricType.COUNTER)
            self._values[name] = self._values.get(name, 0.0) + amount

    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge value."""
        with self._lock:
            self._verify_type(name, MetricType.GAUGE)
            self._values[name] = value

    def observe(self, name: str, value: float) -> None:
        """Record value inside histogram or summary buckets."""
        with self._lock:
            if name not in self._types:
                # Auto-register histograms/timers
                self._types[name] = MetricType.HISTOGRAM
                self._histograms[name] = []
                self._labels[name] = {}
            
            mtype = self._types[name]
            if mtype not in (MetricType.HISTOGRAM, MetricType.SUMMARY, MetricType.TIMER):
                raise InvalidMetricError(f"Cannot observe value for metric '{name}' of type {mtype}.")
            
            self._histograms[name].append(value)

    def get_metric(self, name: str) -> Optional[MetricValue]:
        """Fetch current MetricValue record by name."""
        with self._lock:
            if name not in self._types:
                return None
            mtype = self._types[name]
            labels = self._labels.get(name, {})

            if mtype in (MetricType.COUNTER, MetricType.GAUGE):
                val = self._values.get(name, 0.0)
            else:
                # For histograms/timers, aggregate mean/average value
                hist = self._histograms.get(name, [])
                val = sum(hist) / len(hist) if hist else 0.0

            return MetricValue(
                name=name,
                type=mtype,
                value=val,
                labels=labels,
                timestamp=time.time(),
            )

    def list_metrics(self) -> List[MetricValue]:
        """Expose list of all active registered metric descriptors."""
        names = []
        with self._lock:
            names = list(self._types.keys())
        
        metrics = []
        for name in names:
            metric = self.get_metric(name)
            if metric:
                metrics.append(metric)
        return metrics

    def get_histogram_percentile(self, name: str, percentile: float) -> float:
        """Calculate percentile value for a registered histogram."""
        with self._lock:
            self._verify_type(name, MetricType.HISTOGRAM)
            hist = sorted(self._histograms.get(name, []))
            if not hist:
                return 0.0
            idx = int(len(hist) * (percentile / 100.0))
            idx = min(idx, len(hist) - 1)
            return hist[idx]

    def _verify_type(self, name: str, expected: MetricType) -> None:
        """Verify metric exists and conforms to type requirements."""
        if name not in self._types:
            # Auto-register
            self._types[name] = expected
            self._labels[name] = {}
            if expected in (MetricType.COUNTER, MetricType.GAUGE):
                self._values[name] = 0.0
            return
        
        mtype = self._types[name]
        if mtype != expected:
            raise InvalidMetricError(f"Metric '{name}' is of type {mtype} (expected: {expected}).")
