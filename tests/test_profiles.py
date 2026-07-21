"""Unit tests for ProfileManager."""

import pytest
from flock.cli.exceptions import ProfileNotFoundError
from flock.cli.models import ProfileDefinition
from flock.cli.profiles import ProfileManager


def test_profile_switching() -> None:
    manager = ProfileManager()
    p1 = ProfileDefinition(username="alice", roles=["admin"])
    p2 = ProfileDefinition(username="bob", roles=["guest"])

    manager.add_profile("alice", p1)
    manager.add_profile("bob", p2)
    assert manager.active_profile_name == "alice"

    manager.switch_profile("bob")
    assert manager.active_profile_name == "bob"


def test_profile_missing_raises() -> None:
    manager = ProfileManager()
    with pytest.raises(ProfileNotFoundError):
        manager.switch_profile("missing")
