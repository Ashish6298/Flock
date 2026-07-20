"""Unit tests for RBAC engine."""

import pytest
from flock.security.exceptions import AuthorizationError
from flock.security.rbac import AuthorizationEngine


def test_rbac_policy_evaluations() -> None:
    engine = AuthorizationEngine()
    engine.assign_role("node-1", "coordinator")
    engine.assign_role("node-2", "worker")

    # Authorize coordinator privileges
    dec1 = engine.authorize("node-1", "tasks.create")
    assert dec1.allowed is True

    # Authorize worker privileges
    dec2 = engine.authorize("node-2", "tasks.execute")
    assert dec2.allowed is True

    # Coordinator denies worker executions
    dec3 = engine.authorize("node-1", "tasks.execute")
    assert dec3.allowed is False


def test_assign_missing_role_raises() -> None:
    engine = AuthorizationEngine()
    with pytest.raises(AuthorizationError):
        engine.assign_role("node-1", "unknown-role")
