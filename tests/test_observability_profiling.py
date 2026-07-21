"""Unit tests for ProfilingEngine – Phase 34."""

import time
import pytest

from flock.observability.profiling import ProfilingEngine, ProfilingSnapshot


def test_record_snapshot() -> None:
    engine = ProfilingEngine()
    snap = engine.record("query.execute", 25.5)
    assert snap.operation == "query.execute"
    assert snap.duration_ms == pytest.approx(25.5)


def test_summary_statistics() -> None:
    engine = ProfilingEngine()
    for ms in [10.0, 20.0, 30.0, 40.0, 50.0]:
        engine.record("api.request", ms)
    s = engine.summary("api.request")
    assert s["mean"] == pytest.approx(30.0)
    assert s["min"] == pytest.approx(10.0)
    assert s["max"] == pytest.approx(50.0)
    assert int(s["count"]) == 5


def test_summary_empty_returns_empty_dict() -> None:
    engine = ProfilingEngine()
    assert engine.summary("nonexistent") == {}


def test_context_manager_records_duration() -> None:
    engine = ProfilingEngine()
    with engine.profile("my_op"):
        time.sleep(0.01)
    s = engine.summary("my_op")
    assert s["count"] == 1.0
    assert s["mean"] > 0.0


def test_context_manager_records_even_on_exception() -> None:
    engine = ProfilingEngine()
    try:
        with engine.profile("failing_op"):
            raise RuntimeError("oops")
    except RuntimeError:
        pass
    s = engine.summary("failing_op")
    assert s["count"] == 1.0


def test_all_summaries() -> None:
    engine = ProfilingEngine()
    engine.record("op_a", 10.0)
    engine.record("op_b", 20.0)
    summaries = engine.all_summaries()
    assert "op_a" in summaries
    assert "op_b" in summaries


def test_hotspots_sorted_by_mean_desc() -> None:
    engine = ProfilingEngine()
    engine.record("fast_op", 5.0)
    engine.record("slow_op", 100.0)
    hot = engine.hotspots(top_n=2)
    assert hot[0]["operation"] == "slow_op"


def test_get_snapshots() -> None:
    engine = ProfilingEngine()
    for ms in [1.0, 2.0, 3.0]:
        engine.record("op", ms)
    snaps = engine.get_snapshots("op", limit=2)
    assert len(snaps) == 2


def test_list_operations() -> None:
    engine = ProfilingEngine()
    engine.record("a", 1.0)
    engine.record("b", 2.0)
    assert "a" in engine.list_operations()
    assert "b" in engine.list_operations()


def test_total_recorded() -> None:
    engine = ProfilingEngine()
    engine.record("op", 1.0)
    engine.record("op", 2.0)
    assert engine.total_recorded == 2


def test_clear_specific_operation() -> None:
    engine = ProfilingEngine()
    engine.record("x", 1.0)
    engine.record("y", 2.0)
    engine.clear("x")
    assert engine.summary("x") == {}
    assert engine.summary("y") != {}


def test_clear_all() -> None:
    engine = ProfilingEngine()
    engine.record("x", 1.0)
    engine.record("y", 2.0)
    engine.clear()
    assert engine.list_operations() == []


def test_max_per_operation_bound() -> None:
    engine = ProfilingEngine(max_per_operation=3)
    for ms in range(10):
        engine.record("bounded", float(ms))
    snaps = engine.get_snapshots("bounded", limit=100)
    assert len(snaps) <= 3


def test_snapshot_to_dict() -> None:
    snap = ProfilingSnapshot(
        operation="test",
        duration_ms=12.5,
        timestamp=1000.0,
        metadata={"context": "unit"},
    )
    d = snap.to_dict()
    assert d["operation"] == "test"
    assert d["duration_ms"] == 12.5
    assert d["metadata"]["context"] == "unit"


def test_metadata_attached() -> None:
    engine = ProfilingEngine()
    snap = engine.record("meta_op", 5.0, metadata={"phase": "34"})
    assert snap.metadata["phase"] == "34"
