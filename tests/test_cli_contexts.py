"""Unit tests for CliContexts."""

from flock.cli.models import ClusterContext


def test_cli_cluster_context_values() -> None:
    ctx = ClusterContext(context_name="prod", endpoint="192.168.1.100")
    assert ctx.context_name == "prod"
    assert ctx.endpoint == "192.168.1.100"
