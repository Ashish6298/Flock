"""Dashboard Alert Engine.

Evaluates alert rules against incoming metric data points and
dispatches :class:`~flock.dashboard.models.AlertEvent` notifications
to registered recipient handlers.  Alert evaluation is purely
in-process and does not depend on external messaging infrastructure.
"""

import threading
import time
from typing import Callable, Dict, List

from flock.dashboard.exceptions import AlertRuleError
from flock.dashboard.models import AlertDefinition, AlertEvent, MetricDataPoint


# Handler receives the triggered AlertEvent for routing.
AlertHandler = Callable[[AlertEvent], None]


class AlertEngine:
    """Thread-safe alert rule evaluator for dashboard metrics.

    Alert rules are registered as :class:`AlertDefinition` instances.
    Each call to :meth:`evaluate` checks every registered rule against
    the supplied data point; matching rules fire an
    :class:`AlertEvent` delivered to all registered handlers.

    Attributes:
        _lock: Reentrant lock protecting rule and handler stores.
        _rules: Mapping of alert_id to AlertDefinition.
        _handlers: List of registered alert handler callables.
        _triggered: List of all alert events fired in this session.
    """

    def __init__(self) -> None:
        """Initialise the alert engine with empty rule and handler sets."""
        self._lock: threading.RLock = threading.RLock()
        self._rules: Dict[str, AlertDefinition] = {}
        self._handlers: List[AlertHandler] = []
        self._triggered: List[AlertEvent] = []

    # ------------------------------------------------------------------
    # Rule management
    # ------------------------------------------------------------------

    def add_rule(self, rule: AlertDefinition) -> None:
        """Register an alert rule.

        Args:
            rule: The :class:`AlertDefinition` to register.

        Raises:
            AlertRuleError: If a rule with the same ``alert_id``
                is already registered.
        """
        with self._lock:
            if rule.alert_id in self._rules:
                raise AlertRuleError(
                    f"Alert rule '{rule.alert_id}' is already registered."
                )
            self._rules[rule.alert_id] = rule

    def remove_rule(self, alert_id: str) -> None:
        """Remove a registered alert rule.

        Args:
            alert_id: Identifier of the rule to remove.

        Raises:
            AlertRuleError: If ``alert_id`` is not registered.
        """
        with self._lock:
            if alert_id not in self._rules:
                raise AlertRuleError(
                    f"Alert rule '{alert_id}' is not registered."
                )
            del self._rules[alert_id]

    def list_rules(self) -> List[AlertDefinition]:
        """Return all registered alert rules."""
        with self._lock:
            return list(self._rules.values())

    def get_rule(self, alert_id: str) -> AlertDefinition:
        """Return a specific alert rule by identifier.

        Args:
            alert_id: Identifier to look up.

        Returns:
            The matching :class:`AlertDefinition`.

        Raises:
            AlertRuleError: If ``alert_id`` is not registered.
        """
        with self._lock:
            if alert_id not in self._rules:
                raise AlertRuleError(
                    f"Alert rule '{alert_id}' is not registered."
                )
            return self._rules[alert_id]

    def rule_exists(self, alert_id: str) -> bool:
        """Return ``True`` if an alert rule with the given ID exists."""
        with self._lock:
            return alert_id in self._rules

    # ------------------------------------------------------------------
    # Handler management
    # ------------------------------------------------------------------

    def add_handler(self, handler: AlertHandler) -> None:
        """Register an alert event handler.

        Args:
            handler: Callable that receives fired :class:`AlertEvent`
                instances.
        """
        with self._lock:
            self._handlers.append(handler)

    def clear_handlers(self) -> None:
        """Remove all registered alert handlers."""
        with self._lock:
            self._handlers.clear()

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate(self, point: MetricDataPoint) -> List[AlertEvent]:
        """Evaluate a metric data point against all registered rules.

        For each rule whose ``metric_name`` matches and whose
        ``threshold`` is exceeded, an :class:`AlertEvent` is created,
        stored, and dispatched to every registered handler.

        Args:
            point: The :class:`MetricDataPoint` to evaluate.

        Returns:
            List of :class:`AlertEvent` instances that were fired.
        """
        fired: List[AlertEvent] = []
        with self._lock:
            matching_rules = [
                r for r in self._rules.values()
                if r.metric_name == point.metric_name
                and point.value > r.threshold
            ]
            handlers = list(self._handlers)

        for rule in matching_rules:
            event = AlertEvent(
                alert_id=rule.alert_id,
                triggered_at=time.time(),
                current_value=point.value,
                message=(
                    f"Alert '{rule.alert_id}': {point.metric_name} = "
                    f"{point.value:.4f} exceeds threshold {rule.threshold:.4f}"
                ),
            )
            with self._lock:
                self._triggered.append(event)
            fired.append(event)
            for handler in handlers:
                try:
                    handler(event)
                except Exception:
                    pass  # Handlers must not crash the evaluation loop.

        return fired

    def evaluate_batch(
        self, points: List[MetricDataPoint]
    ) -> List[AlertEvent]:
        """Evaluate a batch of metric points and return all fired events.

        Args:
            points: Sequence of :class:`MetricDataPoint` to evaluate.

        Returns:
            Flat list of all :class:`AlertEvent` instances fired.
        """
        all_events: List[AlertEvent] = []
        for point in points:
            all_events.extend(self.evaluate(point))
        return all_events

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def get_triggered_events(self) -> List[AlertEvent]:
        """Return all alert events fired in this session."""
        with self._lock:
            return list(self._triggered)

    def clear_history(self) -> None:
        """Clear the triggered-event history."""
        with self._lock:
            self._triggered.clear()

    def count_triggered(self) -> int:
        """Return the number of alert events fired in this session."""
        with self._lock:
            return len(self._triggered)
