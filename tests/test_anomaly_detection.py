"""Unit tests for AnomalyDetectionEngine."""

import pytest
from flock.ai.anomaly import AnomalyDetectionEngine
from flock.ai.exceptions import AnomalyDetectionError


def test_anomaly_detection_ranges() -> None:
    engine = AnomalyDetectionEngine()

    # Metric exceeding threshold yields report
    report = engine.check_metric("cpu_load", 0.95, 0.8)
    assert report is not None
    assert report.metric_name == "cpu_load"

    # Metric within bounds returns None
    assert engine.check_metric("cpu_load", 0.5, 0.8) is None


def test_anomaly_negative_threshold_raises() -> None:
    engine = AnomalyDetectionEngine()
    with pytest.raises(AnomalyDetectionError):
        engine.check_metric("cpu_load", 0.5, -1.0)
