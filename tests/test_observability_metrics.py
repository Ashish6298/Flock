"""Unit tests for MetricsEngine – Phase 34."""

import time
import pytest

from flock.observability.metrics import (
    MetricsEngine,
    MovingAverage,
    RollingWindow,
    ThroughputCounter,
    LatencyTracker,
)


# ------------------------------------------------------------------
# MovingAverage
# ------------------------------------------------------------------

def test_ema_initial_value_is_first_observation() -> None:
    ema = MovingAverage(alpha=0.5)
    result = ema.update(10.0)
    assert result == 10.0


def test_ema_smooths_values() -> None:
    ema = MovingAverage(alpha=0.5)
    ema.update(0.0)
    result = ema.update(10.0)
    assert result == pytest.approx(5.0)


def test_ema_invalid_alpha_raises() -> None:
    with pytest.raises(ValueError):
        MovingAverage(alpha=0.0)


def test_ema_value_property_returns_zero_before_update() -> None:
    ema = MovingAverage()
    assert ema.value == 0.0


# ------------------------------------------------------------------
# RollingWindow
# ------------------------------------------------------------------

def test_rolling_window_mean() -> None:
    w = RollingWindow(maxlen=5)
    for v in [1.0, 2.0, 3.0, 4.0, 5.0]:
        w.record(v)
    assert w.mean() == pytest.approx(3.0)


def test_rolling_window_evicts_oldest() -> None:
    w = RollingWindow(maxlen=3)
    for v in [1.0, 2.0, 3.0, 100.0]:
        w.record(v)
    assert 1.0 not in w.values()


def test_rolling_window_percentile() -> None:
    w = RollingWindow(maxlen=10)
    for v in range(1, 11):
        w.record(float(v))
    assert w.percentile(50) >= 5.0


def test_rolling_window_empty_returns_zero() -> None:
    w = RollingWindow()
    assert w.mean() == 0.0
    assert w.stddev() == 0.0


def test_rolling_window_clear() -> None:
    w = RollingWindow()
    w.record(42.0)
    w.clear()
    assert w.count() == 0


# ------------------------------------------------------------------
# ThroughputCounter
# ------------------------------------------------------------------

def test_throughput_counter_rate() -> None:
    tc = ThroughputCounter(window_seconds=60.0)
    tc.record(10)
    rate = tc.rate()
    assert rate > 0.0


def test_throughput_counter_reset() -> None:
    tc = ThroughputCounter()
    tc.record(5)
    tc.reset()
    assert tc.total() == 0


# ------------------------------------------------------------------
# LatencyTracker
# ------------------------------------------------------------------

def test_latency_tracker_summary() -> None:
    lt = LatencyTracker()
    for ms in [10.0, 20.0, 30.0, 40.0, 50.0]:
        lt.record(ms)
    s = lt.summary()
    assert s["mean"] == pytest.approx(30.0)
    assert s["min"] == pytest.approx(10.0)
    assert s["max"] == pytest.approx(50.0)
    assert int(s["count"]) == 5


def test_latency_tracker_total_count() -> None:
    lt = LatencyTracker()
    lt.record(1.0)
    lt.record(2.0)
    assert lt.total_count() == 2


def test_latency_tracker_empty_summary() -> None:
    lt = LatencyTracker()
    s = lt.summary()
    assert s["count"] == 0.0


# ------------------------------------------------------------------
# MetricsEngine
# ------------------------------------------------------------------

def test_engine_ema() -> None:
    engine = MetricsEngine()
    engine.update_ema("cpu", 50.0)
    assert engine.get_ema("cpu") == 50.0


def test_engine_window_summary() -> None:
    engine = MetricsEngine()
    engine.record_window("rps", 100.0)
    engine.record_window("rps", 200.0)
    s = engine.window_summary("rps")
    assert s["count"] == 2.0


def test_engine_throughput_rate() -> None:
    engine = MetricsEngine()
    engine.record_event("requests", 5)
    assert engine.get_rate("requests") > 0.0


def test_engine_latency_summary() -> None:
    engine = MetricsEngine()
    for ms in [10.0, 20.0, 30.0]:
        engine.record_latency("api", ms)
    s = engine.latency_summary("api")
    assert s["mean"] == pytest.approx(20.0)


def test_engine_snapshot() -> None:
    engine = MetricsEngine()
    engine.update_ema("x", 1.0)
    snap = engine.snapshot()
    assert "ema.x" in snap


def test_engine_clear_all() -> None:
    engine = MetricsEngine()
    engine.update_ema("y", 5.0)
    engine.clear_all()
    assert engine.get_ema("y") == 0.0


def test_engine_missing_window_summary() -> None:
    engine = MetricsEngine()
    s = engine.window_summary("nonexistent")
    assert s["count"] == 0.0


def test_engine_missing_rate() -> None:
    engine = MetricsEngine()
    assert engine.get_rate("nothing") == 0.0
