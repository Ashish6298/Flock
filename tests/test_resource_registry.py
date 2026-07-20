"""Unit tests for ResourceRegistry."""

from flock.resources.models import NodeResourceProfile
from flock.resources.registry import ResourceRegistry


def test_registry_register_and_list() -> None:
    registry = ResourceRegistry()
    profile = NodeResourceProfile(
        node_id="node-1",
        cpu_cores=8.0,
        cpu_util=10.0,
        memory_mb=16384.0,
        memory_util=20.0,
    )

    registry.register_node(profile)
    assert registry.get_profile("node-1") == profile

    profiles = registry.list_profiles()
    assert len(profiles) == 1

    registry.unregister_node("node-1")
    assert registry.get_profile("node-1") is None
