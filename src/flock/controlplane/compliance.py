"""Fleet compliance reports builder."""

from __future__ import annotations

import time
import threading
from typing import Dict, List
from flock.controlplane.models import EnrolledCluster
from flock.controlplane.governance import GovernancePolicyManager


class ComplianceReporter:
    """Runs governance rules checks across enrolled clusters and produces metrics reports."""

    def __init__(self, policy_manager: GovernancePolicyManager) -> None:
        self._policy_mgr = policy_manager
        self._lock = threading.RLock()

    def generate_fleet_compliance_score(self, clusters: List[EnrolledCluster]) -> float:
        """Run policy evaluations over clusters and calculate a fleet compliance score percentage."""
        with self._lock:
            if not clusters:
                return 100.0
                
            passed = 0
            for c in clusters:
                try:
                    # If evaluate_compliance runs without raising GovernancePolicyError
                    # and returns True, it passes.
                    if self._policy_mgr.evaluate_compliance(c.cluster_id, c.version):
                        passed += 1
                except Exception:
                    pass
                    
            return (passed / len(clusters)) * 100.0
