"""Performance Registry tracking historical benchmark runs."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from flock.performance.models import (
    BenchmarkDefinition,
    BenchmarkResult,
    ProfilingSession,
    PerformanceBaseline,
    OptimizationReport,
    MetricsSnapshot,
    MetricsAlert,
    PerformanceReport,
)


class PerformanceRegistry:
    """Thread-safe catalog repository index for executions statistics."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._benchmarks: Dict[str, BenchmarkDefinition] = {}
        self._results: Dict[str, List[BenchmarkResult]] = {}
        self._sessions: Dict[str, ProfilingSession] = {}
        self._baselines: Dict[str, PerformanceBaseline] = {}
        self._reports: Dict[str, OptimizationReport] = {}
        self._snapshots: List[MetricsSnapshot] = []
        self._alerts: List[MetricsAlert] = []
        self._perf_reports: Dict[str, PerformanceReport] = {}

    def register_benchmark(self, definition: BenchmarkDefinition) -> None:
        """Register benchmark definition."""
        with self._lock:
            self._benchmarks[definition.name] = definition
            if definition.name not in self._results:
                self._results[definition.name] = []

    def record_result(self, result: BenchmarkResult) -> None:
        """Record benchmark execution outputs snapshot."""
        with self._lock:
            self._results.setdefault(result.name, []).append(result)

    def get_results(self, name: str) -> List[BenchmarkResult]:
        """Fetch results history matching benchmark name."""
        with self._lock:
            return list(self._results.get(name, []))

    def record_session(self, session: ProfilingSession) -> None:
        """Record profiling session metrics."""
        with self._lock:
            self._sessions[session.session_id] = session

    def get_session(self, session_id: str) -> Optional[ProfilingSession]:
        """Fetch recorded profiling session by ID."""
        with self._lock:
            return self._sessions.get(session_id)

    def register_baseline(self, baseline: PerformanceBaseline) -> None:
        """Register a performance baseline."""
        with self._lock:
            self._baselines[baseline.name] = baseline

    def get_baseline(self, name: str) -> Optional[PerformanceBaseline]:
        """Fetch a registered performance baseline."""
        with self._lock:
            return self._baselines.get(name)

    def remove_baseline(self, name: str) -> None:
        """Remove a registered performance baseline."""
        with self._lock:
            self._baselines.pop(name, None)

    def record_optimization_report(self, report: OptimizationReport) -> None:
        """Record an optimization report."""
        with self._lock:
            self._reports[report.name] = report

    def get_optimization_report(self, name: str) -> Optional[OptimizationReport]:
        """Fetch an optimization report by name."""
        with self._lock:
            return self._reports.get(name)

    def record_metric_snapshot(self, snapshot: MetricsSnapshot) -> None:
        """Record a performance metrics snapshot."""
        with self._lock:
            self._snapshots.append(snapshot)

    def get_metric_snapshots(self) -> List[MetricsSnapshot]:
        """Fetch historical metrics snapshots."""
        with self._lock:
            return list(self._snapshots)

    def record_alert(self, alert: MetricsAlert) -> None:
        """Record a performance metrics alert."""
        with self._lock:
            self._alerts.append(alert)

    def get_alerts(self) -> List[MetricsAlert]:
        """Fetch historical performance alerts."""
        with self._lock:
            return list(self._alerts)

    def record_performance_report(self, report: PerformanceReport) -> None:
        """Record a consolidated performance report."""
        with self._lock:
            self._perf_reports[report.name] = report

    def get_performance_report(self, name: str) -> Optional[PerformanceReport]:
        """Fetch a consolidated performance report by name."""
        with self._lock:
            return self._perf_reports.get(name)

    def clear(self) -> None:
        """Purge all catalog mappings."""
        with self._lock:
            self._benchmarks.clear()
            self._results.clear()
            self._sessions.clear()
            self._baselines.clear()
            self._reports.clear()
            self._snapshots.clear()
            self._alerts.clear()
            self._perf_reports.clear()
