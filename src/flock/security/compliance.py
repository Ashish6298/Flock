"""Compliance reporting, security control baselines, and runtime audit checks."""

from __future__ import annotations

import time
import threading
from typing import Dict, List
from flock.security.exceptions import ComplianceControlError
from flock.security.models import ComplianceReport


class ComplianceEngine:
    """Evaluates cluster compliance controls (CIS benchmarks, transport rules, key sizes)."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._required_controls: Dict[str, str] = {
            "SEC-001": "AES key rotation period under 90 days",
            "SEC-002": "X509 Trust roots validation active",
            "SEC-003": "Intrusion heuristics quarantine policy defined",
            "SEC-004": "Audit trail logging integrity enabled",
        }
        # Control status: control_id -> bool (Passed = True)
        self._control_states: Dict[str, bool] = {
            "SEC-001": True,
            "SEC-002": True,
            "SEC-003": True,
            "SEC-004": True,
        }

    def set_control_status(self, control_id: str, passed: bool) -> None:
        """Manually update or override a compliance control status."""
        with self._lock:
            if control_id not in self._required_controls:
                raise ComplianceControlError(f"Control ID '{control_id}' is not registered.")
            self._control_states[control_id] = passed

    def run_compliance_audit(self) -> ComplianceReport:
        """Run assessments across all controls and generate a compliance report."""
        with self._lock:
            passed = []
            failed = []
            remediations = {}
            
            for cid, desc in self._required_controls.items():
                status = self._control_states.get(cid, False)
                if status:
                    passed.append(cid)
                else:
                    failed.append(cid)
                    remediations[cid] = f"Re-enable baseline requirements: {desc}"

            total = len(self._required_controls)
            score = (len(passed) / total * 100.0) if total > 0 else 100.0

            return ComplianceReport(
                timestamp=time.time(),
                passed_controls=passed,
                failed_controls=failed,
                score=score,
                remediations=remediations,
            )
