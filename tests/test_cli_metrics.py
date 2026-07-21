"""Unit tests for CliMetrics."""

from flock.cli.models import CliMetrics


def test_cli_metrics_execution_count() -> None:
    metrics = CliMetrics(executed_commands_count=14)
    assert metrics.executed_commands_count == 14
