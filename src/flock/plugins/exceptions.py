"""Plugin Subsystem Exceptions."""

from flock.exceptions import FlockError

class PluginError(FlockError):
    """Base exception for all plugin operations."""
    pass

class PluginNotFoundError(PluginError):
    """Raised when plugin ID is missing from registry."""
    pass

class PluginAlreadyInstalledError(PluginError):
    """Raised when registering an already registered plugin ID."""
    pass

class PluginDependencyError(PluginError):
    """Raised when dependencies are unresolved or circular dependencies exist."""
    pass

class PluginCompatibilityError(PluginError):
    """Raised when plugin version mismatches framework bounds."""
    pass

class PluginValidationError(PluginError):
    """Raised when plugin manifest formatting is invalid."""
    pass

class PluginSignatureError(PluginError):
    """Raised when plugin SHA-256 integrity validation fails."""
    pass

class PluginActivationError(PluginError):
    """Raised when dynamic loading initialization fails."""
    pass

class PluginSandboxError(PluginError):
    """Raised when plugins violate context execution limits."""
    pass

class PluginConfigurationError(PluginError):
    """Raised when plugin configuration schema checks fail."""
    pass

class PluginExecutionError(PluginError):
    """Raised when plugin execution blocks encounter errors."""
    pass


# ---------------------------------------------------------------------------
# Phase 2 — Lifecycle & Event Exceptions
# ---------------------------------------------------------------------------


class PluginLifecycleError(PluginError):
    """Raised when a lifecycle operation cannot be performed."""
    pass


class PluginInvalidTransitionError(PluginLifecycleError):
    """Raised when an illegal lifecycle state transition is attempted.

    Args:
        plugin_id: The identifier of the plugin involved.
        from_state: The current state at the time of the attempt.
        to_state: The attempted target state.
    """

    def __init__(self, plugin_id: str, from_state: str, to_state: str) -> None:
        self.plugin_id = plugin_id
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Plugin '{plugin_id}': illegal transition from '{from_state}' to '{to_state}'."
        )


class PluginEventDispatchError(PluginError):
    """Raised when an event cannot be dispatched to listeners."""
    pass


class PluginLifecycleStateError(PluginLifecycleError):
    """Raised when a plugin is in an unexpected state for the requested operation."""
    pass


# ---------------------------------------------------------------------------
# Phase 3 — Dependency Management & Resolution Exceptions
# ---------------------------------------------------------------------------


class PluginDependencyResolutionError(PluginDependencyError):
    """Base exception for all dependency resolution failures."""
    pass


class PluginMissingDependencyError(PluginDependencyResolutionError):
    """Raised when a required dependency is missing from the registry."""
    pass


class PluginDependencyVersionConflictError(PluginDependencyResolutionError):
    """Raised when a dependency is present but violates version constraints."""
    pass


class PluginCircularDependencyError(PluginDependencyResolutionError):
    """Raised when a cyclic dependency loop is detected."""
    pass


class PluginInvalidDependencySpecError(PluginDependencyResolutionError):
    """Raised when a dependency specification string cannot be parsed."""
    pass


# ---------------------------------------------------------------------------
# Phase 3 — Plugin Communication & Event Framework Exceptions
# ---------------------------------------------------------------------------


class PluginCommunicationError(PluginError):
    """Base exception for all plugin communication and event routing errors."""
    pass


class PluginEventBusError(PluginCommunicationError):
    """Raised when the event bus fails to publish, subscribe, or dispatch events."""
    pass


class PluginMessageValidationError(PluginCommunicationError):
    """Raised when a plugin message violates schema or metadata constraints."""
    pass


class PluginMessageTimeoutError(PluginCommunicationError):
    """Raised when a direct request/response message times out."""
    pass


class PluginMessageDeliveryError(PluginCommunicationError):
    """Raised when a point-to-point or broadcast message fails to be delivered."""
    pass


# ---------------------------------------------------------------------------
# Phase 4 — Security, Sandboxing & Permission Exceptions
# ---------------------------------------------------------------------------


class PluginSecurityError(PluginError):
    """Base exception for all plugin security-related failures."""
    pass


class PluginPermissionDeniedError(PluginSecurityError):
    """Raised when an operation is blocked by security policies or permissions."""
    pass


class PluginCapabilityMismatchError(PluginSecurityError):
    """Raised when a plugin attempts an action exceeding its declared capabilities."""
    pass


class PluginSecurityPolicyViolationError(PluginSecurityError):
    """Raised when a plugin violates an active security policy constraint."""
    pass


# ---------------------------------------------------------------------------
# Phase 5 — Plugin Service Registry & Dependency Injection Exceptions
# ---------------------------------------------------------------------------


class PluginServiceError(PluginError):
    """Base exception for all service registry and lookup operations."""
    pass


class ServiceRegistrationError(PluginServiceError):
    """Raised when a service cannot be registered due to constraint violations."""
    pass


class ServiceResolutionError(PluginServiceError):
    """Raised when a requested service cannot be resolved or found."""
    pass


class ServiceDependencyError(PluginServiceError):
    """Raised when a service declares invalid or missing dependencies."""
    pass


class ServiceInjectionError(PluginServiceError):
    """Raised when dependency injection fails at runtime."""
    pass


class DuplicateServiceError(ServiceRegistrationError):
    """Raised when a service registration conflicts with an existing registration."""
    pass


# ---------------------------------------------------------------------------
# Phase 6 — Plugin Packaging, Distribution & Marketplace Exceptions
# ---------------------------------------------------------------------------


class PluginPackagingError(PluginError):
    """Base exception for all plugin packaging operations."""
    pass


class PluginPackageValidationError(PluginPackagingError):
    """Raised when a dynamic plugin package fails validation rules."""
    pass


class PluginPackageIntegrityError(PluginPackagingError):
    """Raised when package checksums or signatures do not match."""
    pass


class PluginInstallationError(PluginPackagingError):
    """Raised when package installation or setup fails."""
    pass


class PluginExportError(PluginPackagingError):
    """Raised when exporting plugin package archive fails."""
    pass


class PluginImportError(PluginPackagingError):
    """Raised when importing plugin package archive fails."""
    pass


class PluginDistributionError(PluginPackagingError):
    """Raised when distributing or matching targets for packages fails."""
    pass


# ---------------------------------------------------------------------------
# Phase 7 — Plugin Diagnostics, Health Monitoring & Telemetry Exceptions
# ---------------------------------------------------------------------------


class PluginDiagnosticsError(PluginError):
    """Base exception for all plugin diagnostic and telemetry failures."""
    pass


class PluginHealthCheckError(PluginDiagnosticsError):
    """Raised when health checking evaluation fails or reports errors."""
    pass


class PluginTelemetryError(PluginDiagnosticsError):
    """Raised when processing or saving telemetry events fails."""
    pass


class PluginStatisticsError(PluginDiagnosticsError):
    """Raised when summarizing runtime statistic metrics fails."""
    pass


class PluginHealthReportError(PluginDiagnosticsError):
    """Raised when generating a plugin health report fails."""
    pass


class PluginRuntimeInspectionError(PluginDiagnosticsError):
    """Raised when inspecting plugin resources, memory, or threads fails."""
    pass


# ---------------------------------------------------------------------------
# Phase 8 — Plugin Configuration Management & Persistence Exceptions
# ---------------------------------------------------------------------------


class PluginSettingsConfigurationError(PluginError):
    """Base exception for all plugin configuration and persistence operations."""
    pass


class PluginConfigurationValidationError(PluginSettingsConfigurationError):
    """Raised when configuration values fail schema verification."""
    pass


class PluginConfigurationMigrationError(PluginSettingsConfigurationError):
    """Raised when upgrading versioned configurations fails."""
    pass


class PluginConfigurationPersistenceError(PluginSettingsConfigurationError):
    """Raised when saving or loading serialized configurations fails."""
    pass


class PluginConfigurationImportError(PluginSettingsConfigurationError):
    """Raised when importing configuration documents fails."""
    pass


class PluginConfigurationExportError(PluginSettingsConfigurationError):
    """Raised when exporting configuration documents fails."""
    pass


class PluginConfigurationConflictError(PluginSettingsConfigurationError):
    """Raised when setting configurations conflicts with active settings."""
    pass


# ---------------------------------------------------------------------------
# Phase 8 (Certification) — Plugin Testing, Certification & QA Exceptions
# ---------------------------------------------------------------------------


class PluginCertificationError(PluginError):
    """Base exception for all plugin testing and certification failures."""
    pass


class PluginComplianceError(PluginCertificationError):
    """Raised when a compliance check rule fails verification checks."""
    pass


class PluginQualityValidationError(PluginCertificationError):
    """Raised when quality scoring values exceed or fail parameters limits."""
    pass


class PluginCertificationFailure(PluginCertificationError):
    """Raised when certification pipeline rejects plugin execution."""
    pass


class PluginAuditError(PluginCertificationError):
    """Raised when writing or verifying diagnostic quality logs fails."""
    pass


# ---------------------------------------------------------------------------
# Phase 9 (CLI & Developer Experience) — CLI & Workspace Exceptions
# ---------------------------------------------------------------------------


class PluginCLIError(PluginError):
    """Base exception for all CLI command and development workspace failures."""
    pass


class PluginCommandError(PluginCLIError):
    """Raised when parsing or verifying command inputs parameters fails."""
    pass


class PluginWorkspaceError(PluginCLIError):
    """Raised when workspace configuration directories checks fail."""
    pass


class PluginTemplateError(PluginCLIError):
    """Raised when generating default project structure templates fails."""
    pass


class PluginScaffoldError(PluginCLIError):
    """Raised when generating scaffolds folders structure or manifest files fails."""
    pass


class PluginCommandExecutionError(PluginCLIError):
    """Raised when executing targeted plugin commands fails at runtime."""
    pass


class PluginWorkspaceValidationError(PluginCLIError):
    """Raised when auditing structural layouts integrity in workspaces fails."""
    pass










