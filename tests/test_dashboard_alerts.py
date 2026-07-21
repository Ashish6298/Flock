"""Unit tests for AlertEngine."""

import pytest

from flock.dashboard.alerts import AlertEngine
from flock.dashboard.models import AlertDefinition, MetricDataPoint
from flock.dashboard.exceptions import AlertRuleError


def _make_rule(alert_id: str, metric: str, threshold: float) -> AlertDefinition:
    return AlertDefinition(
        alert_id=alert_id,
        metric_name=metric,
        threshold=threshold,
        severity="warning",
    )


def _make_point(metric: str, value: float) -> MetricDataPoint:
    return MetricDataPoint(timestamp=0.0, metric_name=metric, value=value)


def test_add_and_list_rules() -> None:
    engine = AlertEngine()
    engine.add_rule(_make_rule("r1", "cpu", 80.0))
    assert len(engine.list_rules()) == 1


def test_duplicate_rule_raises() -> None:
    engine = AlertEngine()
    engine.add_rule(_make_rule("r1", "cpu", 80.0))
    with pytest.raises(AlertRuleError):
        engine.add_rule(_make_rule("r1", "cpu", 80.0))


def test_remove_rule() -> None:
    engine = AlertEngine()
    engine.add_rule(_make_rule("r2", "mem", 90.0))
    engine.remove_rule("r2")
    assert engine.rule_exists("r2") is False


def test_remove_missing_rule_raises() -> None:
    engine = AlertEngine()
    with pytest.raises(AlertRuleError):
        engine.remove_rule("ghost")


def test_evaluate_fires_event() -> None:
    engine = AlertEngine()
    engine.add_rule(_make_rule("cpu_alert", "cpu", 80.0))
    events = engine.evaluate(_make_point("cpu", 95.0))
    assert len(events) == 1
    assert events[0].alert_id == "cpu_alert"


def test_evaluate_no_fire_below_threshold() -> None:
    engine = AlertEngine()
    engine.add_rule(_make_rule("cpu_alert", "cpu", 80.0))
    events = engine.evaluate(_make_point("cpu", 70.0))
    assert len(events) == 0


def test_handler_receives_event() -> None:
    received: list[str] = []
    engine = AlertEngine()
    engine.add_rule(_make_rule("mem_alert", "mem", 75.0))
    engine.add_handler(lambda e: received.append(e.alert_id))
    engine.evaluate(_make_point("mem", 80.0))
    assert "mem_alert" in received


def test_evaluate_batch() -> None:
    engine = AlertEngine()
    engine.add_rule(_make_rule("cpu_alert", "cpu", 80.0))
    points = [_make_point("cpu", 90.0), _make_point("cpu", 85.0)]
    events = engine.evaluate_batch(points)
    assert len(events) == 2


def test_clear_history() -> None:
    engine = AlertEngine()
    engine.add_rule(_make_rule("cpu_alert", "cpu", 80.0))
    engine.evaluate(_make_point("cpu", 90.0))
    assert engine.count_triggered() == 1
    engine.clear_history()
    assert engine.count_triggered() == 0
