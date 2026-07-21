"""Unit tests for ThemeManager."""

import pytest

from flock.dashboard.themes import ThemeManager
from flock.dashboard.models import DashboardTheme
from flock.dashboard.exceptions import ThemeNotFoundError


def test_default_themes_registered() -> None:
    mgr = ThemeManager()
    names = [t.theme_name for t in mgr.list_all()]
    assert "dark" in names
    assert "light" in names
    assert "midnight" in names


def test_get_existing_theme() -> None:
    mgr = ThemeManager()
    theme = mgr.get("dark")
    assert theme.theme_name == "dark"


def test_get_missing_raises() -> None:
    mgr = ThemeManager()
    with pytest.raises(ThemeNotFoundError):
        mgr.get("nonexistent")


def test_register_custom_theme() -> None:
    mgr = ThemeManager()
    custom = DashboardTheme(
        theme_name="ocean",
        primary_color="#007BFF",
        background_color="#001F3F",
        font_family="Roboto, sans-serif",
    )
    mgr.register(custom)
    assert mgr.exists("ocean")
    assert mgr.get("ocean") == custom


def test_set_active_theme() -> None:
    mgr = ThemeManager()
    mgr.set_active("light")
    assert mgr.active_name() == "light"
    assert mgr.get_active().theme_name == "light"


def test_set_active_missing_raises() -> None:
    mgr = ThemeManager()
    with pytest.raises(ThemeNotFoundError):
        mgr.set_active("nope")


def test_unregister_theme() -> None:
    mgr = ThemeManager()
    mgr.register(DashboardTheme(
        theme_name="temp",
        primary_color="#fff",
        background_color="#000",
        font_family="Arial",
    ))
    mgr.unregister("temp")
    assert not mgr.exists("temp")


def test_count() -> None:
    mgr = ThemeManager()
    assert mgr.count() == 3  # dark, light, midnight


def test_get_optional() -> None:
    mgr = ThemeManager()
    assert mgr.get_optional("nope") is None
    assert mgr.get_optional("dark") is not None
