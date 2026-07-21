"""Unit tests for CommandFormatter."""

import pytest
from flock.cli.exceptions import OutputFormattingError
from flock.cli.formatter import CommandFormatter
from flock.cli.models import OutputFormat


def test_formatter_json_yaml() -> None:
    formatter = CommandFormatter()
    data = {"status": "ok", "nodes": "3"}

    # Format JSON
    out_json = formatter.format_output(data, OutputFormat(format_type="json"))
    assert '"status": "ok"' in out_json

    # Format YAML simulation
    out_yaml = formatter.format_output(data, OutputFormat(format_type="yaml"))
    assert "status: ok" in out_yaml


def test_formatter_unsupported_raises() -> None:
    formatter = CommandFormatter()
    with pytest.raises(OutputFormattingError):
        formatter.format_output({}, OutputFormat(format_type="csv"))
