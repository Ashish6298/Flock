"""Unit tests for TelemetryCollector – Phase 34."""

import pytest

from flock.observability.collector import TelemetryBatch, TelemetryCollector
from flock.observability.exceptions import CollectorError


def _good_producer() -> dict:  # type: ignore[type-arg]
    return {"cpu": 72.5, "memory": 48.0}


def _bad_producer() -> dict:  # type: ignore[type-arg]
    raise RuntimeError("disk failure")


def test_register_and_collect() -> None:
    col = TelemetryCollector()
    col.register("node", _good_producer)
    batch = col.collect()
    assert batch.success_count() == 1
    assert "node" in batch.snapshots
    assert batch.snapshots["node"]["cpu"] == 72.5


def test_collect_bad_producer_captured_in_errors() -> None:
    col = TelemetryCollector()
    col.register("bad", _bad_producer)
    batch = col.collect()
    assert batch.error_count() == 1
    assert "bad" in batch.errors


def test_collect_mixed() -> None:
    col = TelemetryCollector()
    col.register("good", _good_producer)
    col.register("bad", _bad_producer)
    batch = col.collect()
    assert batch.success_count() == 1
    assert batch.error_count() == 1


def test_unregister() -> None:
    col = TelemetryCollector()
    col.register("x", _good_producer)
    col.unregister("x")
    assert not col.exists("x")


def test_unregister_missing_raises() -> None:
    col = TelemetryCollector()
    with pytest.raises(CollectorError):
        col.unregister("ghost")


def test_list_producers() -> None:
    col = TelemetryCollector()
    col.register("a", _good_producer)
    col.register("b", _good_producer)
    names = col.list_producers()
    assert "a" in names and "b" in names


def test_batch_history() -> None:
    col = TelemetryCollector(max_history=3)
    for _ in range(5):
        col.collect()
    assert col.batch_count() == 3


def test_latest_batch() -> None:
    col = TelemetryCollector()
    col.register("n", _good_producer)
    col.collect()
    latest = col.latest_batch()
    assert latest is not None
    assert "n" in latest.snapshots


def test_latest_batch_none_when_empty() -> None:
    col = TelemetryCollector()
    assert col.latest_batch() is None


def test_clear_history() -> None:
    col = TelemetryCollector()
    col.register("n", _good_producer)
    col.collect()
    col.clear_history()
    assert col.batch_count() == 0


def test_batch_to_dict() -> None:
    col = TelemetryCollector()
    col.register("n", _good_producer)
    batch = col.collect()
    d = batch.to_dict()
    assert "batch_id" in d
    assert "collected_at" in d
    assert "snapshots" in d


def test_count() -> None:
    col = TelemetryCollector()
    col.register("a", _good_producer)
    col.register("b", _good_producer)
    assert col.count() == 2


def test_clear_producers() -> None:
    col = TelemetryCollector()
    col.register("a", _good_producer)
    col.clear_producers()
    assert col.count() == 0
