"""Unit tests for ClusterAdvertisement mapping."""

from flock.federation.models import ClusterAdvertisement


def test_advertisement_structures() -> None:
    adv = ClusterAdvertisement(
        cluster_id="cluster-a",
        timestamp=100.0,
        resource_summary={"cpu_cores": 64.0, "memory_mb": 131072.0},
    )

    assert adv.cluster_id == "cluster-a"
    assert adv.resource_summary["cpu_cores"] == 64.0
