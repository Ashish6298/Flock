"""Modular Command Registry."""

from __future__ import annotations

from typing import Dict

from flock.cli.exceptions import CommandValidationError
from flock.cli.models import CommandDefinition


class CommandRegistry:
    """Registers built-in and plugin operational commands."""

    def __init__(self) -> None:
        self._commands: Dict[str, CommandDefinition] = {}

    def register(self, definition: CommandDefinition) -> None:
        """Add new action templates.

        Raises:
            CommandValidationError: If name is empty or already registered.
        """
        if not definition.name:
            raise CommandValidationError("Command name cannot be empty.")
        if definition.name in self._commands:
            raise CommandValidationError(f"Command '{definition.name}' is already registered.")

        self._commands[definition.name] = definition

    def lookup(self, name: str) -> CommandDefinition:
        """Find command schema by identifier.

        Raises:
            CommandValidationError: If target name is not found.
        """
        if name not in self._commands:
            raise CommandValidationError(f"Command '{name}' not found.")
        return self._commands[name]
