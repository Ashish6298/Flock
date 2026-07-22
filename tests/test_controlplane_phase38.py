"""Unit tests for Phase 38 Enterprise Control Plane, Cluster Governance & Fleet Management Framework Subsystem."""

import time
import pytest
from unittest.mock import MagicMock, AsyncMock

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.protocol.packet import MessageType
from flock.controlplane.exceptions import (
    ControlPlaneError,
    FleetRegistrationError,
    ClusterEnrollmentError,
    GovernancePolicyError,
    FleetUpgradeError,
    MaintenanceWindowError,
    GlobalConfigurationError,
)
from flock.controlplane.models import (
    FleetInfo,
    EnrolledCluster,
    GovernancePolicy,
    FleetUpgradePlan,
    MaintenanceWindow,
)
from flock.controlplane.fleet import FleetRegistry
from flock.controlplane.organizations import OrganizationManager
from flock.controlplane.clusters import ClusterEnrollmentManager
from flock.controlplane.featureflags import FeatureFlagManager
from flock.controlplane.maintenance import MaintenanceManager
from flock.controlplane.upgrades import UpgradeOrchestrator
from flock.controlplane.configuration import ConfigurationManager
from flock.controlplane.governance import GovernancePolicyManager
from flock.controlplane.inventory import FleetInventoryCatalog
from flock.controlplane.compliance import ComplianceReporter
from flock.controlplane.analytics import FleetAnalyticsEngine
from flock.controlplane.audit import ControlPlaneAuditLogger
from flock.controlplane.coordinator import ControlPlaneCoordinator
from flock.controlplane.service import ControlPlaneService


# -----------------------------------------------------------------------------
# Fleet & Organizations Tests
# -----------------------------------------------------------------------------

def test_fleet_and_organizations() -> None:
    fleet_reg = FleetRegistry()
    org_mgr = OrganizationManager()
    
    fleet = FleetInfo(fleet_id="f-1", organization_id="org-1", name="prod-fleet")
    fleet_reg.register_fleet(fleet)
    assert fleet_reg.get_fleet("f-1").name == "prod-fleet"
    
    org_mgr.add_tenant_member("org-1", "f-1")
    assert org_mgr.is_member("org-1", "f-1") is True
    assert org_mgr.is_member("org-1", "f-2") is False


# -----------------------------------------------------------------------------
# Cluster Enrollment Tests
# -----------------------------------------------------------------------------

def test_cluster_enrollment() -> None:
    mgr = ClusterEnrollmentManager()
    c = EnrolledCluster(
        cluster_id="c-1",
        fleet_id="f-1",
        name="us-east-cluster",
        version="1.0.0",
        labels={"region": "east"},
        features_active=["Raft"],
        last_seen=time.time(),
    )
    mgr.enroll_cluster(c)
    assert mgr.get_cluster("c-1").version == "1.0.0"
    
    # Heartbeat
    now = time.time()
    mgr.update_cluster_heartbeat("c-1", now)
    assert mgr.get_cluster("c-1").last_seen == now
    
    mgr.remove_cluster("c-1")
    with pytest.raises(ClusterEnrollmentError):
        mgr.get_cluster("c-1")


# -----------------------------------------------------------------------------
# Feature Flags Tests
# -----------------------------------------------------------------------------

def test_feature_flags() -> None:
    ff = FeatureFlagManager()
    ff.define_flag("alpha-mode", default_enabled=False)
    assert ff.is_feature_enabled("alpha-mode") is False
    
    ff.enable_flag("alpha-mode")
    assert ff.is_feature_enabled("alpha-mode") is True
    
    ff.define_flag("beta-mode", default_enabled=False)
    ff.target_flag_to_cluster("beta-mode", "c-2")
    assert ff.is_feature_enabled("beta-mode", "c-1") is False
    assert ff.is_feature_enabled("beta-mode", "c-2") is True


# -----------------------------------------------------------------------------
# Maintenance Manager Tests
# -----------------------------------------------------------------------------

def test_maintenance_windows() -> None:
    mm = MaintenanceManager()
    now = time.time()
    w = MaintenanceWindow(
        window_id="w-1",
        cluster_id="c-1",
        start_time=now - 100,
        end_time=now + 100,
        description="OS patching",
    )
    mm.schedule_maintenance(w)
    
    assert mm.is_in_maintenance("c-1", now) is True
    assert mm.is_in_maintenance("c-1", now + 200) is False
    
    # Invalid time range
    invalid_w = MaintenanceWindow(
        window_id="w-2",
        cluster_id="c-1",
        start_time=now + 100,
        end_time=now,
        description="invalid",
    )
    with pytest.raises(MaintenanceWindowError):
        mm.schedule_maintenance(invalid_w)


# -----------------------------------------------------------------------------
# Rolling Upgrades Tests
# -----------------------------------------------------------------------------

def test_upgrades_orchestrator() -> None:
    orchestrator = UpgradeOrchestrator()
    plan = FleetUpgradePlan(
        upgrade_id="u-1",
        target_version="1.1.0",
        batch_size=2,
        state="scheduled",
        cluster_states={"c-1": "pending", "c-2": "pending"},
    )
    orchestrator.schedule_upgrade(plan)
    assert orchestrator.get_upgrade_plan("u-1").state == "scheduled"
    
    orchestrator.set_cluster_upgrade_status("u-1", "c-1", "upgraded")
    assert orchestrator.get_upgrade_plan("u-1").cluster_states["c-1"] == "upgraded"


# -----------------------------------------------------------------------------
# Configuration Manager Tests
# -----------------------------------------------------------------------------

def test_configuration_manager() -> None:
    cm = ConfigurationManager()
    cm.set_config("max_tasks", "100")
    assert cm.get_config("max_tasks") == "100"
    assert cm.get_config_version("max_tasks") == 1
    
    # Update config key
    cm.set_config("max_tasks", "200")
    assert cm.get_config("max_tasks") == "200"
    assert cm.get_config_version("max_tasks") == 2
    
    with pytest.raises(GlobalConfigurationError):
        cm.set_config("", "value")


# -----------------------------------------------------------------------------
# Governance Compliance & Inventory Catalog Tests
# -----------------------------------------------------------------------------

def test_governance_and_compliance() -> None:
    gov = GovernancePolicyManager()
    comp = ComplianceReporter(gov)
    catalog = FleetInventoryCatalog()
    
    p = GovernancePolicy(
        policy_id="gov-1",
        rule_name="min_version_check",
        action_type="enforce",
        parameters={"min_version": "1.0.0"},
    )
    gov.register_policy(p)
    
    c1 = EnrolledCluster(
        cluster_id="c-1",
        fleet_id="f-1",
        name="cluster-1",
        version="1.0.0",
        labels={"region": "east"},
        features_active=[],
        last_seen=time.time(),
    )
    c2 = EnrolledCluster(
        cluster_id="c-2",
        fleet_id="f-1",
        name="cluster-2",
        version="0.9.0",
        labels={"region": "west"},
        features_active=[],
        last_seen=time.time(),
    )
    
    catalog.index_cluster_labels("c-1", c1.labels)
    catalog.index_cluster_labels("c-2", c2.labels)
    assert "c-1" in catalog.search_by_label("region", "east")
    
    # Compliant check
    assert gov.evaluate_compliance("c-1", "1.0.0") is True
    
    # Enforced violation raises error
    with pytest.raises(GovernancePolicyError):
        gov.evaluate_compliance("c-2", "0.9.0")
        
    score = comp.generate_fleet_compliance_score([c1, c2])
    assert score == 50.0  # 1 passes, 1 fails


# -----------------------------------------------------------------------------
# Control Plane Service Integration Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_control_plane_service_integration() -> None:
    bus = MagicMock(spec=MessageBus)
    bus.router = MagicMock()
    bus.send = AsyncMock()
    
    events = EventBus()
    event_list = []
    
    async def on_init(data: dict) -> None: # type: ignore[type-arg]
        event_list.append(data)
        
    events.subscribe("controlplane.initialized", on_init)
    
    service = ControlPlaneService("node-1", bus, events)
    await service.start()
    
    assert service._running is True
    assert len(event_list) == 1
    assert service._bus.router.register.call_count == 2
    
    await service.stop()
    assert service._running is False
