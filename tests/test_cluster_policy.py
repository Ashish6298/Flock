"""Unit tests for PolicyEngine."""

from flock.orchestrator.models import ClusterPolicy
from flock.orchestrator.policy import PolicyEngine


def test_policy_violations() -> None:
    policy = ClusterPolicy(
        policy_id="pol-1",
        strategy_name="balanced",
        target_utilization=70.0,
    )
    engine = PolicyEngine(policy)

    # Fits threshold limits
    assert engine.evaluate_violation(60.0) is False

    # Violates threshold limits
    assert engine.evaluate_violation(85.0) is True
