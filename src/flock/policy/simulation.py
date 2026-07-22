"""Policy simulation dry-run engine."""

from __future__ import annotations

import threading
from typing import Dict, List, Any, Tuple
from flock.policy.models import PolicyDefinition, PolicyRule
from flock.policy.engine import PolicyEvaluationEngine


class PolicySimulationEngine:
    """Runs dry-run policy evaluation drills to check for drift or configuration warnings."""

    def __init__(self, eval_engine: PolicyEvaluationEngine) -> None:
        self._eval_engine = eval_engine
        self._lock = threading.RLock()

    def simulate_policy_drill(
        self,
        policy: PolicyDefinition,
        resource_attributes: Dict[str, Any],
    ) -> List[Tuple[PolicyRule, bool, str]]:
        """Simulate policy evaluation on a target resource without enforcing remediations.
        
        Returns:
            List of evaluation tuples.
        """
        with self._lock:
            # Under dry-run/simulation, we invoke evaluation logic directly
            return self._eval_engine.evaluate_policy_rules(policy, resource_attributes)
