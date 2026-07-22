"""Compliance framework auditing and standards report generation."""

from __future__ import annotations

import time
import threading
from typing import Dict, List, Any
from flock.policy.models import ComplianceFrameworkReport, PolicyDefinition
from flock.policy.engine import PolicyEvaluationEngine


class ComplianceOrchestrator:
    """Orchestrates assessments across standard profiles (CIS, SOC2, NIST)."""

    def __init__(self, eval_engine: PolicyEvaluationEngine) -> None:
        self._eval_engine = eval_engine
        self._lock = threading.RLock()

    def run_framework_assessment(
        self,
        framework_name: str,
        policies: List[PolicyDefinition],
        resource_attributes: Dict[str, Any],
    ) -> ComplianceFrameworkReport:
        """Run policy evaluations and compile standard compliance framework reports."""
        with self._lock:
            total_checks = 0
            passed_checks = 0
            failed_checks = 0
            remediations = {}
            
            for policy in policies:
                results = self._eval_engine.evaluate_policy_rules(policy, resource_attributes)
                for rule, status, rem in results:
                    total_checks += 1
                    if status:
                        passed_checks += 1
                    else:
                        failed_checks += 1
                        remediations[rule.name] = rem
                        
            return ComplianceFrameworkReport(
                framework_name=framework_name,
                timestamp=time.time(),
                total_checks=total_checks,
                passed_checks=passed_checks,
                failed_checks=failed_checks,
                remediations=remediations,
            )
