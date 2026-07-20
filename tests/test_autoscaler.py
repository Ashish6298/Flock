"""Unit tests for AutoScaler."""

import pytest
from flock.orchestrator.autoscaler import AutoScaler
from flock.orchestrator.exceptions import ScalingPolicyViolationError
from flock.orchestrator.models import ClusterSnapshot


def test_autoscaler_scale_out_and_in() -> None:
    scaler = AutoScaler(min_nodes=1, max_nodes=5)

    # Scale Out Trigger on high util
    snapshot_high = ClusterSnapshot(
        timestamp=0.0,
        active_nodes=["node-1"],
        task_count=10,
        avg_utilization=90.0,
    )
    dec_out = scaler.evaluate_scale(snapshot_high)
    assert dec_out is not None
    assert dec_out.scale_type == "SCALE_OUT"

    # Scale In Trigger on low util
    snapshot_low = ClusterSnapshot(
        timestamp=0.0,
        active_nodes=["node-1", "node-2"],
        task_count=1,
        avg_utilization=10.0,
    )
    dec_in = scaler.evaluate_scale(snapshot_low)
    assert dec_in is not None
    assert dec_in.scale_type == "SCALE_IN"


def test_autoscaler_limit_violations() -> None:
    scaler = AutoScaler(min_nodes=1, max_nodes=2)
    snapshot = ClusterSnapshot(
        timestamp=0.0,
        active_nodes=["node-1", "node-2"],
        task_count=10,
        avg_utilization=90.0,
    )

    with pytest.raises(ScalingPolicyViolationError):
        scaler.evaluate_scale(snapshot)
