"""Unit tests verifying Cluster MembershipRegistry catalog behavior."""

import pytest
import time
from flock.discovery.models import NodeDescription
from flock.cluster.models import ClusterMember, ClusterMemberStatus
from flock.cluster.registry import MembershipRegistry
from flock.cluster.exceptions import MembershipStateError, DuplicateMembershipError

def test_membership_registry_operations() -> None:
    registry = MembershipRegistry()
    desc = NodeDescription(node_id="node-1", host="127.0.0.1", port=9001)

    member = ClusterMember(
        node_id="node-1",
        description=desc,
        status=ClusterMemberStatus.JOINING,
        join_timestamp=time.time()
    )

    # Initial register
    registry.add_member(member)
    assert len(registry.list_members()) == 1
    assert registry.version == 1

    # Duplicate check
    with pytest.raises(DuplicateMembershipError):
        registry.add_member(member)

    # State update transition
    registry.update_status("node-1", ClusterMemberStatus.ACTIVE)
    assert registry.get_member("node-1").status == ClusterMemberStatus.ACTIVE # type: ignore
    assert registry.version == 2

def test_membership_invalid_transition() -> None:
    registry = MembershipRegistry()
    desc = NodeDescription(node_id="node-2", host="127.0.0.1", port=9002)

    member = ClusterMember(
        node_id="node-2",
        description=desc,
        status=ClusterMemberStatus.REMOVED,
        join_timestamp=time.time()
    )

    registry.add_member(member)
    with pytest.raises(MembershipStateError):
        registry.update_status("node-2", ClusterMemberStatus.ACTIVE)
