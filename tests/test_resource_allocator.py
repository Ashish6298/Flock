"""Unit tests for ResourceAllocator."""

import pytest
from flock.resources.allocator import ResourceAllocator
from flock.resources.exceptions import ResourceExhaustionError
from flock.resources.models import NodeResourceProfile
from flock.resources.registry import ResourceRegistry


def test_allocator_deterministic_lease() -> None:
    registry = ResourceRegistry()
    allocator = ResourceAllocator(registry)

    # Register node
    profile = NodeResourceProfile(
        node_id="node-1",
        cpu_cores=4.0,
        cpu_util=0.0,
        memory_mb=4096.0,
        memory_util=0.0,
    )
    registry.register_node(profile)

    req = {"cpu": 2.0, "memory": 2048.0}
    res = allocator.allocate("req-1", req)

    assert res.success is True
    assert res.assigned_node == "node-1"
    assert res.reservation_id is not None

    # Exhaustion check
    with pytest.raises(ResourceExhaustionError):
        allocator.allocate("req-2", {"cpu": 8.0, "memory": 8192.0})
