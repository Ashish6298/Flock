"""Unit tests for PanelRegistry."""

import pytest

from flock.dashboard.panels import PanelRegistry
from flock.dashboard.models import PanelDefinition
from flock.dashboard.exceptions import PanelNotFoundError, PermissionDeniedError


def _make_panel(
    panel_id: str, required_roles: list[str] | None = None
) -> PanelDefinition:
    return PanelDefinition(
        panel_id=panel_id,
        panel_name=f"Panel {panel_id}",
        widgets=[],
        required_roles=required_roles or [],
    )


def test_register_and_get() -> None:
    reg = PanelRegistry()
    p = _make_panel("p1")
    reg.register(p)
    assert reg.get("p1") == p


def test_get_missing_raises() -> None:
    reg = PanelRegistry()
    with pytest.raises(PanelNotFoundError):
        reg.get("ghost")


def test_unregister() -> None:
    reg = PanelRegistry()
    reg.register(_make_panel("p2"))
    reg.unregister("p2")
    assert not reg.exists("p2")


def test_check_access_no_roles_required() -> None:
    reg = PanelRegistry()
    reg.register(_make_panel("open"))
    reg.check_access("open", [])  # Should not raise.


def test_check_access_with_matching_role() -> None:
    reg = PanelRegistry()
    reg.register(_make_panel("admin_panel", ["admin"]))
    reg.check_access("admin_panel", ["admin"])  # Should not raise.


def test_check_access_denied() -> None:
    reg = PanelRegistry()
    reg.register(_make_panel("secured", ["admin"]))
    with pytest.raises(PermissionDeniedError):
        reg.check_access("secured", ["viewer"])


def test_find_accessible() -> None:
    reg = PanelRegistry()
    reg.register(_make_panel("public"))
    reg.register(_make_panel("private", ["admin"]))
    accessible = reg.find_accessible(["viewer"])
    assert len(accessible) == 1
    assert accessible[0].panel_id == "public"


def test_count_and_clear() -> None:
    reg = PanelRegistry()
    reg.register_many([_make_panel("a"), _make_panel("b")])
    assert reg.count() == 2
    reg.clear()
    assert reg.count() == 0
