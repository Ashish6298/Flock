"""Autoscaling Engine managing replicas scaling targets."""

from __future__ import annotations

import structlog

from flock.functions.exceptions import ScalePolicyError

logger = structlog.get_logger()


class AutoScalingEngine:
    """Calculates scaling replicas based on request traffic metrics."""

    def __init__(self, min_replicas: int = 0, max_replicas: int = 10) -> None:
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas

    def calculate_replicas(self, current_replicas: int, active_concurrency: int) -> int:
        """Evaluate targets. Enforce minimum and maximum limits.

        Raises:
            ScalePolicyError: If current replica state is negative.
        """
        if current_replicas < 0:
            raise ScalePolicyError("Current replicas count cannot be negative.")

        if active_concurrency == 0:
            return self.min_replicas

        # Simple scaling rule: scale up if concurrency exceeds 5
        target = current_replicas
        if active_concurrency > 5:
            target = min(current_replicas + 1, self.max_replicas)

        return max(target, 1)
