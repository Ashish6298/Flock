"""Unit tests for Phase 40 Enterprise Policy-as-Code, Governance Automation & Compliance Orchestration Subsystem."""

import time
import pytest
from unittest.mock import MagicMock, AsyncMock

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.protocol.packet import MessageType
from flock.policy.exceptions import (
    PolicyError,
    PolicyCompilationError,
    PolicyEvaluationError,
)
from flock.policy.models import (
    PolicyRule,
    PolicyDefinition,
    ComplianceFrameworkReport,
)
from flock.policy.repository import PolicyRepository
from flock.policy.compiler import PolicyCompiler
from flock.policy.inheritance import PolicyInheritanceResolver
from flock.policy.engine import PolicyEvaluationEngine, PolicyResourceSelector
from flock.policy.remediation import RemediationPlanner, PolicyApprovalWorkflow
from flock.policy.bundles import PolicyBundleManager
from flock.policy.simulation import PolicySimulationEngine
from flock.policy.compliance import ComplianceOrchestrator
from flock.policy.metrics import PolicyMetricsTracker
from flock.policy.synchronization import PolicySynchronizer
from flock.policy.audit import PolicyAuditLogger
from flock.policy.coordinator import PolicyCoordinator
from flock.policy.service import PolicyService


# -----------------------------------------------------------------------------
# Compiler & Repository Tests
# -----------------------------------------------------------------------------

def test_compiler_and_repository() -> None:
    repo = PolicyRepository()
    
    payload = """
    {
        "policy_id": "pol-encryption",
        "version": "1.0.0",
        "target_selectors": {"env": "prod"},
        "rules": [
            {
                "name": "require-encryption",
                "condition": "encryption == True",
                "remediation_plan": "Enable SSL config parameters"
            }
        ]
    }
    """
    policy = PolicyCompiler.compile_policy(payload)
    assert policy.policy_id == "pol-encryption"
    assert len(policy.rules) == 1
    
    repo.store_policy(policy)
    assert repo.get_policy("pol-encryption").version == "1.0.0"
    
    # Invalid JSON
    with pytest.raises(PolicyCompilationError):
        PolicyCompiler.compile_policy("invalid-json-text")


# -----------------------------------------------------------------------------
# Evaluation Engine & Selector Tests
# -----------------------------------------------------------------------------

def test_evaluation_engine_and_selector() -> None:
    engine = PolicyEvaluationEngine()
    
    policy = PolicyDefinition(
        policy_id="pol-1",
        version="1.0.0",
        target_selectors={"env": "prod"},
        rules=[
            PolicyRule(name="r1", condition="encryption == True", remediation_plan="remedy-1"),
            PolicyRule(name="r2", condition="version >= 2.0", remediation_plan="remedy-2"),
        ]
    )
    
    # Evaluation passes
    res_ok = {"encryption": True, "version": 2.1}
    results = engine.evaluate_policy_rules(policy, res_ok)
    assert all(status for _, status, _ in results)
    
    # Evaluation fails
    res_fail = {"encryption": False, "version": 1.5}
    results_fail = engine.evaluate_policy_rules(policy, res_fail)
    assert not all(status for _, status, _ in results_fail)
    assert results_fail[0][2] == "remedy-1"
    
    # Resource selector
    assert PolicyResourceSelector.match_selectors({"env": "prod"}, {"env": "prod", "region": "east"}) is True
    assert PolicyResourceSelector.match_selectors({"env": "prod"}, {"env": "dev"}) is False


# -----------------------------------------------------------------------------
# Inheritance & Bundles Tests
# -----------------------------------------------------------------------------

def test_inheritance_and_bundles() -> None:
    repo = PolicyRepository()
    resolver = PolicyInheritanceResolver(repo)
    bm = PolicyBundleManager()
    
    parent = PolicyDefinition(
        policy_id="pol-parent",
        version="1.0.0",
        rules=[PolicyRule(name="parent-r", condition="active == True", remediation_plan="parent")]
    )
    repo.store_policy(parent)
    
    child = PolicyDefinition(
        policy_id="pol-child",
        version="1.0.0",
        parent_policy_id="pol-parent",
        rules=[PolicyRule(name="child-r", condition="encryption == True", remediation_plan="child")]
    )
    
    effective = resolver.resolve_effective_rules(child)
    assert len(effective.rules) == 2
    
    # Bundles
    bm.publish_bundle("b-1", [parent, child])
    assert len(bm.get_bundle("b-1")) == 2


# -----------------------------------------------------------------------------
# Approvals, Simulation & Compliance Tests
# -----------------------------------------------------------------------------

def test_approvals_simulation_and_compliance() -> None:
    engine = PolicyEvaluationEngine()
    workflow = PolicyApprovalWorkflow()
    sim = PolicySimulationEngine(engine)
    orchestrator = ComplianceOrchestrator(engine)
    
    workflow.approve_exception("pol-encryption", "cluster-1")
    assert workflow.has_exception("pol-encryption", "cluster-1") is True
    assert workflow.has_exception("pol-encryption", "cluster-2") is False
    
    policy = PolicyDefinition(
        policy_id="pol-1",
        version="1.0.0",
        rules=[PolicyRule(name="r1", condition="encryption == True", remediation_plan="remedy")]
    )
    
    # Simulation dry-run
    res = sim.simulate_policy_drill(policy, {"encryption": False})
    assert res[0][1] is False
    
    # ComplianceFrameworkReport SOC2
    report = orchestrator.run_framework_assessment("SOC2", [policy], {"encryption": True})
    assert report.framework_name == "SOC2"
    assert report.total_checks == 1
    assert report.passed_checks == 1


# -----------------------------------------------------------------------------
# Policy Service Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_policy_service_integration() -> None:
    bus = MagicMock(spec=MessageBus)
    bus.router = MagicMock()
    bus.send = AsyncMock()
    
    events = EventBus()
    event_list = []
    
    async def on_init(data: dict) -> None: # type: ignore[type-arg]
        event_list.append(data)
        
    events.subscribe("policy.initialized", on_init)
    
    service = PolicyService(bus, events)
    await service.start()
    
    assert service._running is True
    assert len(event_list) == 1
    assert service._bus.router.register.call_count == 2
    
    await service.stop()
    assert service._running is False
