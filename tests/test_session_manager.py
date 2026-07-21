"""Unit tests for SessionManager."""

import time
import pytest
from flock.cli.exceptions import SessionExpiredError
from flock.cli.session import SessionManager


def test_session_validation() -> None:
    manager = SessionManager()
    manager.create_session("s1", "token-abc", duration_sec=3600.0)

    # Valid session does not raise
    manager.validate_session("s1")


def test_session_expired_raises() -> None:
    manager = SessionManager()
    manager.create_session("s2", "token-xyz", duration_sec=-10.0)

    with pytest.raises(SessionExpiredError):
        manager.validate_session("s2")
