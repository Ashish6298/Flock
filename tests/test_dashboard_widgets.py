"""Unit tests for WidgetRegistry."""

import pytest

from flock.dashboard.widgets import WidgetRegistry
from flock.dashboard.models import WidgetDefinition
from flock.dashboard.exceptions import WidgetNotFoundError


def _make_widget(widget_id: str, widget_type: str = "chart") -> WidgetDefinition:
    return WidgetDefinition(
        widget_id=widget_id,
        widget_type=widget_type,
        title=f"Widget {widget_id}",
        data_source="cpu_pct",
    )


def test_register_and_get() -> None:
    reg = WidgetRegistry()
    w = _make_widget("w1")
    reg.register(w)
    assert reg.get("w1") == w


def test_get_missing_raises() -> None:
    reg = WidgetRegistry()
    with pytest.raises(WidgetNotFoundError):
        reg.get("nonexistent")


def test_unregister() -> None:
    reg = WidgetRegistry()
    reg.register(_make_widget("w2"))
    reg.unregister("w2")
    assert not reg.exists("w2")


def test_unregister_missing_raises() -> None:
    reg = WidgetRegistry()
    with pytest.raises(WidgetNotFoundError):
        reg.unregister("ghost")


def test_list_all() -> None:
    reg = WidgetRegistry()
    reg.register(_make_widget("a"))
    reg.register(_make_widget("b"))
    assert len(reg.list_all()) == 2


def test_find_by_type() -> None:
    reg = WidgetRegistry()
    reg.register(_make_widget("c", "chart"))
    reg.register(_make_widget("d", "gauge"))
    charts = reg.find_by_type("chart")
    assert len(charts) == 1
    assert charts[0].widget_id == "c"


def test_count() -> None:
    reg = WidgetRegistry()
    reg.register_many([_make_widget("x"), _make_widget("y")])
    assert reg.count() == 2


def test_clear() -> None:
    reg = WidgetRegistry()
    reg.register(_make_widget("z"))
    reg.clear()
    assert reg.count() == 0


def test_get_optional_missing() -> None:
    reg = WidgetRegistry()
    assert reg.get_optional("nope") is None
