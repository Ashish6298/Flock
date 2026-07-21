"""Unit tests for ObservabilityAlertManager – Phase 34."""

import time
import pytest

from flock.observability.alerts import (
    AlertRule,
    AlertSeverity,
    AlertState,
    ObservabilityAlertManager,
)
from flock.observability.exceptions import AlertError, AlertRuleNotFoundError


def _make_rule(
    rule_id: str = "r1",
    metric: str = "cpu",
    threshold: float = 80.0,
    cooldown: float = 0.0,
) -> AlertRule:
    return AlertRule(
        rule_id=rule_id,
        metric_name=metric,
        threshold=threshold,
        severity=AlertSeverity.WARNING,
        cooldown_seconds=cooldown,
    )


def test_add_and_list_rules() -> None:
    mgr = ObservabilityAlertManager()
    mgr.add_rule(_make_rule("r1"))
    assert len(mgr.list_rules()) == 1


def test_duplicate_rule_raises() -> None:
    mgr = ObservabilityAlertManager()
    mgr.add_rule(_make_rule("r1"))
    with pytest.raises(AlertError):
        mgr.add_rule(_make_rule("r1"))


def test_remove_rule() -> None:
    mgr = ObservabilityAlertManager()
    mgr.add_rule(_make_rule("r1"))
    mgr.remove_rule("r1")
    assert len(mgr.list_rules()) == 0


def test_remove_missing_rule_raises() -> None:
    mgr = ObservabilityAlertManager()
    with pytest.raises(AlertRuleNotFoundError):
        mgr.remove_rule("ghost")


def test_evaluate_fires_incident() -> None:
    mgr = ObservabilityAlertManager()
    mgr.add_rule(_make_rule("cpu_high", "cpu", 80.0, cooldown=0.0))
    fired = mgr.evaluate("cpu", 95.0)
    assert len(fired) == 1
    assert fired[0].metric_name == "cpu"
    assert fired[0].observed_value == 95.0


def test_evaluate_no_fire_below_threshold() -> None:
    mgr = ObservabilityAlertManager()
    mgr.add_rule(_make_rule("cpu_high", "cpu", 80.0))
    fired = mgr.evaluate("cpu", 70.0)
    assert len(fired) == 0


def test_evaluate_cooldown_prevents_second_fire() -> None:
    mgr = ObservabilityAlertManager()
    mgr.add_rule(_make_rule("r1", "cpu", 80.0, cooldown=3600.0))
    mgr.evaluate("cpu", 90.0)
    fired = mgr.evaluate("cpu", 90.0)
    assert len(fired) == 0


def test_suppression_prevents_firing() -> None:
    mgr = ObservabilityAlertManager()
    mgr.add_rule(_make_rule("r1", "cpu", 80.0))
    mgr.suppress("r1")
    fired = mgr.evaluate("cpu", 95.0)
    assert len(fired) == 0


def test_unsuppress_allows_firing() -> None:
    mgr = ObservabilityAlertManager()
    mgr.add_rule(_make_rule("r1", "cpu", 80.0, cooldown=0.0))
    mgr.suppress("r1")
    mgr.unsuppress("r1")
    fired = mgr.evaluate("cpu", 95.0)
    assert len(fired) == 1


def test_handler_receives_incident() -> None:
    received: list = []
    mgr = ObservabilityAlertManager()
    mgr.add_rule(_make_rule("r1", "cpu", 80.0, cooldown=0.0))
    mgr.add_handler(lambda inc: received.append(inc.rule_id))
    mgr.evaluate("cpu", 95.0)
    assert "r1" in received


def test_acknowledge_incident() -> None:
    mgr = ObservabilityAlertManager()
    mgr.add_rule(_make_rule("r1", "cpu", 80.0, cooldown=0.0))
    fired = mgr.evaluate("cpu", 95.0)
    mgr.acknowledge(fired[0].incident_id)
    assert fired[0].state == AlertState.ACKNOWLEDGED
    assert fired[0].acknowledged_at is not None


def test_resolve_incident() -> None:
    mgr = ObservabilityAlertManager()
    mgr.add_rule(_make_rule("r1", "cpu", 80.0, cooldown=0.0))
    fired = mgr.evaluate("cpu", 95.0)
    mgr.resolve(fired[0].incident_id)
    assert fired[0].state == AlertState.RESOLVED


def test_acknowledge_missing_raises() -> None:
    mgr = ObservabilityAlertManager()
    with pytest.raises(AlertRuleNotFoundError):
        mgr.acknowledge("nonexistent-id")


def test_get_firing() -> None:
    mgr = ObservabilityAlertManager()
    mgr.add_rule(_make_rule("r1", "cpu", 80.0, cooldown=0.0))
    mgr.evaluate("cpu", 95.0)
    firing = mgr.get_firing()
    assert len(firing) == 1


def test_clear_history() -> None:
    mgr = ObservabilityAlertManager()
    mgr.add_rule(_make_rule("r1", "cpu", 80.0, cooldown=0.0))
    mgr.evaluate("cpu", 95.0)
    mgr.clear_history()
    assert mgr.incident_count() == 0


def test_incident_to_dict() -> None:
    mgr = ObservabilityAlertManager()
    mgr.add_rule(_make_rule("r1", "cpu", 80.0, cooldown=0.0))
    fired = mgr.evaluate("cpu", 90.0)
    d = fired[0].to_dict()
    assert "incident_id" in d
    assert d["metric_name"] == "cpu"


def test_get_rule() -> None:
    mgr = ObservabilityAlertManager()
    mgr.add_rule(_make_rule("r1", "cpu", 80.0))
    rule = mgr.get_rule("r1")
    assert rule.rule_id == "r1"


def test_get_rule_missing_raises() -> None:
    mgr = ObservabilityAlertManager()
    with pytest.raises(AlertRuleNotFoundError):
        mgr.get_rule("ghost")
