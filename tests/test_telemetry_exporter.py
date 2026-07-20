"""Unit tests for TelemetryExporter."""

import json
from flock.observability.exporter import TelemetryExporter
from flock.observability.models import MetricType, MetricValue


def test_exporter_prometheus_format() -> None:
    exporter = TelemetryExporter()
    metrics = [
        MetricValue(
            name="flock.consensus.commits",
            type=MetricType.COUNTER,
            value=42.0,
            labels={"node": "leader-1"},
            timestamp=0.0,
        )
    ]

    prom_text = exporter.export_prometheus(metrics)
    assert "# HELP flock_consensus_commits" in prom_text
    assert "# TYPE flock_consensus_commits counter" in prom_text
    assert 'flock_consensus_commits{node="leader-1"} 42.0' in prom_text


def test_exporter_json_format() -> None:
    exporter = TelemetryExporter()
    metrics = [
        MetricValue(
            name="test.gauge",
            type=MetricType.GAUGE,
            value=100.5,
            labels={},
            timestamp=0.0,
        )
    ]

    json_text = exporter.export_json(metrics)
    parsed = json.loads(json_text)
    assert len(parsed) == 1
    assert parsed[0]["name"] == "test.gauge"
    assert parsed[0]["value"] == 100.5
