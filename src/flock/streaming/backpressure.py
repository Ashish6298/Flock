"""Backpressure Controller tracking publish rates."""

from __future__ import annotations

import time

from flock.streaming.exceptions import BackpressureLimitExceededError


class BackpressureController:
    """Enforces execution limits and checks rate throttling parameters."""

    def __init__(self, max_rate: int = 100, window_seconds: float = 1.0) -> None:
        self.max_rate = max_rate
        self.window = window_seconds
        
        self._timestamps: list[float] = []

    def record_and_assert(self) -> None:
        """Record a publish execution stamp.

        Raises:
            BackpressureLimitExceededError: If rate exceeds thresholds.
        """
        now = time.time()
        
        # Prune stale entries
        self._timestamps = [t for t in self._timestamps if now - t < self.window]
        
        if len(self._timestamps) >= self.max_rate:
            raise BackpressureLimitExceededError("Rate limit exceeded, applying backpressure.")

        self._timestamps.append(now)
