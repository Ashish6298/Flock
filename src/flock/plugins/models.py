from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PluginManifest(BaseModel):
    """Represents a plugin metadata manifest descriptor."""
    plugin_id: str
    name: str
    version: str
    author: str
    sdk_version: str = "1.0.0"
    dependencies: List[str] = Field(default_factory=list)
    optional_dependencies: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)

    entry_point: Optional[str] = None

    model_config = {
        "frozen": True
    }


class PluginConfiguration(BaseModel):
    """Represents persistence configuration settings overrides."""
    plugin_id: str
    settings: Dict[str, str] = Field(default_factory=dict)
    is_enabled: bool = True

    model_config = {
        "frozen": True
    }


class PluginHealthReport(BaseModel):
    """Represents periodic plugin resource metrics report."""
    plugin_id: str
    status: str  # "HEALTHY", "DEGRADED", "FAILED"
    cpu_usage: float
    memory_usage: float

    model_config = {
        "frozen": True
    }


class PluginContext(BaseModel):
    """Represents context resources allocated to sandboxed plugins."""
    plugin_id: str
    data_directory: str
    permissions: List[str] = Field(default_factory=list)
    configuration: Dict[str, str] = Field(default_factory=dict)

    model_config = {
        "frozen": True,
        "arbitrary_types_allowed": True
    }

    def get_config(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Safely fetch config settings."""
        return self.configuration.get(key, default)

    def log_info(self, message: str, **kwargs: Any) -> None:
        """Isolated logging helper."""
        import structlog
        structlog.get_logger("flock.plugins").info(message, plugin_id=self.plugin_id, **kwargs)

    def log_error(self, message: str, **kwargs: Any) -> None:
        """Isolated logging helper."""
        import structlog
        structlog.get_logger("flock.plugins").error(message, plugin_id=self.plugin_id, **kwargs)




class PluginEventPriority(int, Enum):
    """Event priority levels for execution ordering."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class PluginEvent(BaseModel):
    """Represents a structured event published by a plugin or the system."""
    event_id: str
    event_type: str
    sender_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    priority: PluginEventPriority = PluginEventPriority.NORMAL
    timestamp: float = Field(default_factory=lambda: __import__("time").time())
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PluginMessage(BaseModel):
    """Represents a direct message exchanged between two plugins."""
    message_id: str
    sender_id: str
    recipient_id: str
    subject: str
    body: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    timestamp: float = Field(default_factory=lambda: __import__("time").time())
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PluginSubscription(BaseModel):
    """Represents a plugin subscription to specific event types."""
    subscription_id: str
    plugin_id: str
    event_type: str
    priority_filter: Optional[PluginEventPriority] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PluginBroadcast(BaseModel):
    """Represents a message broadcasted to multiple plugin recipients."""
    broadcast_id: str
    sender_id: str
    subject: str
    body: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=lambda: __import__("time").time())
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PluginResponse(BaseModel):
    """Represents the response to a PluginMessage request."""
    response_id: str
    request_id: str
    sender_id: str
    recipient_id: str
    success: bool
    payload: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    timestamp: float = Field(default_factory=lambda: __import__("time").time())
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PermissionScope(str, Enum):
    """Defines the authorization scope of a permission."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    NETWORK = "network"
    SYSTEM = "system"


class PluginPermission(BaseModel):
    """Represents a specific granted permission with scope."""
    permission_id: str
    plugin_id: str
    scope: PermissionScope
    resource: str
    is_granted: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PluginCapability(BaseModel):
    """Represents a declared runtime capability constraint."""
    name: str
    description: str
    required_permissions: List[PermissionScope] = Field(default_factory=list)

    model_config = {
        "frozen": True
    }


class SecurityPolicy(BaseModel):
    """Represents a set of security constraints and permissions for a plugin or namespace."""
    policy_id: str
    plugin_id_pattern: str  # Can be specific ID or glob/namespace pattern
    allowed_permissions: List[PermissionScope] = Field(default_factory=list)
    denied_permissions: List[PermissionScope] = Field(default_factory=list)
    max_memory_mb: Optional[float] = None
    max_cpu_percent: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class SecurityViolation(BaseModel):
    """Represents a logged security violation event."""
    violation_id: str
    plugin_id: str
    attempted_action: str
    required_scope: PermissionScope
    timestamp: float = Field(default_factory=lambda: __import__("time").time())
    details: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PermissionDecision(BaseModel):
    """Represents a cached permission decision evaluation."""
    decision_id: str
    plugin_id: str
    scope: PermissionScope
    resource: str
    allowed: bool
    evaluated_at: float = Field(default_factory=lambda: __import__("time").time())
    policy_id: Optional[str] = None

    model_config = {
        "frozen": True
    }


class SandboxConfiguration(BaseModel):
    """Configuration parameter bounds for a sandboxed execution context."""
    sandbox_id: str
    plugin_id: str
    allowed_scopes: List[PermissionScope] = Field(default_factory=list)
    restricted_directories: List[str] = Field(default_factory=list)
    allowed_hosts: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PluginAuditEntry(BaseModel):
    """Audit log record for security-relevant operations."""
    entry_id: str
    plugin_id: str
    action: str
    status: str  # "SUCCESS", "DENIED", "VIOLATION"
    timestamp: float = Field(default_factory=lambda: __import__("time").time())
    details: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PermissionRequest(BaseModel):
    """Represents a plugin request for a capability or resource access."""
    request_id: str
    plugin_id: str
    scope: PermissionScope
    resource: str
    justification: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class ServiceDescriptor(BaseModel):
    """Identifies and describes a registered plugin service contract."""
    service_id: str
    interface_name: str
    provider_plugin_id: str
    version: str = "1.0.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class ServiceDependency(BaseModel):
    """Declares a dependency on an external plugin service interface."""
    interface_name: str
    is_optional: bool = False
    version_constraint: Optional[str] = None

    model_config = {
        "frozen": True
    }


class ServiceRegistration(BaseModel):
    """Details of a registered service instance and metadata."""
    registration_id: str
    descriptor: ServiceDescriptor
    registered_at: float = Field(default_factory=lambda: __import__("time").time())
    is_active: bool = True

    model_config = {
        "frozen": True
    }


class ServiceResolution(BaseModel):
    """Resolution result mapping dependency query to provider class."""
    dependency: ServiceDependency
    resolved_provider_id: Optional[str] = None
    resolved_at: float = Field(default_factory=lambda: __import__("time").time())
    success: bool

    model_config = {
        "frozen": True
    }


class InjectionContext(BaseModel):
    """Context detail for target destination instance being injected."""
    target_plugin_id: str
    target_class_name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PluginPackageMetadata(BaseModel):
    """General metadata describing plugin package dependencies and platform compatibility."""
    plugin_id: str
    min_sdk_version: str = "1.0.0"
    operating_systems: List[str] = Field(default_factory=list)
    license: str = "MIT"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PluginSignature(BaseModel):
    """Integrity signature block matching plugin archive content."""
    sha256_hash: str
    signature: Optional[str] = None
    publisher_key: Optional[str] = None
    signed_at: Optional[float] = None

    model_config = {
        "frozen": True
    }


class PluginPackageValidationResult(BaseModel):
    """Audit outcome of a package validation check."""
    success: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    model_config = {
        "frozen": True
    }


class PluginArchive(BaseModel):
    """Reference detailing a built plugin ZIP archive location and checksum."""
    archive_path: str
    checksum: str
    file_size_bytes: int

    model_config = {
        "frozen": True
    }


class PluginPackageManifest(BaseModel):
    """Details identifying target plugins and dependencies for packaging."""
    plugin_id: str
    version: str
    manifest_checksum: str
    packaged_files: List[str] = Field(default_factory=list)

    model_config = {
        "frozen": True
    }


class PluginPackage(BaseModel):
    """Represents a fully structured plugin package bundle ready for distribution."""
    plugin_id: str
    manifest: PluginPackageManifest
    metadata: PluginPackageMetadata
    signature: PluginSignature
    archive: PluginArchive

    model_config = {
        "frozen": True
    }


class PluginDistributionTarget(BaseModel):
    """Identifies the installation targets and registry compatibility endpoints."""
    target_id: str
    platform_name: str
    api_endpoint: str
    is_active: bool = True

    model_config = {
        "frozen": True
    }


class PluginInstallationRecord(BaseModel):
    """Tracks historical package installations in the registry."""
    plugin_id: str
    installed_version: str
    installed_at: float = Field(default_factory=lambda: __import__("time").time())
    archive_checksum: str
    install_path: str
    status: str = "INSTALLED"  # "INSTALLED", "UNINSTALLED", "CORRUPTED"

    model_config = {
        "frozen": True
    }




class PluginHealthStatus(str, Enum):
    """Plugin health status enum classifications."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    WARNING = "WARNING"
    FAILED = "FAILED"
    DISABLED = "DISABLED"


class PluginHealthSnapshot(BaseModel):
    """Represents a passive diagnostic evaluation record at a single point in time."""
    plugin_id: str
    status: PluginHealthStatus
    timestamp: datetime = Field(default_factory=lambda: datetime.now(__import__("datetime").timezone.utc))
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PluginDiagnosticRecord(BaseModel):
    """System-level diagnostic details for inspection."""
    record_id: str
    plugin_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(__import__("datetime").timezone.utc))
    level: str  # "INFO", "WARNING", "ERROR"
    message: str
    source_component: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PluginTelemetryEvent(BaseModel):
    """Passive telemetry monitoring event details."""
    event_id: str
    plugin_id: str
    event_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(__import__("datetime").timezone.utc))
    payload: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PluginRuntimeMetrics(BaseModel):
    """Execution latency and resource usages."""
    cpu_percent: float = 0.0
    memory_bytes: int = 0
    execution_latency_ms: float = 0.0
    active_threads: int = 0

    model_config = {
        "frozen": True
    }


class PluginFailureRecord(BaseModel):
    """Tracks exceptions and failures encountered during plugin lifecycle or execution."""
    failure_id: str
    plugin_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(__import__("datetime").timezone.utc))
    exception_class: str
    error_message: str
    stack_trace: Optional[str] = None
    fatal: bool = False

    model_config = {
        "frozen": True
    }


class PluginStatistics(BaseModel):
    """Historical telemetry statistics summary."""
    plugin_id: str
    uptime_seconds: float = 0.0
    execution_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    restart_count: int = 0
    last_reset_at: datetime = Field(default_factory=lambda: datetime.now(__import__("datetime").timezone.utc))

    model_config = {
        "frozen": True
    }


class PluginTelemetryHealthReport(BaseModel):
    """Passive health analysis report consolidate structure."""
    plugin_id: str
    overall_status: PluginHealthStatus
    generated_at: datetime = Field(default_factory=lambda: datetime.now(__import__("datetime").timezone.utc))
    snapshot: PluginHealthSnapshot
    statistics: PluginStatistics
    metrics: PluginRuntimeMetrics
    recent_failures: List[PluginFailureRecord] = Field(default_factory=list)

    model_config = {
        "frozen": True
    }


class PluginDiagnosticSummary(BaseModel):
    """Compact summary of diagnostics across plugins."""
    plugins_analyzed: int
    healthy_count: int
    warning_count: int
    failed_count: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(__import__("datetime").timezone.utc))
    summaries: Dict[str, PluginHealthStatus] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PluginConfigurationField(BaseModel):
    """Metadata detailing a single configuration field constraint."""
    name: str
    type_name: str  # "string", "int", "bool", "float", etc.
    default_value: Any
    description: Optional[str] = None
    is_required: bool = False

    model_config = {
        "frozen": True
    }


class PluginConfigurationSchema(BaseModel):
    """Consolidated configuration schema mapping for a plugin."""
    plugin_id: str
    version: str
    fields: Dict[str, PluginConfigurationField] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PluginConfigurationProfile(BaseModel):
    """Named profile collection of settings overrides."""
    profile_id: str
    profile_name: str
    plugin_id: str
    settings: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = False

    model_config = {
        "frozen": True
    }


class PluginConfigurationVersion(BaseModel):
    """Identifies version state metadata for migrations."""
    version_id: str
    plugin_id: str
    version_string: str
    applied_at: datetime = Field(default_factory=lambda: datetime.now(__import__("datetime").timezone.utc))

    model_config = {
        "frozen": True
    }


class PluginConfigurationSnapshot(BaseModel):
    """Immutable snapshot configuration settings at a point in time."""
    snapshot_id: str
    plugin_id: str
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(__import__("datetime").timezone.utc))

    model_config = {
        "frozen": True
    }


class PluginConfigurationHistory(BaseModel):
    """Tracks updates and transitions to config settings."""
    history_id: str
    plugin_id: str
    previous_settings: Dict[str, Any] = Field(default_factory=dict)
    new_settings: Dict[str, Any] = Field(default_factory=dict)
    changed_at: datetime = Field(default_factory=lambda: datetime.now(__import__("datetime").timezone.utc))
    reason: Optional[str] = None

    model_config = {
        "frozen": True
    }


class PluginConfigurationMigration(BaseModel):
    """Declares step detail for schema configuration upgrades."""
    migration_id: str
    plugin_id: str
    from_version: str
    to_version: str
    migration_key: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PluginConfigurationValidationResult(BaseModel):
    """Audit schema validator outcome."""
    success: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    model_config = {
        "frozen": True
    }


class PluginConfigurationExport(BaseModel):
    """Document payload export bundle of plugin configuration settings."""
    plugin_id: str
    version: str
    exported_at: datetime = Field(default_factory=lambda: datetime.now(__import__("datetime").timezone.utc))
    settings: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PluginCertificationStatus(str, Enum):
    """Supported certification outcome status values."""
    CERTIFIED = "CERTIFIED"
    CONDITIONALLY_CERTIFIED = "CONDITIONALLY_CERTIFIED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class PluginCertificationCheck(BaseModel):
    """Details a single compliance rule validation check execution."""
    rule_name: str
    category: str
    success: bool
    details: str

    model_config = {
        "frozen": True
    }


class PluginQualityCategory(BaseModel):
    """Metrics category mapping for quality scoring calculations."""
    category_name: str
    score: float  # 0.0 to 100.0
    weight: float  # 0.0 to 1.0

    model_config = {
        "frozen": True
    }


class PluginQualityScore(BaseModel):
    """Aggregated quality metrics containing weighted categories scores."""
    overall_score: float  # 0.0 to 100.0
    categories: List[PluginQualityCategory] = Field(default_factory=list)

    model_config = {
        "frozen": True
    }


class PluginComplianceResult(BaseModel):
    """Outcome status for compliance execution constraints."""
    passed_rules: List[str] = Field(default_factory=list)
    failed_rules: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PluginCompatibilityReport(BaseModel):
    """Details SDK, dependency, and platform capability compatibility checks."""
    is_compatible: bool
    sdk_version_check: str
    unresolved_dependencies: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PluginCertificationMetrics(BaseModel):
    """Performance latency and capability checks metrics compiled during validation."""
    conformance_percent: float
    rules_checked: int
    rules_passed: int
    duration_ms: float

    model_config = {
        "frozen": True
    }


class PluginCertificationReport(BaseModel):
    """Consolidated testing and quality certification report payload."""
    report_id: str
    plugin_id: str
    version: str
    status: PluginCertificationStatus
    quality_score: PluginQualityScore
    compatibility: PluginCompatibilityReport
    compliance: PluginComplianceResult
    metrics: PluginCertificationMetrics
    certified_at: datetime = Field(default_factory=lambda: datetime.now(__import__("datetime").timezone.utc))

    model_config = {
        "frozen": True
    }


class PluginCLICommand(BaseModel):
    """Represents a CLI command execution request."""
    command_name: str
    arguments: List[str] = Field(default_factory=list)
    options: Dict[str, str] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PluginCLIResult(BaseModel):
    """Outcome status for CLI command executions."""
    success: bool
    output: str
    error_message: Optional[str] = None

    model_config = {
        "frozen": True
    }


class PluginWorkspaceConfiguration(BaseModel):
    """Workspace configuration variables representation."""
    workspace_name: str
    root_path: str
    default_sdk_version: str = "1.0.0"

    model_config = {
        "frozen": True
    }


class PluginWorkspace(BaseModel):
    """Identifies workspace metadata files mapping structure."""
    workspace_id: str
    config: PluginWorkspaceConfiguration
    created_at: datetime = Field(default_factory=lambda: datetime.now(__import__("datetime").timezone.utc))

    model_config = {
        "frozen": True
    }


class PluginTemplate(BaseModel):
    """Named structure blueprint for generating new plugins."""
    template_id: str
    name: str
    description: str
    files: Dict[str, str] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PluginScaffold(BaseModel):
    """Audit metadata tracking generated plugin folders structure."""
    scaffold_id: str
    plugin_id: str
    target_path: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(__import__("datetime").timezone.utc))

    model_config = {
        "frozen": True
    }


class PluginCommandHistory(BaseModel):
    """Logs history execution parameters and execution results."""
    history_id: str
    command: PluginCLICommand
    result: PluginCLIResult
    executed_at: datetime = Field(default_factory=lambda: datetime.now(__import__("datetime").timezone.utc))

    model_config = {
        "frozen": True
    }


class PluginCLIStatistics(BaseModel):
    """Metrics mapping overall CLI usage history statistics."""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0

    model_config = {
        "frozen": True
    }


class PluginCLIReport(BaseModel):
    """Consolidated report auditing developer activity and CLI history."""
    report_id: str
    statistics: PluginCLIStatistics
    history: List[PluginCommandHistory] = Field(default_factory=list)

    model_config = {
        "frozen": True
    }


class PluginWorkspaceSummary(BaseModel):
    """Overview statistics detailing plugins count and configurations in workspaces."""
    workspace_id: str
    plugins_registered_count: int
    active_plugins_count: int

    model_config = {
        "frozen": True
    }








