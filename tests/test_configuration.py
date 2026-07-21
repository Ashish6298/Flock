"""Unit tests for ConfigurationManager."""

import pytest
from flock.cli.configuration import ConfigurationManager
from flock.cli.exceptions import ContextSwitchError
from flock.cli.models import ClusterContext


def test_configuration_switching() -> None:
    manager = ConfigurationManager()
    ctx1 = ClusterContext(context_name="east", endpoint="10.0.0.1")
    ctx2 = ClusterContext(context_name="west", endpoint="10.0.0.2")

    manager.add_context(ctx1)
    manager.add_context(ctx2)
    assert manager.active_context_name == "east"

    manager.switch_context("west")
    assert manager.active_context_name == "west"


def test_configuration_missing_raises() -> None:
    manager = ConfigurationManager()
    with pytest.raises(ContextSwitchError):
        manager.switch_context("missing")
