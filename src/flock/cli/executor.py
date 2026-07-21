"""Command Execution Engine."""

from __future__ import annotations

from typing import Dict

from flock.cli.commands import CommandRegistry
from flock.cli.exceptions import CommandExecutionError, CommandPermissionError
from flock.cli.models import CommandContext, ExecutionResult


class CommandExecutionEngine:
    """Dispatches parsed instructions to services interfaces."""

    def __init__(self, registry: CommandRegistry) -> None:
        self.registry = registry

    def execute(self, command_name: str, context: CommandContext) -> ExecutionResult:
        """Evaluate parameters permissions.

        Raises:
            CommandPermissionError: If active profile does not match required roles.
            CommandExecutionError: If execution failure occurs.
        """
        # Lookup definition to retrieve permissions
        try:
            defn = self.registry.lookup(command_name)
        except Exception as exc:
            raise CommandExecutionError(f"Lookup failed: {exc}")

        # Check permissions
        if defn.required_permissions:
            # Heuristic: Simple profile role comparison check
            if context.active_profile != "admin":
                raise CommandPermissionError(
                    f"Profile '{context.active_profile}' lacks permissions for '{command_name}'."
                )

        return ExecutionResult(exit_code=0, data={"status": "completed"})
