"""Policy Coordinator linking repository, compiler, engines, and compliance orchestrators."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional, Any
from flock.policy.repository import PolicyRepository
from flock.policy.compiler import PolicyCompiler
from flock.policy.inheritance import PolicyInheritanceResolver
from flock.policy.engine import PolicyEvaluationEngine
from flock.policy.remediation import RemediationPlanner, PolicyApprovalWorkflow
from flock.policy.bundles import PolicyBundleManager
from flock.policy.simulation import PolicySimulationEngine
from flock.policy.compliance import ComplianceOrchestrator
from flock.policy.metrics import PolicyMetricsTracker
from flock.policy.synchronization import PolicySynchronizer
from flock.policy.audit import PolicyAuditLogger


class PolicyCoordinator:
    """Consolidates repository catalog, policy compilers, evaluation engines, and compliance checkers."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        
        # Initialize policy subsystems
        self.repository = PolicyRepository()
        self.compiler = PolicyCompiler()
        self.inheritance = PolicyInheritanceResolver(self.repository)
        self.engine = PolicyEvaluationEngine()
        self.remediation = RemediationPlanner()
        self.approvals = PolicyApprovalWorkflow()
        self.bundles = PolicyBundleManager()
        self.simulation = PolicySimulationEngine(self.engine)
        self.compliance = ComplianceOrchestrator(self.engine)
        self.metrics = PolicyMetricsTracker()
        self.sync = PolicySynchronizer()
        self.audit = PolicyAuditLogger()
