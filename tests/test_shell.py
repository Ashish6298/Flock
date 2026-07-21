"""Unit tests for ReplEngine."""

from flock.cli.shell import ReplEngine


def test_repl_engine_variables() -> None:
    shell = ReplEngine()
    shell.set_variable("namespace", "prod")

    assert shell.get_variable("namespace") == "prod"
    assert shell.get_variable("missing") == ""
