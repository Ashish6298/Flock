"""Delay calculators applying fixed, linear, or exponential backoffs with jitter."""

import random
import math
from typing import Optional
from flock.recovery.models import RetryPolicy, RetryContext, RetryDecision, BackoffStrategy

class RetryPolicyEngine:
    """Calculates backoff increments and retry decisions based on configured policies."""

    @staticmethod
    def evaluate(policy: RetryPolicy, context: RetryContext, exception_class: Optional[str] = None) -> RetryDecision:
        """Evaluate if task is eligible for retry and compute delay.

        Args:
            policy: Target retry policy rules.
            context: Current retry counters and history.
            exception_class: Optional exception name context.
        """
        # Attempt limit check
        if context.attempt_count >= policy.max_attempts:
            return RetryDecision(should_retry=False, reason="Max retry attempts exhausted")

        # Exception filter validation
        if exception_class:
            if policy.non_retryable_exceptions and exception_class in policy.non_retryable_exceptions:
                return RetryDecision(should_retry=False, reason=f"Exception {exception_class} is explicitly marked non-retryable")
            if policy.retryable_exceptions and exception_class not in policy.retryable_exceptions:
                return RetryDecision(should_retry=False, reason=f"Exception {exception_class} is not in retryable filters list")

        # Delay calculations
        delay = policy.base_delay_sec
        strategy = policy.backoff_strategy

        if strategy == BackoffStrategy.IMMEDIATE:
            delay = 0.0
        elif strategy == BackoffStrategy.LINEAR:
            delay = policy.base_delay_sec * (context.attempt_count + 1)
        elif strategy == BackoffStrategy.EXPONENTIAL:
            delay = policy.base_delay_sec * math.pow(2, context.attempt_count)
        elif strategy == BackoffStrategy.EXPONENTIAL_JITTER:
            base_val = policy.base_delay_sec * math.pow(2, context.attempt_count)
            # Apply randomized uniform jitter
            delay = random.uniform(policy.base_delay_sec, base_val)

        # Cap delay at maximum limits
        delay = min(delay, policy.max_delay_sec)

        return RetryDecision(
            should_retry=True,
            delay_sec=delay,
            reason=f"Eligible for retry (attempt {context.attempt_count + 1}/{policy.max_attempts})"
        )
