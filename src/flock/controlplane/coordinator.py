"""Control Plane Coordinator linking registries, policies, rollouts, and maintenance managers."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional, Any
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


class ControlPlaneCoordinator:
    """Consolidates fleet inventory registries, rolling upgrade managers, and feature flags engines."""

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        self._lock = threading.RLock()
        
        # Initialize control plane subsystems
        self.fleet = FleetRegistry()
        self.organizations = OrganizationManager()
        self.clusters = ClusterEnrollmentManager()
        self.featureflags = FeatureFlagManager()
        self.maintenance = MaintenanceManager()
        self.upgrades = UpgradeOrchestrator()
        self.configuration = ConfigurationManager()
        self.governance = GovernancePolicyManager()
        self.inventory = FleetInventoryCatalog()
        self.compliance = ComplianceReporter(self.governance)
        self.analytics = FleetAnalyticsEngine()
        self.audit = ControlPlaneAuditLogger()
