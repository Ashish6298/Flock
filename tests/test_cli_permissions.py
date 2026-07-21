"""Unit tests for CliPermissions."""

import pytest
from flock.cli.commands import CommandRegistry
from flock.cli.exceptions import CommandPermissionError
from flock.cli.executor import CommandExecutionEngine
from flock.cli.models import CommandContext, CommandDefinition


def test_cli_permission_enforcement() -> None:
    registry = CommandRegistry()
    defn = CommandDefinition(name="delete-all", description="Destroy everything", required_permissions=["admin"])
    registry.register(defn)

    executor = CommandExecutionEngine(registry)
    ctx = CommandContext(active_profile="guest", active_context="local")

    with pytest.raises(CommandPermissionError):
        executor.execute("delete-all", ctx)
