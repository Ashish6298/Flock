"""Unit tests for PluginSandbox."""

import pytest
from flock.plugins.exceptions import PluginSandboxError
from flock.plugins.models import PluginContext
from flock.plugins.sandbox import PluginSandbox


def test_sandbox_enforces_execute_permissions() -> None:
    sandbox = PluginSandbox()

    # Context missing EXECUTE permission throws PluginSandboxError
    ctx_denied = PluginContext(plugin_id="plugin-3", data_directory="/tmp/plugin-3", permissions=["READ"])
    with pytest.raises(PluginSandboxError):
        sandbox.execute_in_sandbox(ctx_denied, lambda: "hello")

    # Context holding EXECUTE permission runs successfully
    ctx_allowed = PluginContext(plugin_id="plugin-3", data_directory="/tmp/plugin-3", permissions=["EXECUTE"])
    res = sandbox.execute_in_sandbox(ctx_allowed, lambda: "hello")
    assert res == "hello"
