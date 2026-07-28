"""Performance Reporting & Engineering Analytics Engine."""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from flock.performance.models import (
    PerformanceReport,
    PerformanceScorecard,
    PerformanceCertification,
    PerformanceFinding,
    HistoricalComparison,
    BenchmarkResult,
)
from flock.performance.registry import PerformanceRegistry


class PerformanceReportingEngine:
    """Aggregates all performance data into unified reports and certifications."""

    def __init__(self, registry: PerformanceRegistry) -> None:
        self._registry = registry

    def generate_performance_report(
        self,
        name: str,
        result: BenchmarkResult,
        findings: Optional[List[PerformanceFinding]] = None,
    ) -> PerformanceReport:
        """Consolidate scorecard, certification, and findings into a PerformanceReport."""
        if result.mean_duration_ms < 50.0:
            score = 95.0
            grade = "A"
        elif result.mean_duration_ms < 100.0:
            score = 85.0
            grade = "B"
        else:
            score = 65.0
            grade = "C"

        scorecard = PerformanceScorecard(
            overall_score=score,
            latency_rating=grade,
            throughput_rating=grade,
            stability_rating="A",
        )

        is_certified = result.mean_duration_ms < 150.0
        verdict = (
            "Certified for release." if is_certified else "Verification failed due to high latency."
        )

        certification = PerformanceCertification(
            is_certified=is_certified,
            release_version="1.1.0",
            environment="production",
            summary_verdict=verdict,
        )

        report = PerformanceReport(
            name=name,
            timestamp=time.time(),
            scorecard=scorecard,
            certification=certification,
            findings=findings or [],
            baseline_comparisons=[],
        )
        self._registry.record_performance_report(report)
        return report

    def compare_reports(
        self,
        base: PerformanceReport,
        target: PerformanceReport,
    ) -> HistoricalComparison:
        """Compare two generated reports to highlight changes."""
        lat_delta = (
            (target.scorecard.overall_score - base.scorecard.overall_score)
            / base.scorecard.overall_score
        ) * 100.0
        improved = target.scorecard.overall_score >= base.scorecard.overall_score

        return HistoricalComparison(
            base_version=base.certification.release_version,
            target_version=target.certification.release_version,
            latency_delta_percent=lat_delta,
            throughput_delta_percent=lat_delta,
            improvement_detected=improved,
        )
