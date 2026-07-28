"""Repeatable Benchmark Engine orchestrator."""

from __future__ import annotations

import math
import time
from typing import Any, Callable, List

from flock.performance.models import BenchmarkDefinition, BenchmarkResult


class BenchmarkEngine:
    """Benchmark engine running warmups and tracking standard dev latencies."""

    def execute_benchmark(
        self,
        definition: BenchmarkDefinition,
        workload: Callable[[], Any],
    ) -> BenchmarkResult:
        """Run warmups, run measured iterations, and aggregate duration bounds."""
        # Warmup
        for _ in range(definition.warmup_iterations):
            workload()

        durations: List[float] = []
        for _ in range(definition.measured_iterations):
            start = time.perf_counter()
            workload()
            durations.append((time.perf_counter() - start) * 1000.0)  # ms

        total = sum(durations)
        mean_dur = total / len(durations)
        min_dur = min(durations)
        max_dur = max(durations)

        # Standard Deviation
        variance = sum((x - mean_dur) ** 2 for x in durations) / len(durations)
        std_dev = math.sqrt(variance)

        # Throughput: operations per second (1000 ms / mean_dur)
        throughput = 1000.0 / mean_dur if mean_dur > 0 else 0.0

        return BenchmarkResult(
            name=definition.name,
            mean_duration_ms=mean_dur,
            min_duration_ms=min_dur,
            max_duration_ms=max_dur,
            std_dev_ms=std_dev,
            throughput=throughput,
        )
