"""Unit tests for ClusterPredictions."""

from flock.ai.models import NodePrediction


def test_node_failure_probability_values() -> None:
    pred = NodePrediction(
        node_id="node-1",
        failure_probability=0.05,
    )

    assert pred.node_id == "node-1"
    assert pred.failure_probability == 0.05
