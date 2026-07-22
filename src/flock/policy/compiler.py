"""Policy-as-Code declarative JSON/YAML parser and compiler."""

from __future__ import annotations

import json
from typing import Dict, Any, List
from flock.policy.exceptions import PolicyCompilationError
from flock.policy.models import PolicyDefinition, PolicyRule


class PolicyCompiler:
    """Parses declarative configuration schemas and compiles them into PolicyDefinition models."""

    @staticmethod
    def compile_policy(raw_payload: str) -> PolicyDefinition:
        """Parse raw JSON string into a compiled PolicyDefinition model.
        
        Raises:
            PolicyCompilationError: If parsing or required fields verification fails.
        """
        try:
            data = json.loads(raw_payload)
        except Exception as exc:
            raise PolicyCompilationError(f"Failed to parse raw policy payload JSON: {exc}") from exc
            
        pid = data.get("policy_id")
        ver = data.get("version", "1.0.0")
        selectors = data.get("target_selectors", {})
        parent = data.get("parent_policy_id")
        raw_rules = data.get("rules", [])
        
        if not pid:
            raise PolicyCompilationError("Missing required field 'policy_id' in policy payload.")
            
        rules: List[PolicyRule] = []
        for r in raw_rules:
            name = r.get("name")
            cond = r.get("condition")
            rem = r.get("remediation_plan", "Notify administrator")
            
            if not name or not cond:
                raise PolicyCompilationError("Rule definition must specify 'name' and 'condition' fields.")
                
            rules.append(PolicyRule(name=name, condition=cond, remediation_plan=rem))
            
        return PolicyDefinition(
            policy_id=pid,
            version=ver,
            target_selectors=selectors,
            rules=rules,
            parent_policy_id=parent,
        )
