"""Sampling Engine – Phase 34.

Implements probabilistic, adaptive, and rule-based trace sampling
strategies.  High-priority events are always preserved.  The default
strategy is probabilistic with a configurable rate.
"""

from __future__ import annotations

import random
import threading
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from flock.observability.exceptions import SamplingError


class SamplingStrategy(str, Enum):
    """Available sampling strategies."""

    PROBABILISTIC = "probabilistic"   # Fixed sampling rate.
    ADAPTIVE = "adaptive"             # Rate adjusts based on throughput.
    RULE_BASED = "rule_based"         # Per-key rule overrides.
    ALWAYS_ON = "always_on"           # Sample every event.
    ALWAYS_OFF = "always_off"         # Drop every event.


class SamplingDecision:
    """Result of a sampling evaluation.

    Attributes:
        sampled: Whether the event should be retained.
        reason: Human-readable explanation.
    """

    __slots__ = ("sampled", "reason")

    def __init__(self, sampled: bool, reason: str = "") -> None:
        self.sampled: bool = sampled
        self.reason: str = reason

    def __bool__(self) -> bool:
        return self.sampled


class SamplingRule:
    """A named predicate that overrides the default sampling decision.

    Attributes:
        name: Rule identifier.
        predicate: Called with the event dict; returns ``True`` to force
            sampling, ``False`` to force dropping.
        force_sample: If ``True`` the rule forces a positive sample;
            otherwise it forces a drop.
    """

    def __init__(
        self,
        name: str,
        predicate: Callable[[Dict[str, Any]], bool],
        force_sample: bool = True,
    ) -> None:
        self.name: str = name
        self.predicate: Callable[[Dict[str, Any]], bool] = predicate
        self.force_sample: bool = force_sample


class SamplingEngine:
    """Thread-safe trace and event sampling engine.

    Supports probabilistic, adaptive, rule-based, always-on, and
    always-off strategies.  High-priority event keys are always sampled
    regardless of strategy.

    Attributes:
        _lock: Protects mutable state.
        _strategy: Active sampling strategy.
        _rate: Current sampling rate in ``[0.0, 1.0]``.
        _rules: Ordered list of sampling rules.
        _high_priority_keys: Set of event keys that bypass sampling.
        _sampled_count: Cumulative count of sampled events.
        _dropped_count: Cumulative count of dropped events.
        _adaptive_target: Target events per second for adaptive mode.
        _adaptive_current_rate: Dynamically adjusted rate.
    """

    def __init__(
        self,
        strategy: SamplingStrategy = SamplingStrategy.PROBABILISTIC,
        rate: float = 0.1,
    ) -> None:
        """Initialise.

        Args:
            strategy: Default sampling strategy.
            rate: Initial sampling rate for probabilistic/adaptive modes.
        """
        if not 0.0 <= rate <= 1.0:
            raise SamplingError("Sampling rate must be in [0.0, 1.0].")
        self._lock: threading.RLock = threading.RLock()
        self._strategy: SamplingStrategy = strategy
        self._rate: float = rate
        self._rules: List[SamplingRule] = []
        self._high_priority_keys: Set[str] = set()
        self._sampled_count: int = 0
        self._dropped_count: int = 0
        self._adaptive_target: float = 100.0  # events/second target
        self._adaptive_current_rate: float = rate

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def set_strategy(self, strategy: SamplingStrategy) -> None:
        """Change the active sampling strategy.

        Args:
            strategy: New :class:`SamplingStrategy`.
        """
        with self._lock:
            self._strategy = strategy

    def set_rate(self, rate: float) -> None:
        """Update the sampling rate.

        Args:
            rate: New rate in ``[0.0, 1.0]``.

        Raises:
            SamplingError: If ``rate`` is out of range.
        """
        if not 0.0 <= rate <= 1.0:
            raise SamplingError("Sampling rate must be in [0.0, 1.0].")
        with self._lock:
            self._rate = rate
            self._adaptive_current_rate = rate

    def add_rule(self, rule: SamplingRule) -> None:
        """Register a sampling rule.

        Rules are evaluated in registration order; the first matching
        rule wins.

        Args:
            rule: Rule to add.
        """
        with self._lock:
            self._rules.append(rule)

    def remove_rule(self, name: str) -> None:
        """Remove a rule by name.

        Args:
            name: Rule name to remove.

        Raises:
            SamplingError: If no rule with ``name`` exists.
        """
        with self._lock:
            before = len(self._rules)
            self._rules = [r for r in self._rules if r.name != name]
            if len(self._rules) == before:
                raise SamplingError(f"Sampling rule '{name}' not found.")

    def mark_high_priority(self, key: str) -> None:
        """Mark an event key as high-priority (always sampled).

        Args:
            key: Event key to preserve.
        """
        with self._lock:
            self._high_priority_keys.add(key)

    def clear_high_priority(self, key: str) -> None:
        """Remove an event key from the high-priority set."""
        with self._lock:
            self._high_priority_keys.discard(key)

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def should_sample(
        self,
        event: Dict[str, Any],
        priority_key: Optional[str] = None,
    ) -> SamplingDecision:
        """Determine whether an event should be sampled.

        Evaluation order:
        1. If ``priority_key`` is registered as high-priority → always sample.
        2. Check rule-based overrides (first match wins).
        3. Apply the active strategy.

        Args:
            event: Event dict for rule predicate evaluation.
            priority_key: Optional key to check for high-priority status.

        Returns:
            A :class:`SamplingDecision`.
        """
        with self._lock:
            strategy = self._strategy
            rate = self._rate
            high_priority_keys = set(self._high_priority_keys)
            rules = list(self._rules)

        # 1. High-priority override.
        if priority_key and priority_key in high_priority_keys:
            self._record(sampled=True)
            return SamplingDecision(True, "high-priority")

        # 2. Rule-based overrides.
        for rule in rules:
            try:
                if rule.predicate(event):
                    self._record(sampled=rule.force_sample)
                    reason = (
                        f"rule:{rule.name}:force_sample={rule.force_sample}"
                    )
                    return SamplingDecision(rule.force_sample, reason)
            except Exception:
                pass

        # 3. Strategy.
        if strategy == SamplingStrategy.ALWAYS_ON:
            self._record(sampled=True)
            return SamplingDecision(True, "always_on")
        if strategy == SamplingStrategy.ALWAYS_OFF:
            self._record(sampled=False)
            return SamplingDecision(False, "always_off")

        effective_rate = (
            self._adaptive_current_rate
            if strategy == SamplingStrategy.ADAPTIVE
            else rate
        )
        sampled = random.random() < effective_rate
        self._record(sampled=sampled)
        return SamplingDecision(sampled, f"probabilistic:{effective_rate:.4f}")

    def adapt_rate(self, observed_rate: float) -> None:
        """Adjust adaptive sampling rate based on observed event throughput.

        When ``observed_rate`` exceeds ``_adaptive_target`` the sampling
        rate is reduced; when it is below, the rate is increased.

        Args:
            observed_rate: Current observed event rate (events/second).
        """
        with self._lock:
            if self._adaptive_target <= 0:
                return
            adjustment = self._adaptive_target / max(observed_rate, 0.001)
            new_rate = max(0.001, min(1.0, self._adaptive_current_rate * adjustment))
            self._adaptive_current_rate = new_rate

    def _record(self, sampled: bool) -> None:
        """Thread-unsafe counter update (must be called with _lock *not* held)."""
        if sampled:
            with self._lock:
                self._sampled_count += 1
        else:
            with self._lock:
                self._dropped_count += 1

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    @property
    def sampled_count(self) -> int:
        """Total events sampled since instantiation."""
        with self._lock:
            return self._sampled_count

    @property
    def dropped_count(self) -> int:
        """Total events dropped since instantiation."""
        with self._lock:
            return self._dropped_count

    def effective_rate(self) -> float:
        """Return the actual observed sampling rate.

        Returns:
            Fraction of events sampled, or ``0.0`` if none evaluated.
        """
        with self._lock:
            total = self._sampled_count + self._dropped_count
        return self._sampled_count / total if total > 0 else 0.0

    def reset_counters(self) -> None:
        """Reset sampled/dropped counters."""
        with self._lock:
            self._sampled_count = 0
            self._dropped_count = 0
