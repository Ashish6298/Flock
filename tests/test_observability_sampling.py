"""Unit tests for SamplingEngine – Phase 34."""

import pytest

from flock.observability.sampling import (
    SamplingEngine,
    SamplingRule,
    SamplingStrategy,
)
from flock.observability.exceptions import SamplingError


def test_always_on_samples_all() -> None:
    engine = SamplingEngine(strategy=SamplingStrategy.ALWAYS_ON)
    for _ in range(20):
        decision = engine.should_sample({})
        assert decision.sampled is True


def test_always_off_drops_all() -> None:
    engine = SamplingEngine(strategy=SamplingStrategy.ALWAYS_OFF)
    for _ in range(20):
        decision = engine.should_sample({})
        assert decision.sampled is False


def test_probabilistic_rate_zero_drops_all() -> None:
    engine = SamplingEngine(strategy=SamplingStrategy.PROBABILISTIC, rate=0.0)
    decisions = [engine.should_sample({}) for _ in range(20)]
    assert all(not d.sampled for d in decisions)


def test_probabilistic_rate_one_samples_all() -> None:
    engine = SamplingEngine(strategy=SamplingStrategy.PROBABILISTIC, rate=1.0)
    decisions = [engine.should_sample({}) for _ in range(20)]
    assert all(d.sampled for d in decisions)


def test_high_priority_key_always_sampled() -> None:
    engine = SamplingEngine(strategy=SamplingStrategy.ALWAYS_OFF)
    engine.mark_high_priority("critical_trace")
    decision = engine.should_sample({}, priority_key="critical_trace")
    assert decision.sampled is True
    assert "high-priority" in decision.reason


def test_high_priority_key_removed() -> None:
    engine = SamplingEngine(strategy=SamplingStrategy.ALWAYS_OFF)
    engine.mark_high_priority("k")
    engine.clear_high_priority("k")
    decision = engine.should_sample({}, priority_key="k")
    assert decision.sampled is False


def test_rule_force_sample() -> None:
    engine = SamplingEngine(strategy=SamplingStrategy.ALWAYS_OFF)
    rule = SamplingRule(
        name="error_rule",
        predicate=lambda e: e.get("level") == "error",
        force_sample=True,
    )
    engine.add_rule(rule)
    decision = engine.should_sample({"level": "error"})
    assert decision.sampled is True


def test_rule_force_drop() -> None:
    engine = SamplingEngine(strategy=SamplingStrategy.ALWAYS_ON)
    rule = SamplingRule(
        name="debug_drop",
        predicate=lambda e: e.get("level") == "debug",
        force_sample=False,
    )
    engine.add_rule(rule)
    decision = engine.should_sample({"level": "debug"})
    assert decision.sampled is False


def test_remove_rule() -> None:
    engine = SamplingEngine()
    rule = SamplingRule("r1", predicate=lambda e: True)
    engine.add_rule(rule)
    engine.remove_rule("r1")
    # After removal always_on rule gone; probabilistic applies
    # Just verify no exception raised
    engine.should_sample({})


def test_remove_missing_rule_raises() -> None:
    engine = SamplingEngine()
    with pytest.raises(SamplingError):
        engine.remove_rule("nonexistent")


def test_invalid_rate_raises() -> None:
    with pytest.raises(SamplingError):
        SamplingEngine(rate=1.5)


def test_set_rate_invalid_raises() -> None:
    engine = SamplingEngine()
    with pytest.raises(SamplingError):
        engine.set_rate(-0.1)


def test_counters_increment() -> None:
    engine = SamplingEngine(strategy=SamplingStrategy.ALWAYS_ON)
    engine.should_sample({})
    engine.should_sample({})
    assert engine.sampled_count == 2
    assert engine.dropped_count == 0


def test_effective_rate() -> None:
    engine = SamplingEngine(strategy=SamplingStrategy.ALWAYS_ON, rate=1.0)
    for _ in range(10):
        engine.should_sample({})
    assert engine.effective_rate() == pytest.approx(1.0)


def test_reset_counters() -> None:
    engine = SamplingEngine(strategy=SamplingStrategy.ALWAYS_ON)
    engine.should_sample({})
    engine.reset_counters()
    assert engine.sampled_count == 0
    assert engine.dropped_count == 0


def test_adaptive_strategy() -> None:
    engine = SamplingEngine(strategy=SamplingStrategy.ADAPTIVE, rate=1.0)
    engine.adapt_rate(1000.0)  # high throughput → reduce rate
    # Should not raise and counters should work
    engine.should_sample({})
    assert engine.sampled_count + engine.dropped_count == 1
