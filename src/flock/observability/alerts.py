"""Observability Alert Manager – Phase 34.

Threshold and anomaly-based alert rules evaluated against metric
observations.  Includes cooldown periods, acknowledgement states,
suppression, escalation levels, and EventBus notification hooks.

This module is separate from ``flock.dashboard.alerts`` which handles
*dashboard panel* alerting.  The observability alert manager operates
on raw metric observations and integrates with the telemetry pipeline.
"""

from __future__ import annotations

import threading
import time
from enum import Enum
from typing import Callable, Dict, List, Optional, Set

from flock.observability.exceptions import AlertError, AlertRuleNotFoundError


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertState(str, Enum):
    """Lifecycle state of a triggered alert."""

    FIRING = "firing"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class AlertRule:
    """Configuration for a single alert rule.

    Attributes:
        rule_id: Unique identifier.
        metric_name: Metric to watch.
        threshold: Trigger when value exceeds this.
        severity: Alert severity.
        cooldown_seconds: Minimum seconds between successive firings.
        description: Human-readable description.
    """

    def __init__(
        self,
        rule_id: str,
        metric_name: str,
        threshold: float,
        severity: AlertSeverity = AlertSeverity.WARNING,
        cooldown_seconds: float = 60.0,
        description: str = "",
    ) -> None:
        self.rule_id: str = rule_id
        self.metric_name: str = metric_name
        self.threshold: float = threshold
        self.severity: AlertSeverity = severity
        self.cooldown_seconds: float = cooldown_seconds
        self.description: str = description


class AlertIncident:
    """A triggered alert incident.

    Attributes:
        incident_id: Unique identifier.
        rule_id: Source rule identifier.
        metric_name: Metric that triggered.
        observed_value: Value that caused the trigger.
        threshold: Threshold that was exceeded.
        severity: Alert severity.
        state: Current lifecycle state.
        triggered_at: Unix epoch timestamp.
        acknowledged_at: When acknowledged, or ``None``.
        resolved_at: When resolved, or ``None``.
        message: Human-readable alert message.
    """

    def __init__(
        self,
        incident_id: str,
        rule_id: str,
        metric_name: str,
        observed_value: float,
        threshold: float,
        severity: AlertSeverity,
        message: str,
        triggered_at: float,
    ) -> None:
        self.incident_id: str = incident_id
        self.rule_id: str = rule_id
        self.metric_name: str = metric_name
        self.observed_value: float = observed_value
        self.threshold: float = threshold
        self.severity: AlertSeverity = severity
        self.state: AlertState = AlertState.FIRING
        self.triggered_at: float = triggered_at
        self.acknowledged_at: Optional[float] = None
        self.resolved_at: Optional[float] = None
        self.message: str = message

    def to_dict(self) -> Dict:  # type: ignore[type-arg]
        """Serialise the incident to a plain dict."""
        return {
            "incident_id": self.incident_id,
            "rule_id": self.rule_id,
            "metric_name": self.metric_name,
            "observed_value": self.observed_value,
            "threshold": self.threshold,
            "severity": self.severity.value,
            "state": self.state.value,
            "triggered_at": self.triggered_at,
            "acknowledged_at": self.acknowledged_at,
            "resolved_at": self.resolved_at,
            "message": self.message,
        }


# Handler callable receives an AlertIncident on fire.
AlertHandler = Callable[[AlertIncident], None]


class ObservabilityAlertManager:
    """Thread-safe alert rule evaluator for the observability pipeline.

    Alert rules are registered with metric names and thresholds.
    :meth:`evaluate` is called with a metric name and its current value;
    matching rules that are not in cooldown fire new incidents.

    Attributes:
        _lock: Reentrant lock protecting all mutable state.
        _rules: Registered alert rules.
        _incidents: All triggered incidents (history).
        _active: Currently firing/acknowledged incidents by rule_id.
        _last_fired: Per-rule last-fired timestamps for cooldown.
        _suppressed: Rule IDs with active suppression.
        _handlers: Registered notification handlers.
    """

    def __init__(self) -> None:
        """Initialise the alert manager."""
        import uuid
        self._uuid = uuid
        self._lock: threading.RLock = threading.RLock()
        self._rules: Dict[str, AlertRule] = {}
        self._incidents: List[AlertIncident] = []
        self._active: Dict[str, AlertIncident] = {}
        self._last_fired: Dict[str, float] = {}
        self._suppressed: Set[str] = set()
        self._handlers: List[AlertHandler] = []

    # ------------------------------------------------------------------
    # Rule management
    # ------------------------------------------------------------------

    def add_rule(self, rule: AlertRule) -> None:
        """Register an alert rule.

        Args:
            rule: Rule to add.

        Raises:
            AlertError: If a rule with the same ID already exists.
        """
        with self._lock:
            if rule.rule_id in self._rules:
                raise AlertError(
                    f"Alert rule '{rule.rule_id}' already registered."
                )
            self._rules[rule.rule_id] = rule

    def remove_rule(self, rule_id: str) -> None:
        """Remove a rule.

        Args:
            rule_id: Rule to remove.

        Raises:
            AlertRuleNotFoundError: If the rule is not found.
        """
        with self._lock:
            if rule_id not in self._rules:
                raise AlertRuleNotFoundError(
                    f"Alert rule '{rule_id}' not found."
                )
            del self._rules[rule_id]

    def get_rule(self, rule_id: str) -> AlertRule:
        """Return a registered rule by ID."""
        with self._lock:
            if rule_id not in self._rules:
                raise AlertRuleNotFoundError(
                    f"Alert rule '{rule_id}' not found."
                )
            return self._rules[rule_id]

    def list_rules(self) -> List[AlertRule]:
        """Return all registered rules."""
        with self._lock:
            return list(self._rules.values())

    # ------------------------------------------------------------------
    # Suppression
    # ------------------------------------------------------------------

    def suppress(self, rule_id: str) -> None:
        """Suppress a rule so it does not fire new incidents."""
        with self._lock:
            self._suppressed.add(rule_id)

    def unsuppress(self, rule_id: str) -> None:
        """Remove suppression from a rule."""
        with self._lock:
            self._suppressed.discard(rule_id)

    def is_suppressed(self, rule_id: str) -> bool:
        """Return ``True`` if the rule is suppressed."""
        with self._lock:
            return rule_id in self._suppressed

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def add_handler(self, handler: AlertHandler) -> None:
        """Register a notification handler.

        Args:
            handler: Called with each new :class:`AlertIncident`.
        """
        with self._lock:
            self._handlers.append(handler)

    def clear_handlers(self) -> None:
        """Remove all registered handlers."""
        with self._lock:
            self._handlers.clear()

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate(
        self, metric_name: str, value: float
    ) -> List[AlertIncident]:
        """Evaluate a metric value against all registered rules.

        Rules that match (value > threshold) and are not in cooldown or
        suppressed will fire a new :class:`AlertIncident`.

        Args:
            metric_name: Metric being reported.
            value: Current metric value.

        Returns:
            List of newly fired incidents.
        """
        now = time.time()
        fired: List[AlertIncident] = []

        with self._lock:
            matching = [
                r for r in self._rules.values()
                if r.metric_name == metric_name
            ]
            handlers = list(self._handlers)

        for rule in matching:
            if value <= rule.threshold:
                continue
            with self._lock:
                suppressed = rule.rule_id in self._suppressed
                last = self._last_fired.get(rule.rule_id, 0.0)

            if suppressed:
                continue
            if now - last < rule.cooldown_seconds:
                continue

            incident = AlertIncident(
                incident_id=str(self._uuid.uuid4()),
                rule_id=rule.rule_id,
                metric_name=metric_name,
                observed_value=value,
                threshold=rule.threshold,
                severity=rule.severity,
                message=(
                    f"[{rule.severity.value.upper()}] "
                    f"{metric_name}={value:.4f} "
                    f"exceeds {rule.threshold:.4f} "
                    f"(rule: {rule.rule_id})"
                ),
                triggered_at=now,
            )

            with self._lock:
                self._incidents.append(incident)
                self._active[rule.rule_id] = incident
                self._last_fired[rule.rule_id] = now

            fired.append(incident)
            for handler in handlers:
                try:
                    handler(incident)
                except Exception:
                    pass

        return fired

    # ------------------------------------------------------------------
    # Incident management
    # ------------------------------------------------------------------

    def acknowledge(self, incident_id: str) -> None:
        """Acknowledge a firing incident.

        Args:
            incident_id: Incident to acknowledge.

        Raises:
            AlertRuleNotFoundError: If the incident is not found.
        """
        with self._lock:
            for incident in self._incidents:
                if incident.incident_id == incident_id:
                    incident.state = AlertState.ACKNOWLEDGED
                    incident.acknowledged_at = time.time()
                    return
        raise AlertRuleNotFoundError(
            f"Incident '{incident_id}' not found."
        )

    def resolve(self, incident_id: str) -> None:
        """Mark an incident as resolved.

        Args:
            incident_id: Incident to resolve.

        Raises:
            AlertRuleNotFoundError: If the incident is not found.
        """
        with self._lock:
            for incident in self._incidents:
                if incident.incident_id == incident_id:
                    incident.state = AlertState.RESOLVED
                    incident.resolved_at = time.time()
                    return
        raise AlertRuleNotFoundError(
            f"Incident '{incident_id}' not found."
        )

    def get_firing(self) -> List[AlertIncident]:
        """Return all currently firing incidents."""
        with self._lock:
            return [
                i for i in self._incidents
                if i.state == AlertState.FIRING
            ]

    def get_all_incidents(self) -> List[AlertIncident]:
        """Return all incidents (any state)."""
        with self._lock:
            return list(self._incidents)

    def incident_count(self) -> int:
        """Return total number of incidents."""
        with self._lock:
            return len(self._incidents)

    def clear_history(self) -> None:
        """Clear all incident history."""
        with self._lock:
            self._incidents.clear()
            self._active.clear()
