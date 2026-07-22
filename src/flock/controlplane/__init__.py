"""Init for controlplane package. Exposes all Control Plane, Fleet Management, and Governance interfaces."""

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
    FleetMetricsReport,
)
from flock.controlplane.fleet import FleetRegistry
from flock.controlplane.organizations import OrganizationManager
from flock.controlplane.clusters import ClusterEnrollmentManager
from flock.controlplane.featureflags import FeatureFlagManager
from flock.controlplane.maintenance import MaintenanceManager
from flock.controlplane.upgrades import UpgradeOrchestrator
from flock.controlplane.configuration import ConfigurationManager
from flock.controlplane.governance import GovernancePolicyManager
from flock.controlplane.policies import GovernancePolicyManager as GovernancePolicyManagerAlias
from flock.controlplane.inventory import FleetInventoryCatalog
from flock.controlplane.compliance import ComplianceReporter
from flock.controlplane.analytics import FleetAnalyticsEngine
from flock.controlplane.audit import ControlPlaneAuditLogger
from flock.controlplane.coordinator import ControlPlaneCoordinator
from flock.controlplane.service import ControlPlaneService

__all__ = [
    # Exceptions
    "ControlPlaneError",
    "FleetRegistrationError",
    "ClusterEnrollmentError",
    "GovernancePolicyError",
    "FleetUpgradeError",
    "MaintenanceWindowError",
    "GlobalConfigurationError",
    
    # Models
    "FleetInfo",
    "EnrolledCluster",
    "GovernancePolicy",
    "FleetUpgradePlan",
    "MaintenanceWindow",
    "FleetMetricsReport",
    
    # Engines & Managers
    "FleetRegistry",
    "OrganizationManager",
    "ClusterEnrollmentManager",
    "FeatureFlagManager",
    "MaintenanceManager",
    "UpgradeOrchestrator",
    "ConfigurationManager",
    "GovernancePolicyManager",
    "FleetInventoryCatalog",
    "ComplianceReporter",
    "FleetAnalyticsEngine",
    "ControlPlaneAuditLogger",
    "ControlPlaneCoordinator",
    "ControlPlaneService",
]
