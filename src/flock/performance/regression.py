"""Performance Regression Detection & Baseline Management."""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from flock.performance.models import (
    PerformanceBaseline,
    RegressionResult,
    RegressionThreshold,
    PerformanceTrend,
    BenchmarkResult,
)
from flock.performance.registry import PerformanceRegistry


class PerformanceRegressionEngine:
    """Detects performance regressions and handles baseline management."""

    def __init__(self, registry: PerformanceRegistry) -> None:
        self._registry = registry

    def create_baseline(self, name: str, result: BenchmarkResult) -> PerformanceBaseline:
        """Create and register a performance baseline from a benchmark result."""
        baseline = PerformanceBaseline(
            name=name,
            target_mean_duration_ms=result.mean_duration_ms,
            target_throughput=result.throughput,
            timestamp=time.time(),
        )
        self._registry.register_baseline(baseline)
        return baseline

    def update_baseline(self, name: str, result: BenchmarkResult) -> PerformanceBaseline:
        """Update and register a new baseline from a benchmark result."""
        return self.create_baseline(name, result)

    def compare_against_baseline(
        self,
        result: BenchmarkResult,
        threshold: RegressionThreshold = RegressionThreshold(),
    ) -> RegressionResult:
        """Compare a benchmark result against a registered baseline."""
        baseline = self._registry.get_baseline(result.name)
        if not baseline:
            raise ValueError(f"No baseline found for benchmark '{result.name}'")

        # Calculations
        latency_diff = result.mean_duration_ms - baseline.target_mean_duration_ms
        latency_change_pct = (latency_diff / baseline.target_mean_duration_ms) * 100.0

        throughput_diff = result.throughput - baseline.target_throughput
        throughput_change_pct = (throughput_diff / baseline.target_throughput) * 100.0

        # Evaluate thresholds
        status = "PASSED"
        msg = "Performance matches the target baseline."

        latency_exceeded = latency_change_pct > threshold.latency_increase_percent_limit
        throughput_exceeded = (
            throughput_change_pct < -threshold.throughput_degradation_percent_limit
        )

        if latency_exceeded or throughput_exceeded:
            status = "FAILED"
            msg = f"Performance regression detected: Latency +{latency_change_pct:.1f}%, Throughput {throughput_change_pct:.1f}%"
        elif latency_change_pct > 0 or throughput_change_pct < 0:
            status = "WARNING"
            msg = "Performance is slightly degraded but within limits."

        return RegressionResult(
            name=result.name,
            status=status,
            latency_change_percent=latency_change_pct,
            throughput_change_percent=throughput_change_pct,
            message=msg,
        )

    def get_performance_trends(self, name: str) -> PerformanceTrend:
        """Aggregate history to calculate whether performance is improving, stable, or degrading."""
        results = self._registry.get_results(name)
        if len(results) < 2:
            return PerformanceTrend(name=name, direction="STABLE", history_count=len(results))

        sorted_results = sorted(results, key=lambda r: r.timestamp)
        mid = len(sorted_results) // 2
        first_half = sorted_results[:mid]
        second_half = sorted_results[mid:]

        first_mean = sum(r.mean_duration_ms for r in first_half) / len(first_half)
        second_mean = sum(r.mean_duration_ms for r in second_half) / len(second_half)

        diff_pct = ((second_mean - first_mean) / first_mean) * 100.0

        if diff_pct > 5.0:
            direction = "DEGRADING"
        elif diff_pct < -5.0:
            direction = "IMPROVING"
        else:
            direction = "STABLE"

        return PerformanceTrend(
            name=name,
            direction=direction,
            history_count=len(results),
        )
