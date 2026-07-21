"""Unit tests for CommandRegistry."""

import pytest
from flock.cli.commands import CommandRegistry
from flock.cli.exceptions import CommandValidationError
from flock.cli.models import CommandDefinition


def test_command_registry_add_lookup() -> None:
    registry = CommandRegistry()
    defn = CommandDefinition(name="status", description="Get node status")
    
    registry.register(defn)
    assert registry.lookup("status").name == "status"


def test_command_registry_duplicate_raises() -> None:
    registry = CommandRegistry()
    defn = CommandDefinition(name="status", description="Get node status")
    registry.register(defn)

    with pytest.raises(CommandValidationError):
        registry.register(defn)
