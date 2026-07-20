"""Unit tests for FederationRegistry."""

from flock.federation.models import FederationCluster
from flock.federation.registry import FederationRegistry


def test_registry_register_and_list() -> None:
    registry = FederationRegistry()
    cluster = FederationCluster(
        cluster_id="cluster-1",
        name="west-region",
        endpoints=["10.0.0.1:5000"],
        is_healthy=True,
        capacity_score=8.5,
    )

    registry.register_cluster(cluster)
    assert registry.get_cluster("cluster-1") == cluster

    clusters = registry.list_clusters()
    assert len(clusters) == 1

    registry.unregister_cluster("cluster-1")
    assert registry.get_cluster("cluster-1") is None
