"""Unit and integration tests for Plugin Security Manager."""

from __future__ import annotations

import pytest
import uuid
from typing import List

from flock.plugins.models import (
    PermissionScope,
    PluginPermission,
    SecurityPolicy,
    PermissionRequest,
)
from flock.plugins.registry import PluginRegistry
from flock.plugins.security import PluginSecurityManager
from flock.plugins.exceptions import PluginPermissionDeniedError


def test_default_deny_behavior() -> None:
    registry = PluginRegistry()
    manager = PluginSecurityManager(registry)

    # No policies registered: default deny should block read access to sensitive resource
    assert manager.check_permission("plugin-a", PermissionScope.READ, "/etc/passwd") is False


def test_explicit_permission_grant() -> None:
    registry = PluginRegistry()
    manager = PluginSecurityManager(registry)

    # Grant explicit read access to specific plugin and resource path pattern
    perm = PluginPermission(
        permission_id=str(uuid.uuid4()),
        plugin_id="plugin-a",
        scope=PermissionScope.READ,
        resource="/data/*",
    )
    manager.grant_explicit_permission(perm)

    assert manager.check_permission("plugin-a", PermissionScope.READ, "/data/logs.txt") is True
    # Glob check should fail for resource outside the allowed path
    assert manager.check_permission("plugin-a", PermissionScope.READ, "/etc/passwd") is False


def test_security_policy_allow_and_deny() -> None:
    registry = PluginRegistry()
    manager = PluginSecurityManager(registry)

    # Register a policy denying WRITE and allowing READ
    policy = SecurityPolicy(
        policy_id="policy-1",
        plugin_id_pattern="plugin-*",
        allowed_permissions=[PermissionScope.READ],
        denied_permissions=[PermissionScope.WRITE],
    )
    manager.register_policy(policy)

    assert manager.check_permission("plugin-a", PermissionScope.READ, "any_resource") is True
    assert manager.check_permission("plugin-a", PermissionScope.WRITE, "any_resource") is False


def test_explicit_deny_trumps_allow() -> None:
    registry = PluginRegistry()
    manager = PluginSecurityManager(registry)

    # Policy explicitly denies WRITE
    policy = SecurityPolicy(
        policy_id="policy-1",
        plugin_id_pattern="plugin-*",
        allowed_permissions=[],
        denied_permissions=[PermissionScope.WRITE],
    )
    manager.register_policy(policy)

    # Attempt to grant explicit write permission
    perm = PluginPermission(
        permission_id=str(uuid.uuid4()),
        plugin_id="plugin-a",
        scope=PermissionScope.WRITE,
        resource="*",
    )
    manager.grant_explicit_permission(perm)

    # Deny should trump explicit grant
    assert manager.check_permission("plugin-a", PermissionScope.WRITE, "resource") is False


def test_verify_permission_raises_exception() -> None:
    registry = PluginRegistry()
    manager = PluginSecurityManager(registry)

    with pytest.raises(PluginPermissionDeniedError):
        manager.verify_permission("plugin-a", PermissionScope.WRITE, "file")


def test_permission_request_workflow() -> None:
    registry = PluginRegistry()
    manager = PluginSecurityManager(registry)

    policy = SecurityPolicy(
        policy_id="policy-1",
        plugin_id_pattern="plugin-*",
        allowed_permissions=[PermissionScope.EXECUTE],
        denied_permissions=[],
    )
    manager.register_policy(policy)

    req = PermissionRequest(
        request_id="req-1",
        plugin_id="plugin-a",
        scope=PermissionScope.EXECUTE,
        resource="cpu",
        justification="Needs execution",
    )
    # Autogrants permission because policy allows execute
    granted = manager.request_permission(req)
    assert granted is True
