"""Anomaly Detection Engine."""

from __future__ import annotations

from typing import Optional

from flock.ai.exceptions import AnomalyDetectionError
from flock.ai.models import AnomalyReport


class AnomalyDetectionEngine:
    """Evaluates telemetry parameters against threshold limits."""

    def __init__(self) -> None:
        pass

    def check_metric(self, name: str, value: float, threshold: float) -> Optional[AnomalyReport]:
        """Detect anomalies. Raise exception if metrics boundaries are negative.

        Raises:
            AnomalyDetectionError: If threshold value is negative.
        """
        if threshold < 0.0:
            raise AnomalyDetectionError("Anomaly threshold limit cannot be negative.")

        if value > threshold:
            return AnomalyReport(metric_name=name, value=value, threshold=threshold)
        return None
