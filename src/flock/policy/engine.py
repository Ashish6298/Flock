"""Policy evaluation engine with condition match checks."""

from __future__ import annotations

import threading
from typing import Dict, List, Any, Tuple
from flock.policy.exceptions import PolicyEvaluationError
from flock.policy.models import PolicyDefinition, PolicyRule


class PolicyEvaluationEngine:
    """Evaluates rules conditions over target resource attribute configurations."""

    def __init__(self) -> None:
        self._lock = threading.RLock()

    def evaluate_policy_rules(
        self,
        policy: PolicyDefinition,
        resource_attributes: Dict[str, Any],
    ) -> List[Tuple[PolicyRule, bool, str]]:
        """Evaluate all rules within a policy against a resource attributes dictionary.
        
        Returns:
            List of tuples of (Rule, Passed status, Remediation text description)
        """
        with self._lock:
            results = []
            for rule in policy.rules:
                passed, reason = self._evaluate_rule_condition(rule.condition, resource_attributes)
                results.append((rule, passed, rule.remediation_plan if not passed else ""))
            return results

    def _evaluate_rule_condition(self, condition: str, attributes: Dict[str, Any]) -> Tuple[bool, str]:
        """Simple and safe evaluator of rule conditions.
        
        Condition strings like:
          - "encryption == True"
          - "version >= '1.0.0'"
        """
        import re
        try:
            # Simple attribute key-value extraction check
            match = re.match(r"^([a-zA-Z0-9_\.\-]+)\s*(==|>=|<=|>|<|!=)\s*(.+)$", condition.strip())
            if not match:
                # Fallback to direct key existence check
                key = condition.strip()
                if key in attributes:
                    return bool(attributes[key]), f"Key '{key}' evaluation completed."
                return False, f"Condition syntax error or missing key: {condition}"
                
            key, op, val_str = match.groups()
            if key not in attributes:
                return False, f"Attribute key '{key}' not found in resource context."
                
            actual = attributes[key]
            
            # Parse target value
            val_clean = val_str.strip().strip("'").strip('"')
            if val_clean.lower() == "true":
                expected: Any = True
            elif val_clean.lower() == "false":
                expected = False
            else:
                try:
                    expected = float(val_clean)
                    actual = float(actual)
                except Exception:
                    expected = val_clean
                    
            # Perform check
            if op == "==":
                status = (actual == expected)
            elif op == "!=":
                status = (actual != expected)
            elif op == ">=":
                status = (actual >= expected)
            elif op == "<=":
                status = (actual <= expected)
            elif op == ">":
                status = (actual > expected)
            elif op == "<":
                status = (actual < expected)
            else:
                status = False
                
            return status, f"Evaluated condition '{condition}' successfully."
        except Exception as exc:
            return False, f"Condition evaluation error: {exc}"
class PolicyResourceSelector:
    """Matches resource selectors constraints (labels) against target resource tags."""

    @staticmethod
    def match_selectors(selectors: Dict[str, str], resource_labels: Dict[str, str]) -> bool:
        """Returns True if the resource labels satisfy all policy selector key/value rules."""
        for k, v in selectors.items():
            if resource_labels.get(k) != v:
                return False
        return True
