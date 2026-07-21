"""Unit tests for ReplicationCoordinator."""

from flock.datagrid.replication import ReplicationCoordinator


def test_coordinator_replicates_keys() -> None:
    coord = ReplicationCoordinator()

    # Verify sync checks
    assert coord.is_synchronized("node-1", "k1") is False

    coord.mark_synchronized("node-1", "k1")
    assert coord.is_synchronized("node-1", "k1") is True
