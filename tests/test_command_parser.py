"""Unit tests for CommandParser."""

import pytest
from flock.cli.exceptions import CommandValidationError
from flock.cli.parser import CommandParser


def test_command_parser_tokens() -> None:
    parser = CommandParser()
    tokens = parser.parse("cluster show --all")
    assert tokens == ["cluster", "show", "--all"]


def test_command_parser_empty_raises() -> None:
    parser = CommandParser()
    with pytest.raises(CommandValidationError):
        parser.parse("  ")
