"""Unit tests for SessionManager."""

import time
import pytest

from flock.dashboard.sessions import SessionManager
from flock.dashboard.exceptions import SessionExpiredError


def test_create_and_validate_session() -> None:
    mgr = SessionManager()
    token = mgr.create_session("alice", ["admin"])
    assert token.username == "alice"
    assert "admin" in token.roles
    validated = mgr.validate(token.session_id)
    assert validated.session_id == token.session_id


def test_expired_session_raises() -> None:
    mgr = SessionManager(ttl_seconds=0.01)
    token = mgr.create_session("bob", [])
    time.sleep(0.05)
    with pytest.raises(SessionExpiredError):
        mgr.validate(token.session_id)


def test_revoke_session() -> None:
    mgr = SessionManager()
    token = mgr.create_session("carol", [])
    mgr.revoke(token.session_id)
    assert not mgr.is_valid(token.session_id)


def test_revoke_all_for_user() -> None:
    mgr = SessionManager()
    mgr.create_session("dave", [])
    mgr.create_session("dave", [])
    count = mgr.revoke_all_for_user("dave")
    assert count == 2


def test_list_active() -> None:
    mgr = SessionManager()
    mgr.create_session("eve", [])
    mgr.create_session("frank", [])
    assert mgr.count_active() == 2


def test_purge_expired() -> None:
    mgr = SessionManager(ttl_seconds=0.01)
    mgr.create_session("grace", [])
    time.sleep(0.05)
    removed = mgr.purge_expired()
    assert removed == 1
    assert mgr.count_active() == 0


def test_get_returns_none_for_expired() -> None:
    mgr = SessionManager(ttl_seconds=0.01)
    token = mgr.create_session("henry", [])
    time.sleep(0.05)
    assert mgr.get(token.session_id) is None
