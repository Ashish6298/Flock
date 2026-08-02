"""Unit and integration tests for Plugin Sandbox Execution."""

from __future__ import annotations

import pytest
import uuid

from flock.plugins.models import PluginContext, PermissionScope, PluginPermission
from flock.plugins.registry import PluginRegistry
from flock.plugins.security import PluginSecurityManager
from flock.plugins.sandbox import PluginSandbox
from flock.plugins.exceptions import PluginSandboxError


def test_sandbox_executes_action_when_granted() -> None:
    registry = PluginRegistry()
    security = PluginSecurityManager(registry)
    sandbox = PluginSandbox(security)

    context = PluginContext(
        plugin_id="plugin-a",
        data_directory="/tmp/plugin-a",
        permissions=["execute"],
    )

    # Grant EXECUTE permission to execution_context
    perm = PluginPermission(
        permission_id=str(uuid.uuid4()),
        plugin_id="plugin-a",
        scope=PermissionScope.EXECUTE,
        resource="execution_context",
    )
    security.grant_explicit_permission(perm)

    def action(x: int, y: int) -> int:
        return x + y

    result = sandbox.execute_in_sandbox(context, action, 5, y=10)
    assert result == 15


def test_sandbox_raises_on_permission_denied() -> None:
    registry = PluginRegistry()
    security = PluginSecurityManager(registry)
    sandbox = PluginSandbox(security)

    context = PluginContext(
        plugin_id="plugin-a",
        data_directory="/tmp/plugin-a",
        permissions=[],
    )

    # No permission granted: EXECUTE scope check will fail and raise PluginSandboxError
    def action() -> str:
        return "unreachable"

    with pytest.raises(PluginSandboxError) as excinfo:
        sandbox.execute_in_sandbox(context, action)
    assert "Permission denied: Action requires 'EXECUTE' capability context." in str(excinfo.value)


def test_sandbox_isolates_action_failures() -> None:
    registry = PluginRegistry()
    security = PluginSecurityManager(registry)
    sandbox = PluginSandbox(security)

    context = PluginContext(
        plugin_id="plugin-a",
        data_directory="/tmp/plugin-a",
        permissions=["execute"],
    )

    perm = PluginPermission(
        permission_id=str(uuid.uuid4()),
        plugin_id="plugin-a",
        scope=PermissionScope.EXECUTE,
        resource="execution_context",
    )
    security.grant_explicit_permission(perm)

    def failing_action() -> None:
        raise ValueError("Simulated action failure")

    with pytest.raises(PluginSandboxError) as excinfo:
        sandbox.execute_in_sandbox(context, failing_action)
    assert "Plugin execution runtime error inside sandbox" in str(excinfo.value)
