"""Cluster Intelligence Engine."""

from __future__ import annotations

from typing import Dict, List

from flock.ai.models import ClusterAnalysis


class ClusterIntelligenceEngine:
    """Aggregates telemetry records to analyze utilization status."""

    def __init__(self) -> None:
        pass

    def analyze_utilization(self, samples: List[Dict[str, float]]) -> ClusterAnalysis:
        """Calculate average values metrics."""
        if not samples:
            return ClusterAnalysis(metrics_map={})

        sums: Dict[str, float] = {}
        counts: Dict[str, int] = {}

        for sample in samples:
            for key, val in sample.items():
                sums[key] = sums.get(key, 0.0) + val
                counts[key] = counts.get(key, 0) + 1

        averages = {k: (sums[k] / counts[k]) for k in sums}
        return ClusterAnalysis(metrics_map=averages)
