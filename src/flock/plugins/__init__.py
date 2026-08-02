"""Plugin Subsystem — Flock Plugin SDK & Extension API.

Exports the complete public surface for Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6, and Phase 7.
"""

# Phase 1 — Plugin SDK & Extension API
from flock.plugins.exceptions import (
    PluginError,
    PluginNotFoundError,
    PluginAlreadyInstalledError,
    PluginDependencyError,
    PluginCompatibilityError,
    PluginValidationError,
    PluginSignatureError,
    PluginActivationError,
    PluginSandboxError,
    PluginConfigurationError,
    PluginExecutionError,
    # Phase 2 lifecycle exceptions
    PluginLifecycleError,
    PluginInvalidTransitionError,
    PluginEventDispatchError,
    PluginLifecycleStateError,
    # Phase 3 dependency exceptions
    PluginDependencyResolutionError,
    PluginMissingDependencyError,
    PluginDependencyVersionConflictError,
    PluginCircularDependencyError,
    PluginInvalidDependencySpecError,
    # Phase 3 communication exceptions
    PluginCommunicationError,
    PluginEventBusError,
    PluginMessageValidationError,
    PluginMessageTimeoutError,
    PluginMessageDeliveryError,
    # Phase 4 security exceptions
    PluginSecurityError,
    PluginPermissionDeniedError,
    PluginCapabilityMismatchError,
    PluginSecurityPolicyViolationError,
    # Phase 5 service exceptions
    PluginServiceError,
    ServiceRegistrationError,
    ServiceResolutionError,
    ServiceDependencyError,
    ServiceInjectionError,
    DuplicateServiceError,
    # Phase 6 packaging exceptions
    PluginPackagingError,
    PluginPackageValidationError,
    PluginPackageIntegrityError,
    PluginInstallationError,
    PluginExportError,
    PluginImportError,
    PluginDistributionError,
    # Phase 7 diagnostics exceptions
    PluginDiagnosticsError,
    PluginHealthCheckError,
    PluginTelemetryError,
    PluginStatisticsError,
    PluginHealthReportError,
    PluginRuntimeInspectionError,
)
from flock.plugins.models import (
    PluginManifest,
    PluginConfiguration,
    PluginHealthReport,
    PluginContext,
)
from flock.plugins.registry import PluginRegistry
from flock.plugins.loader import PluginLoader
from flock.plugins.sandbox import PluginSandbox
from flock.plugins.resolver import PluginDependencyResolver
from flock.plugins.service import PluginService
from flock.plugins.base import FlockPlugin
from flock.plugins.validation import PluginValidator
from flock.plugins.discovery import PluginDiscovery

# Phase 2 — Plugin Lifecycle & Event System
from flock.plugins.lifecycle_models import (
    PluginLifecycleState,
    PluginEventType,
    PluginLifecycleTransition,
    PluginEventPayload,
    PluginStatus,
    PluginEventSubscription,
)
from flock.plugins.events import PluginEventDispatcher, PluginEventBus
from flock.plugins.lifecycle import PluginLifecycleEngine

# Phase 3 — Plugin Dependency Management & Resolution Models
from flock.plugins.dependency_models import (
    VersionOperator,
    DependencyConstraint,
    DependencySpec,
    DependencyResolutionResult,
    PlanStepType,
    InstallationStep,
    DependencyInstallationPlan,
)

# Phase 3 — Plugin Communication Models and Engines
from flock.plugins.models import (
    PluginEventPriority,
    PluginEvent,
    PluginMessage,
    PluginSubscription,
    PluginBroadcast,
    PluginResponse,
)
from flock.plugins.messaging import PluginMessagingEngine

# Phase 4 — Plugin Security, Sandboxing & Permission Models
from flock.plugins.models import (
    PermissionScope,
    PluginPermission,
    PluginCapability,
    SecurityPolicy,
    SecurityViolation,
    PermissionDecision,
    SandboxConfiguration,
    PluginAuditEntry,
    PermissionRequest,
)
from flock.plugins.security import PluginSecurityManager

# Phase 5 — Plugin Service Registry & Dependency Injection
from flock.plugins.models import (
    ServiceDescriptor,
    ServiceDependency,
    ServiceRegistration,
    ServiceResolution,
    InjectionContext,
)
from flock.plugins.services import PluginServiceRegistry

# Phase 6 — Plugin Packaging, Distribution & Marketplace Foundation
from flock.plugins.models import (
    PluginPackageMetadata,
    PluginSignature,
    PluginPackageValidationResult,
    PluginArchive,
    PluginPackageManifest,
    PluginPackage,
    PluginDistributionTarget,
    PluginInstallationRecord,
)
from flock.plugins.packaging import PluginPackagingEngine

# Phase 7 — Plugin Diagnostics, Health Monitoring & Telemetry
from flock.plugins.models import (
    PluginHealthStatus,
    PluginHealthSnapshot,
    PluginDiagnosticRecord,
    PluginTelemetryEvent,
    PluginStatistics,
    PluginRuntimeMetrics,
    PluginFailureRecord,
    PluginDiagnosticSummary,
    PluginTelemetryHealthReport,
)
from flock.plugins.diagnostics import PluginDiagnosticsEngine

# Phase 8 — Plugin Configuration Management & Persistence
from flock.plugins.exceptions import (
    PluginSettingsConfigurationError,
    PluginConfigurationValidationError,
    PluginConfigurationMigrationError,
    PluginConfigurationPersistenceError,
    PluginConfigurationImportError,
    PluginConfigurationExportError,
    PluginConfigurationConflictError,
)
from flock.plugins.models import (
    PluginConfigurationField,
    PluginConfigurationSchema,
    PluginConfigurationProfile,
    PluginConfigurationVersion,
    PluginConfigurationSnapshot,
    PluginConfigurationHistory,
    PluginConfigurationMigration,
    PluginConfigurationValidationResult,
    PluginConfigurationExport,
)
from flock.plugins.configuration import PluginConfigurationEngine

# Phase 8 (Certification) — Plugin Testing, Certification & QA
from flock.plugins.exceptions import (
    PluginCertificationError,
    PluginComplianceError,
    PluginQualityValidationError,
    PluginCertificationFailure,
    PluginAuditError,
)
from flock.plugins.models import (
    PluginCertificationStatus,
    PluginCertificationCheck,
    PluginQualityCategory,
    PluginQualityScore,
    PluginComplianceResult,
    PluginCompatibilityReport,
    PluginCertificationMetrics,
    PluginCertificationReport,
)
from flock.plugins.certification import PluginCertificationEngine

# Phase 9 (CLI & Developer Experience) — CLI & Workspace
from flock.plugins.exceptions import (
    PluginCLIError,
    PluginCommandError,
    PluginWorkspaceError,
    PluginTemplateError,
    PluginScaffoldError,
    PluginCommandExecutionError,
    PluginWorkspaceValidationError,
)
from flock.plugins.models import (
    PluginCLICommand,
    PluginCLIResult,
    PluginWorkspaceConfiguration,
    PluginWorkspace,
    PluginTemplate,
    PluginScaffold,
    PluginCommandHistory,
    PluginCLIStatistics,
    PluginCLIReport,
    PluginWorkspaceSummary,
)
from flock.plugins.cli import PluginCLI

__all__ = [
    # Phase 1 – Exceptions
    "PluginError",
    "PluginNotFoundError",
    "PluginAlreadyInstalledError",
    "PluginDependencyError",
    "PluginCompatibilityError",
    "PluginValidationError",
    "PluginSignatureError",
    "PluginActivationError",
    "PluginSandboxError",
    "PluginConfigurationError",
    "PluginExecutionError",
    # Phase 2 – Lifecycle Exceptions
    "PluginLifecycleError",
    "PluginInvalidTransitionError",
    "PluginEventDispatchError",
    "PluginLifecycleStateError",
    # Phase 3 – Dependency Exceptions
    "PluginDependencyResolutionError",
    "PluginMissingDependencyError",
    "PluginDependencyVersionConflictError",
    "PluginCircularDependencyError",
    "PluginInvalidDependencySpecError",
    # Phase 3 – Communication Exceptions
    "PluginCommunicationError",
    "PluginEventBusError",
    "PluginMessageValidationError",
    "PluginMessageTimeoutError",
    "PluginMessageDeliveryError",
    # Phase 4 – Security Exceptions
    "PluginSecurityError",
    "PluginPermissionDeniedError",
    "PluginCapabilityMismatchError",
    "PluginSecurityPolicyViolationError",
    # Phase 5 – Service Exceptions
    "PluginServiceError",
    "ServiceRegistrationError",
    "ServiceResolutionError",
    "ServiceDependencyError",
    "ServiceInjectionError",
    "DuplicateServiceError",
    # Phase 6 – Packaging Exceptions
    "PluginPackagingError",
    "PluginPackageValidationError",
    "PluginPackageIntegrityError",
    "PluginInstallationError",
    "PluginExportError",
    "PluginImportError",
    "PluginDistributionError",
    # Phase 7 – Diagnostics Exceptions
    "PluginDiagnosticsError",
    "PluginHealthCheckError",
    "PluginTelemetryError",
    "PluginStatisticsError",
    "PluginHealthReportError",
    "PluginRuntimeInspectionError",
    # Phase 1 – Models
    "PluginManifest",
    "PluginConfiguration",
    "PluginHealthReport",
    "PluginContext",
    # Phase 1 – Core Components
    "PluginRegistry",
    "PluginLoader",
    "PluginSandbox",
    "PluginDependencyResolver",
    "PluginService",
    "FlockPlugin",
    "PluginValidator",
    "PluginDiscovery",
    # Phase 2 – Lifecycle Models
    "PluginLifecycleState",
    "PluginEventType",
    "PluginLifecycleTransition",
    "PluginEventPayload",
    "PluginStatus",
    "PluginEventSubscription",
    # Phase 2 – Lifecycle Engine & Events
    "PluginEventDispatcher",
    "PluginLifecycleEngine",
    # Phase 3 – Dependency Models
    "VersionOperator",
    "DependencyConstraint",
    "DependencySpec",
    "DependencyResolutionResult",
    "PlanStepType",
    "InstallationStep",
    "DependencyInstallationPlan",
    # Phase 3 – Communication Models & Bus
    "PluginEventPriority",
    "PluginEvent",
    "PluginMessage",
    "PluginSubscription",
    "PluginBroadcast",
    "PluginResponse",
    "PluginEventBus",
    "PluginMessagingEngine",
    # Phase 4 – Security Models & Managers
    "PermissionScope",
    "PluginPermission",
    "PluginCapability",
    "SecurityPolicy",
    "SecurityViolation",
    "PermissionDecision",
    "SandboxConfiguration",
    "PluginAuditEntry",
    "PermissionRequest",
    "PluginSecurityManager",
    # Phase 5 – Service Models & Registries
    "ServiceDescriptor",
    "ServiceDependency",
    "ServiceRegistration",
    "ServiceResolution",
    "InjectionContext",
    "PluginServiceRegistry",
    # Phase 6 – Packaging Models & Engines
    "PluginPackageMetadata",
    "PluginSignature",
    "PluginPackageValidationResult",
    "PluginArchive",
    "PluginPackageManifest",
    "PluginPackage",
    "PluginDistributionTarget",
    "PluginInstallationRecord",
    "PluginPackagingEngine",
    # Phase 7 – Diagnostics Models & Engines
    "PluginHealthStatus",
    "PluginHealthSnapshot",
    "PluginDiagnosticRecord",
    "PluginTelemetryEvent",
    "PluginStatistics",
    "PluginRuntimeMetrics",
    "PluginFailureRecord",
    "PluginDiagnosticSummary",
    "PluginTelemetryHealthReport",
    "PluginDiagnosticsEngine",
    # Phase 8 — Configuration Models & Engines
    "PluginSettingsConfigurationError",
    "PluginConfigurationValidationError",
    "PluginConfigurationMigrationError",
    "PluginConfigurationPersistenceError",
    "PluginConfigurationImportError",
    "PluginConfigurationExportError",
    "PluginConfigurationConflictError",
    "PluginConfigurationField",
    "PluginConfigurationSchema",
    "PluginConfigurationProfile",
    "PluginConfigurationVersion",
    "PluginConfigurationSnapshot",
    "PluginConfigurationHistory",
    "PluginConfigurationMigration",
    "PluginConfigurationValidationResult",
    "PluginConfigurationExport",
    "PluginConfigurationEngine",
    # Phase 8 (Certification) — Quality QA Models & Engines
    "PluginCertificationError",
    "PluginComplianceError",
    "PluginQualityValidationError",
    "PluginCertificationFailure",
    "PluginAuditError",
    "PluginCertificationStatus",
    "PluginCertificationCheck",
    "PluginQualityCategory",
    "PluginQualityScore",
    "PluginComplianceResult",
    "PluginCompatibilityReport",
    "PluginCertificationMetrics",
    "PluginCertificationReport",
    "PluginCertificationEngine",
    # Phase 9 (CLI & Developer Experience) — CLI & Workspace Models & Engines
    "PluginCLIError",
    "PluginCommandError",
    "PluginWorkspaceError",
    "PluginTemplateError",
    "PluginScaffoldError",
    "PluginCommandExecutionError",
    "PluginWorkspaceValidationError",
    "PluginCLICommand",
    "PluginCLIResult",
    "PluginWorkspaceConfiguration",
    "PluginWorkspace",
    "PluginTemplate",
    "PluginScaffold",
    "PluginCommandHistory",
    "PluginCLIStatistics",
    "PluginCLIReport",
    "PluginWorkspaceSummary",
    "PluginCLI",
]
