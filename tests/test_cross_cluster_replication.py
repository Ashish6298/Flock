"""Unit tests for CrossClusterReplicationEngine."""

import pytest
from flock.events.bus import EventBus
from flock.federation.exceptions import CrossClusterReplicationError
from flock.federation.models import FederationSnapshot
from flock.federation.replication import CrossClusterReplicationEngine


@pytest.mark.asyncio
async def test_snapshot_replication_lifecycle() -> None:
    events = EventBus()
    engine = CrossClusterReplicationEngine(events)

    snap = FederationSnapshot(
        timestamp=0.0,
        cluster_count=2,
        total_nodes=10,
        global_task_count=5,
    )

    assert await engine.replicate_snapshot(snap, "cluster-b") is True


@pytest.mark.asyncio
async def test_replicate_empty_snapshot_raises() -> None:
    events = EventBus()
    engine = CrossClusterReplicationEngine(events)

    snap = FederationSnapshot(
        timestamp=0.0,
        cluster_count=0,  # Zero clusters invalidates replication
        total_nodes=0,
        global_task_count=0,
    )

    with pytest.raises(CrossClusterReplicationError):
        await engine.replicate_snapshot(snap, "cluster-b")
