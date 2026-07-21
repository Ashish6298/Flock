"""Unit tests for DataSourceManager."""

import pytest

from flock.dashboard.datasources import DataSourceManager
from flock.dashboard.models import DataSourceResult, MetricDataPoint
from flock.dashboard.exceptions import DataSourceError


def _good_source() -> DataSourceResult:
    return DataSourceResult(
        source_name="test",
        data_points=[MetricDataPoint(timestamp=1.0, metric_name="x", value=42.0)],
    )


def _bad_source() -> DataSourceResult:
    raise RuntimeError("connection lost")


def test_register_and_query() -> None:
    mgr = DataSourceManager()
    mgr.register("good", _good_source)
    result = mgr.query("good")
    assert result.success is True
    assert result.data_points[0].value == 42.0


def test_query_missing_raises() -> None:
    mgr = DataSourceManager()
    with pytest.raises(DataSourceError):
        mgr.query("missing")


def test_query_safe_bad_source() -> None:
    mgr = DataSourceManager()
    mgr.register("bad", _bad_source)
    result = mgr.query_safe("bad")
    assert result.success is False
    assert result.error is not None


def test_query_all() -> None:
    mgr = DataSourceManager()
    mgr.register("s1", _good_source)
    mgr.register("s2", _good_source)
    results = mgr.query_all()
    assert len(results) == 2
    assert all(r.success for r in results)


def test_make_constant_source() -> None:
    mgr = DataSourceManager()
    mgr.make_constant_source("const", 99.0)
    result = mgr.query("const")
    assert result.data_points[0].value == 99.0


def test_unregister() -> None:
    mgr = DataSourceManager()
    mgr.register("s", _good_source)
    mgr.unregister("s")
    assert not mgr.exists("s")


def test_unregister_missing_raises() -> None:
    mgr = DataSourceManager()
    with pytest.raises(DataSourceError):
        mgr.unregister("ghost")


def test_list_sources() -> None:
    mgr = DataSourceManager()
    mgr.register("a", _good_source)
    mgr.register("b", _good_source)
    names = mgr.list_sources()
    assert "a" in names and "b" in names


def test_count_and_clear() -> None:
    mgr = DataSourceManager()
    mgr.register("x", _good_source)
    assert mgr.count() == 1
    mgr.clear()
    assert mgr.count() == 0
