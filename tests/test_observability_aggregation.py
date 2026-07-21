"""Unit tests for AggregationEngine – Phase 34."""

import pytest

from flock.observability.aggregation import (
    AggregationEngine,
    AnomalyBaseline,
    TrendAnalyzer,
    WindowedAggregation,
)


# ------------------------------------------------------------------
# WindowedAggregation
# ------------------------------------------------------------------

def test_windowed_aggregation_summary() -> None:
    wa = WindowedAggregation(window_seconds=60.0)
    for v in [10.0, 20.0, 30.0]:
        wa.add(v)
    s = wa.summary()
    assert s["mean"] == pytest.approx(20.0)
    assert s["count"] == 3.0
    assert s["min"] == pytest.approx(10.0)
    assert s["max"] == pytest.approx(30.0)


def test_windowed_aggregation_empty_summary() -> None:
    wa = WindowedAggregation()
    s = wa.summary()
    assert s["count"] == 0.0


def test_windowed_aggregation_rate() -> None:
    wa = WindowedAggregation(window_seconds=60.0)
    wa.add(1.0)
    wa.add(2.0)
    rate = wa.rate_per_second()
    assert rate > 0.0


def test_windowed_aggregation_clear() -> None:
    wa = WindowedAggregation()
    wa.add(5.0)
    wa.clear()
    assert wa.values() == []


# ------------------------------------------------------------------
# AnomalyBaseline
# ------------------------------------------------------------------

def test_anomaly_baseline_not_anomalous_with_few_samples() -> None:
    ab = AnomalyBaseline()
    ab.observe(50.0)
    assert not ab.is_anomalous(51.0)


def test_anomaly_baseline_detects_outlier() -> None:
    ab = AnomalyBaseline(sigma_threshold=2.0)
    # Use slightly varying values so stddev > 0 (mean~50, stddev~2)
    import random
    rng = random.Random(42)
    for _ in range(30):
        ab.observe(50.0 + rng.gauss(0, 2))
    assert ab.is_anomalous(200.0)


def test_anomaly_baseline_normal_value_not_anomalous() -> None:
    ab = AnomalyBaseline(sigma_threshold=3.0)
    for _ in range(30):
        ab.observe(50.0)
    assert not ab.is_anomalous(50.5)


def test_anomaly_baseline_deviation_score() -> None:
    ab = AnomalyBaseline(sigma_threshold=3.0)
    import random
    rng = random.Random(42)
    for _ in range(30):
        ab.observe(50.0 + rng.gauss(0, 2))
    score = ab.deviation_score(200.0)
    assert score > 0.0


# ------------------------------------------------------------------
# TrendAnalyzer
# ------------------------------------------------------------------

def test_trend_analyzer_increasing() -> None:
    ta = TrendAnalyzer()
    for v in [1.0, 2.0, 3.0, 4.0, 5.0]:
        ta.record(v)
    assert ta.is_increasing()


def test_trend_analyzer_decreasing() -> None:
    ta = TrendAnalyzer()
    for v in [5.0, 4.0, 3.0, 2.0, 1.0]:
        ta.record(v)
    assert ta.is_decreasing()


def test_trend_analyzer_flat_slope() -> None:
    ta = TrendAnalyzer()
    assert ta.slope() == 0.0


# ------------------------------------------------------------------
# AggregationEngine
# ------------------------------------------------------------------

def test_aggregation_engine_observe_and_summary() -> None:
    engine = AggregationEngine()
    for v in [10.0, 20.0, 30.0]:
        engine.observe("cpu", v)
    s = engine.summary("cpu")
    assert s["mean"] == pytest.approx(20.0)
    assert s["latest"] == pytest.approx(30.0)


def test_aggregation_engine_list_metrics() -> None:
    engine = AggregationEngine()
    engine.observe("cpu", 50.0)
    engine.observe("mem", 40.0)
    names = engine.list_metrics()
    assert "cpu" in names and "mem" in names


def test_aggregation_engine_anomaly_detection() -> None:
    engine = AggregationEngine()
    import random
    rng = random.Random(42)
    for _ in range(30):
        engine.observe("cpu", 50.0 + rng.gauss(0, 2))
    assert engine.is_anomalous("cpu", 999.0)
    assert not engine.is_anomalous("cpu", 50.5)


def test_aggregation_engine_unknown_metric_not_anomalous() -> None:
    engine = AggregationEngine()
    assert not engine.is_anomalous("unknown", 100.0)


def test_aggregation_engine_take_snapshot() -> None:
    engine = AggregationEngine()
    engine.observe("cpu", 75.0)
    snap = engine.take_snapshot()
    assert "metrics" in snap
    assert "cpu" in snap["metrics"]


def test_aggregation_engine_get_snapshots() -> None:
    engine = AggregationEngine(max_snapshots=3)
    for _ in range(5):
        engine.observe("x", 1.0)
        engine.take_snapshot()
    snaps = engine.get_snapshots(limit=10)
    assert len(snaps) == 3


def test_aggregation_engine_clear() -> None:
    engine = AggregationEngine()
    engine.observe("cpu", 50.0)
    engine.take_snapshot()
    engine.clear()
    assert engine.list_metrics() == []
    assert engine.get_snapshots() == []


def test_aggregation_engine_empty_summary() -> None:
    engine = AggregationEngine()
    assert engine.summary("nonexistent") == {}
