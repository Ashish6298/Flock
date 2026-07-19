"""Unit tests validating RetryPolicyEngine backoff delays and filter matches."""

import pytest
from flock.recovery.models import RetryPolicy, RetryContext, BackoffStrategy
from flock.recovery.policy import RetryPolicyEngine

def test_retry_policy_engine_backoffs() -> None:
    policy = RetryPolicy(max_attempts=3, base_delay_sec=1.0, backoff_strategy=BackoffStrategy.EXPONENTIAL)
    ctx = RetryContext(task_id="task-1", attempt_count=0)

    # Attempt 1
    decision = RetryPolicyEngine.evaluate(policy, ctx)
    assert decision.should_retry is True
    assert decision.delay_sec == 1.0

    # Attempt 2
    ctx2 = RetryContext(task_id="task-1", attempt_count=1)
    decision2 = RetryPolicyEngine.evaluate(policy, ctx2)
    assert decision2.should_retry is True
    assert decision2.delay_sec == 2.0

    # Attempt 3 (limit reached)
    ctx3 = RetryContext(task_id="task-1", attempt_count=3)
    decision3 = RetryPolicyEngine.evaluate(policy, ctx3)
    assert decision3.should_retry is False

def test_retry_policy_filters() -> None:
    policy = RetryPolicy(
        max_attempts=3,
        retryable_exceptions=["RuntimeError"],
        non_retryable_exceptions=["ValueError"]
    )
    ctx = RetryContext(task_id="task-2", attempt_count=0)

    # Retryable match
    decision_ok = RetryPolicyEngine.evaluate(policy, ctx, "RuntimeError")
    assert decision_ok.should_retry is True

    # Non-retryable match
    decision_fail = RetryPolicyEngine.evaluate(policy, ctx, "ValueError")
    assert decision_fail.should_retry is False

    # Not in list check
    decision_other = RetryPolicyEngine.evaluate(policy, ctx, "KeyError")
    assert decision_other.should_retry is False
