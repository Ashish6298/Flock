"""Unit tests for CliHistory."""

from flock.cli.history import HistoryLogger


def test_cli_history_logger() -> None:
    logger = HistoryLogger()
    logger.append_command("status")
    logger.append_command("reboot")

    assert logger.get_lines() == ["status", "reboot"]
