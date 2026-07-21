"""Unit tests for CommandExecutionEngine."""

import pytest
from flock.cli.commands import CommandRegistry
from flock.cli.exceptions import CommandPermissionError
from flock.cli.executor import CommandExecutionEngine
from flock.cli.models import CommandContext, CommandDefinition


def test_command_executor_permissions() -> None:
    registry = CommandRegistry()
    defn = CommandDefinition(name="reboot", description="Reboot node", required_permissions=["admin"])
    registry.register(defn)

    executor = CommandExecutionEngine(registry)
    
    # Authorized admin runs successfully
    ctx_admin = CommandContext(active_profile="admin", active_context="local")
    res = executor.execute("reboot", ctx_admin)
    assert res.exit_code == 0

    # Non-admin triggers PermissionError
    ctx_guest = CommandContext(active_profile="guest", active_context="local")
    with pytest.raises(CommandPermissionError):
        executor.execute("reboot", ctx_guest)
