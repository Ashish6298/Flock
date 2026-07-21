"""Unit tests for DashboardRenderer."""

import pytest

from flock.dashboard.renderer import DashboardRenderer
from flock.dashboard.models import DataSourceResult, MetricDataPoint, WidgetDefinition
from flock.dashboard.exceptions import RenderError


def _make_widget(widget_type: str) -> WidgetDefinition:
    return WidgetDefinition(
        widget_id=f"w_{widget_type}",
        widget_type=widget_type,
        title=f"{widget_type.capitalize()} Widget",
        data_source="cpu_pct",
    )


def _make_result(n: int = 3) -> DataSourceResult:
    points = [
        MetricDataPoint(timestamp=float(i), metric_name="cpu", value=float(i * 10))
        for i in range(1, n + 1)
    ]
    return DataSourceResult(source_name="cpu_pct", data_points=points)


def test_render_chart() -> None:
    r = DashboardRenderer()
    payload = r.render(_make_widget("chart"), _make_result())
    assert payload["widget_type"] == "chart"
    assert len(payload["series"]) == 3


def test_render_gauge() -> None:
    r = DashboardRenderer()
    payload = r.render(_make_widget("gauge"), _make_result())
    assert payload["widget_type"] == "gauge"
    assert "value" in payload
    assert "percent" in payload


def test_render_stat() -> None:
    r = DashboardRenderer()
    payload = r.render(_make_widget("stat"), _make_result())
    assert payload["widget_type"] == "stat"
    assert payload["count"] == 3


def test_render_table() -> None:
    r = DashboardRenderer()
    payload = r.render(_make_widget("table"), _make_result())
    assert payload["widget_type"] == "table"
    assert len(payload["rows"]) == 3


def test_render_log() -> None:
    r = DashboardRenderer()
    payload = r.render(_make_widget("log"), _make_result(2))
    assert payload["widget_type"] == "log"
    assert len(payload["entries"]) == 2


def test_render_map() -> None:
    r = DashboardRenderer()
    payload = r.render(_make_widget("map"), _make_result(1))
    assert payload["widget_type"] == "map"
    assert len(payload["nodes"]) == 1


def test_render_unknown_type_fallback() -> None:
    r = DashboardRenderer()
    payload = r.render(_make_widget("mystery"), _make_result(1))
    assert payload["widget_type"] == "mystery"
    assert "raw_points" in payload


def test_render_error_result_raises() -> None:
    r = DashboardRenderer()
    bad_result = DataSourceResult(
        source_name="bad", success=False, error="connection refused"
    )
    with pytest.raises(RenderError):
        r.render(_make_widget("chart"), bad_result)


def test_render_empty_data_points() -> None:
    r = DashboardRenderer()
    result = DataSourceResult(source_name="cpu_pct", data_points=[])
    payload = r.render(_make_widget("stat"), result)
    assert payload["count"] == 0
    assert payload["current"] == 0.0
