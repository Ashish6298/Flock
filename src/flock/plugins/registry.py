"""Plugin Registry tracking installations metadata."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional, Set, Any

from flock.plugins.exceptions import PluginAlreadyInstalledError, PluginNotFoundError
from flock.plugins.models import (
    PluginManifest,
    PluginSubscription,
    PluginMessage,
    PluginBroadcast,
    PluginResponse,
    ServiceRegistration,
    SecurityPolicy,
    PluginPermission,
    PluginAuditEntry,
    SecurityViolation,
    PluginInstallationRecord,
    PluginPackage,
    PluginHealthSnapshot,
    PluginDiagnosticRecord,
    PluginTelemetryEvent,
    PluginRuntimeMetrics,
    PluginFailureRecord,
    PluginStatistics,
    PluginConfigurationSchema,
    PluginConfigurationProfile,
    PluginConfigurationSnapshot,
    PluginConfigurationHistory,
    PluginConfigurationMigration,
    PluginCertificationReport,
    PluginCommandHistory,
    PluginWorkspace,
    PluginTemplate,
    PluginScaffold,
)


class PluginRegistry:
    """Thread-safe index registry for dynamic manifests."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        
        # plugin_id -> PluginManifest
        self._plugins: Dict[str, PluginManifest] = {}
        self._activated: Dict[str, bool] = {}

    def register_plugin(self, manifest: PluginManifest) -> None:
        """Add plugin metadata descriptor.

        Raises:
            PluginAlreadyInstalledError: If plugin ID is already registered.
        """
        with self._lock:
            if manifest.plugin_id in self._plugins:
                raise PluginAlreadyInstalledError(f"Plugin '{manifest.plugin_id}' already registered.")
            self._plugins[manifest.plugin_id] = manifest
            self._activated[manifest.plugin_id] = False

    def unregister_plugin(self, plugin_id: str) -> None:
        """Remove plugin metadata descriptor."""
        with self._lock:
            self._plugins.pop(plugin_id, None)
            self._activated.pop(plugin_id, None)

    def get_plugin(self, plugin_id: str) -> Optional[PluginManifest]:
        """Fetch plugin manifest descriptor."""
        with self._lock:
            return self._plugins.get(plugin_id)

    def list_plugins(self) -> List[PluginManifest]:
        """List all registered manifests."""
        with self._lock:
            return list(self._plugins.values())

    def set_activated(self, plugin_id: str, active: bool) -> None:
        """Update activated flag.

        Raises:
            PluginNotFoundError: If plugin ID is missing.
        """
        with self._lock:
            if plugin_id not in self._plugins:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' not found.")
            self._activated[plugin_id] = active

    def is_activated(self, plugin_id: str) -> bool:
        """Check active status."""
        with self._lock:
            return self._activated.get(plugin_id, False)

    def validate_registry_dependencies(self) -> None:
        """Validate dependencies for all registered plugins.

        Raises:
            PluginDependencyError: If a required dependency is missing or version mismatch.
        """
        with self._lock:
            from flock.plugins.resolver import PluginDependencyResolver
            resolver = PluginDependencyResolver()
            resolver.resolve_dependencies(list(self._plugins.values()))

    # ---------------------------------------------------------------------------
    # Phase 3 — Plugin Communication & Event Registry Storage
    # ---------------------------------------------------------------------------

    def init_communication_storage(self) -> None:
        """Initializes internal storage structures for subscriptions, handlers, sessions, and messages."""
        with self._lock:
            if not hasattr(self, "_subscriptions_map"):
                self._subscriptions_map: Dict[str, PluginSubscription] = {}  # sub_id -> PluginSubscription
            if not hasattr(self, "_handlers_map"):
                self._handlers_map: Dict[str, Dict[str, Any]] = {}  # plugin_id -> subject -> handler_callable
            if not hasattr(self, "_active_sessions"):
                self._active_sessions: Set[str] = set()  # session_ids
            if not hasattr(self, "_message_log"):
                self._message_log: List[PluginMessage] = []
            if not hasattr(self, "_broadcast_log"):
                self._broadcast_log: List[PluginBroadcast] = []
            if not hasattr(self, "_response_log"):
                self._response_log: List[PluginResponse] = []

    def register_subscription(self, sub: PluginSubscription) -> None:
        """Saves a plugin event subscription."""
        with self._lock:
            self.init_communication_storage()
            self._subscriptions_map[sub.subscription_id] = sub

    def remove_subscription(self, sub_id: str) -> bool:
        """Removes an active event subscription by ID."""
        with self._lock:
            self.init_communication_storage()
            if sub_id in self._subscriptions_map:
                del self._subscriptions_map[sub_id]
                return True
            return False

    def query_subscriptions(self, event_type: Optional[str] = None, plugin_id: Optional[str] = None) -> List[PluginSubscription]:
        """Queries subscriptions with optional event_type and plugin_id filters."""
        with self._lock:
            self.init_communication_storage()
            results = list(self._subscriptions_map.values())
            if event_type is not None:
                results = [s for s in results if s.event_type == event_type]
            if plugin_id is not None:
                results = [s for s in results if s.plugin_id == plugin_id]
            return results

    def register_message_handler(self, plugin_id: str, subject: str, handler: Any) -> None:
        """Registers a direct message handler callback for a plugin and subject."""
        with self._lock:
            self.init_communication_storage()
            if plugin_id not in self._handlers_map:
                self._handlers_map[plugin_id] = {}
            self._handlers_map[plugin_id][subject] = handler

    def remove_message_handler(self, plugin_id: str, subject: str) -> bool:
        """Removes a registered message handler."""
        with self._lock:
            self.init_communication_storage()
            if plugin_id in self._handlers_map and subject in self._handlers_map[plugin_id]:
                del self._handlers_map[plugin_id][subject]
                return True
            return False

    def get_message_handler(self, plugin_id: str, subject: str) -> Optional[Any]:
        """Retrieves a message handler for a plugin and subject."""
        with self._lock:
            self.init_communication_storage()
            return self._handlers_map.get(plugin_id, {}).get(subject)

    def log_message(self, msg: PluginMessage) -> None:
        """Appends a point-to-point message to history logs."""
        with self._lock:
            self.init_communication_storage()
            self._message_log.append(msg)

    def log_broadcast(self, bcast: PluginBroadcast) -> None:
        """Appends a broadcast message to history logs."""
        with self._lock:
            self.init_communication_storage()
            self._broadcast_log.append(bcast)

    def log_response(self, resp: PluginResponse) -> None:
        """Appends a response to history logs."""
        with self._lock:
            self.init_communication_storage()
            self._response_log.append(resp)

    def get_message_history(self) -> List[PluginMessage]:
        """Returns copies of all recorded point-to-point messages."""
        with self._lock:
            self.init_communication_storage()
            return list(self._message_log)

    def get_broadcast_history(self) -> List[PluginBroadcast]:
        """Returns copies of all recorded broadcast messages."""
        with self._lock:
            self.init_communication_storage()
            return list(self._broadcast_log)

    def register_session(self, session_id: str) -> None:
        """Registers an active communications session."""
        with self._lock:
            self.init_communication_storage()
            self._active_sessions.add(session_id)

    def remove_session(self, session_id: str) -> bool:
        """Removes an active communications session."""
        with self._lock:
            self.init_communication_storage()
            if session_id in self._active_sessions:
                self._active_sessions.remove(session_id)
                return True
            return False

    def is_session_active(self, session_id: str) -> bool:
        """Checks if a session is currently active."""
        with self._lock:
            self.init_communication_storage()
            return session_id in self._active_sessions

    # ---------------------------------------------------------------------------
    # Phase 4 — Security Registry Storage
    # ---------------------------------------------------------------------------

    def init_security_storage(self) -> None:
        """Initializes internal structures for security policies, permissions, and audit logs."""
        with self._lock:
            if not hasattr(self, "_security_policies"):
                self._security_policies: Dict[str, SecurityPolicy] = {}  # policy_id -> SecurityPolicy
            if not hasattr(self, "_granted_permissions"):
                self._granted_permissions: Dict[str, List[PluginPermission]] = {}  # plugin_id -> list of PluginPermission
            if not hasattr(self, "_audit_entries"):
                self._audit_entries: List[PluginAuditEntry] = []
            if not hasattr(self, "_security_violations"):
                self._security_violations: List[SecurityViolation] = []

    def register_security_policy(self, policy: SecurityPolicy) -> None:
        """Registers a namespace or plugin security policy."""
        with self._lock:
            self.init_security_storage()
            self._security_policies[policy.policy_id] = policy

    def get_security_policies(self) -> List[SecurityPolicy]:
        """Returns all registered security policies."""
        with self._lock:
            self.init_security_storage()
            return list(self._security_policies.values())

    def grant_permission(self, perm: PluginPermission) -> None:
        """Saves a granted permission record."""
        with self._lock:
            self.init_security_storage()
            if perm.plugin_id not in self._granted_permissions:
                self._granted_permissions[perm.plugin_id] = []
            self._granted_permissions[perm.plugin_id].append(perm)

    def query_permissions(self, plugin_id: str) -> List[PluginPermission]:
        """Queries granted permissions for a specific plugin."""
        with self._lock:
            self.init_security_storage()
            return list(self._granted_permissions.get(plugin_id, []))

    def record_audit_entry(self, entry: PluginAuditEntry) -> None:
        """Appends an entry to the audit log."""
        with self._lock:
            self.init_security_storage()
            self._audit_entries.append(entry)

    def query_audit_logs(self, plugin_id: Optional[str] = None) -> List[PluginAuditEntry]:
        """Queries security audit entries, optionally filtered by plugin_id."""
        with self._lock:
            self.init_security_storage()
            if plugin_id is not None:
                return [e for e in self._audit_entries if e.plugin_id == plugin_id]
            return list(self._audit_entries)

    def record_security_violation(self, violation: SecurityViolation) -> None:
        """Logs a security policy violation."""
        with self._lock:
            self.init_security_storage()
            self._security_violations.append(violation)

    def get_security_violations(self, plugin_id: Optional[str] = None) -> List[SecurityViolation]:
        """Queries security violations, optionally filtered by plugin_id."""
        with self._lock:
            self.init_security_storage()
            if plugin_id is not None:
                return [v for v in self._security_violations if v.plugin_id == plugin_id]
            return list(self._security_violations)

    def clear_expired_audit_records(self, before_timestamp: float) -> int:
        """Prunes audit entries generated prior to the target timestamp. Returns count deleted."""
        with self._lock:
            self.init_security_storage()
            original_len = len(self._audit_entries)
            self._audit_entries = [e for e in self._audit_entries if e.timestamp >= before_timestamp]
            return original_len - len(self._audit_entries)

    # ---------------------------------------------------------------------------
    # Phase 5 — Plugin Service Catalog Storage
    # ---------------------------------------------------------------------------

    def init_service_storage(self) -> None:
        """Initializes internal structures for plugin service registrations."""
        with self._lock:
            if not hasattr(self, "_service_registrations"):
                self._service_registrations: Dict[str, ServiceRegistration] = {}  # registration_id -> ServiceRegistration
            if not hasattr(self, "_service_instances"):
                self._service_instances: Dict[str, Any] = {}  # registration_id -> service implementation class/instance

    def add_service_registration(self, reg: ServiceRegistration, instance: Any) -> None:
        """Saves a service registration mapping."""
        with self._lock:
            self.init_service_storage()
            self._service_registrations[reg.registration_id] = reg
            self._service_instances[reg.registration_id] = instance

    def remove_service_registration(self, reg_id: str) -> bool:
        """Removes a service registration mapping."""
        with self._lock:
            self.init_service_storage()
            if reg_id in self._service_registrations:
                del self._service_registrations[reg_id]
                self._service_instances.pop(reg_id, None)
                return True
            return False

    def query_service_registrations(self, interface_name: Optional[str] = None, provider_plugin_id: Optional[str] = None) -> List[ServiceRegistration]:
        """Queries registered services by interface_name or provider_plugin_id."""
        with self._lock:
            self.init_service_storage()
            results = list(self._service_registrations.values())
            if interface_name is not None:
                results = [r for r in results if r.descriptor.interface_name == interface_name]
            if provider_plugin_id is not None:
                results = [r for r in results if r.descriptor.provider_plugin_id == provider_plugin_id]
            return results

    def get_service_instance(self, reg_id: str) -> Optional[Any]:
        """Retrieves the service instance object for a registration."""
        with self._lock:
            self.init_service_storage()
            return self._service_instances.get(reg_id)

    # ---------------------------------------------------------------------------
    # Phase 6 — Plugin Packaging & Installation Registry Storage
    # ---------------------------------------------------------------------------

    def init_packaging_storage(self) -> None:
        """Initializes internal structures for plugin packages and installation history."""
        with self._lock:
            if not hasattr(self, "_packages"):
                self._packages: Dict[str, PluginPackage] = {}  # plugin_id -> PluginPackage
            if not hasattr(self, "_installation_history"):
                self._installation_history: Dict[str, List[PluginInstallationRecord]] = {}  # plugin_id -> list of records

    def record_package_installation(self, record: PluginInstallationRecord, package: PluginPackage) -> None:
        """Saves a package installation record and metadata."""
        with self._lock:
            self.init_packaging_storage()
            self._packages[record.plugin_id] = package
            if record.plugin_id not in self._installation_history:
                self._installation_history[record.plugin_id] = []
            self._installation_history[record.plugin_id].append(record)

    def record_package_uninstallation(self, plugin_id: str) -> bool:
        """Removes the package registry matching plugin_id and marks history uninstalled."""
        with self._lock:
            self.init_packaging_storage()
            if plugin_id in self._packages:
                del self._packages[plugin_id]
                # Mark latest record in history as UNINSTALLED
                history = self._installation_history.get(plugin_id, [])
                if history:
                    last_record = history[-1]
                    # Since models are frozen, we create a new instance with status="UNINSTALLED"
                    updated_record = PluginInstallationRecord(
                        plugin_id=last_record.plugin_id,
                        installed_version=last_record.installed_version,
                        installed_at=last_record.installed_at,
                        archive_checksum=last_record.archive_checksum,
                        install_path=last_record.install_path,
                        status="UNINSTALLED",
                    )
                    self._installation_history[plugin_id][-1] = updated_record
                return True
            return False

    def query_installed_package(self, plugin_id: str) -> Optional[PluginPackage]:
        """Retrieves installed package configuration details matching plugin_id."""
        with self._lock:
            self.init_packaging_storage()
            return self._packages.get(plugin_id)

    def query_installation_history(self, plugin_id: str) -> List[PluginInstallationRecord]:
        """Queries historical records for dynamic package installations matching plugin_id."""
        with self._lock:
            self.init_packaging_storage()
            return list(self._installation_history.get(plugin_id, []))

    def list_installed_packages(self) -> List[PluginPackage]:
        """Lists all registered installed plugin packages."""
        with self._lock:
            self.init_packaging_storage()
            return list(self._packages.values())

    # ---------------------------------------------------------------------------
    # Phase 7 — Plugin Diagnostics & Telemetry Registry Storage
    # ---------------------------------------------------------------------------

    def init_diagnostic_storage(self) -> None:
        """Initializes internal structures for plugin passive diagnostics and telemetry."""
        with self._lock:
            if not hasattr(self, "_diagnostic_records"):
                self._diagnostic_records: Dict[str, List[PluginDiagnosticRecord]] = {}  # plugin_id -> list
            if not hasattr(self, "_health_snapshots"):
                self._health_snapshots: Dict[str, List[PluginHealthSnapshot]] = {}  # plugin_id -> list
            if not hasattr(self, "_telemetry_events"):
                self._telemetry_events: Dict[str, List[PluginTelemetryEvent]] = {}  # plugin_id -> list
            if not hasattr(self, "_runtime_metrics"):
                self._runtime_metrics: Dict[str, PluginRuntimeMetrics] = {}  # plugin_id -> PluginRuntimeMetrics
            if not hasattr(self, "_failure_records"):
                self._failure_records: Dict[str, List[PluginFailureRecord]] = {}  # plugin_id -> list
            if not hasattr(self, "_statistics"):
                self._statistics: Dict[str, PluginStatistics] = {}  # plugin_id -> PluginStatistics

    def record_diagnostic(self, rec: PluginDiagnosticRecord) -> None:
        """Appends a diagnostic log entry."""
        with self._lock:
            self.init_diagnostic_storage()
            if rec.plugin_id not in self._diagnostic_records:
                self._diagnostic_records[rec.plugin_id] = []
            self._diagnostic_records[rec.plugin_id].append(rec)

    def record_health_snapshot(self, snap: PluginHealthSnapshot) -> None:
        """Appends a health evaluation snapshot."""
        with self._lock:
            self.init_diagnostic_storage()
            if snap.plugin_id not in self._health_snapshots:
                self._health_snapshots[snap.plugin_id] = []
            self._health_snapshots[snap.plugin_id].append(snap)

    def record_telemetry(self, event: PluginTelemetryEvent) -> None:
        """Appends a passive telemetry tracking event."""
        with self._lock:
            self.init_diagnostic_storage()
            if event.plugin_id not in self._telemetry_events:
                self._telemetry_events[event.plugin_id] = []
            self._telemetry_events[event.plugin_id].append(event)

    def record_failure(self, fail: PluginFailureRecord) -> None:
        """Appends a lifecycle or execution failure log."""
        with self._lock:
            self.init_diagnostic_storage()
            if fail.plugin_id not in self._failure_records:
                self._failure_records[fail.plugin_id] = []
            self._failure_records[fail.plugin_id].append(fail)

    def update_runtime_metrics(self, plugin_id: str, metrics: PluginRuntimeMetrics) -> None:
        """Updates the active runtime resource metrics snapshot."""
        with self._lock:
            self.init_diagnostic_storage()
            self._runtime_metrics[plugin_id] = metrics

    def update_statistics(self, stats: PluginStatistics) -> None:
        """Updates the consolidated telemetry statistics for the plugin."""
        with self._lock:
            self.init_diagnostic_storage()
            self._statistics[stats.plugin_id] = stats

    def query_diagnostics(self, plugin_id: str) -> List[PluginDiagnosticRecord]:
        """Queries diagnostic records matching plugin_id."""
        with self._lock:
            self.init_diagnostic_storage()
            return list(self._diagnostic_records.get(plugin_id, []))

    def query_health_snapshots(self, plugin_id: str) -> List[PluginHealthSnapshot]:
        """Queries health snapshots matching plugin_id."""
        with self._lock:
            self.init_diagnostic_storage()
            return list(self._health_snapshots.get(plugin_id, []))

    def query_telemetry(self, plugin_id: str) -> List[PluginTelemetryEvent]:
        """Queries passive telemetry events matching plugin_id."""
        with self._lock:
            self.init_diagnostic_storage()
            return list(self._telemetry_events.get(plugin_id, []))

    def query_failures(self, plugin_id: str) -> List[PluginFailureRecord]:
        """Queries failure records matching plugin_id."""
        with self._lock:
            self.init_diagnostic_storage()
            return list(self._failure_records.get(plugin_id, []))

    def get_runtime_metrics(self, plugin_id: str) -> PluginRuntimeMetrics:
        """Gets active metrics, returning empty defaults if none recorded."""
        with self._lock:
            self.init_diagnostic_storage()
            return self._runtime_metrics.get(plugin_id, PluginRuntimeMetrics())

    def get_statistics(self, plugin_id: str) -> PluginStatistics:
        """Gets active statistics summary, returning empty defaults if none recorded."""
        with self._lock:
            self.init_diagnostic_storage()
            return self._statistics.get(plugin_id, PluginStatistics(plugin_id=plugin_id))

    def clear_diagnostics(self, plugin_id: str) -> None:
        """Clears all historical diagnostic streams for the targeted plugin."""
        with self._lock:
            self.init_diagnostic_storage()
            self._diagnostic_records.pop(plugin_id, None)
            self._health_snapshots.pop(plugin_id, None)
            self._telemetry_events.pop(plugin_id, None)
            self._failure_records.pop(plugin_id, None)
            self._runtime_metrics.pop(plugin_id, None)
            self._statistics.pop(plugin_id, None)

    # ---------------------------------------------------------------------------
    # Phase 8 — Plugin Configuration Registry Storage
    # ---------------------------------------------------------------------------

    def init_config_storage(self) -> None:
        """Initializes internal structures for plugin configuration and persistence."""
        with self._lock:
            if not hasattr(self, "_config_schemas"):
                self._config_schemas: Dict[str, PluginConfigurationSchema] = {}  # plugin_id -> PluginConfigurationSchema
            if not hasattr(self, "_config_values"):
                self._config_values: Dict[str, Dict[str, Any]] = {}  # plugin_id -> current config settings dict
            if not hasattr(self, "_config_profiles"):
                self._config_profiles: Dict[str, Dict[str, PluginConfigurationProfile]] = {}  # plugin_id -> {profile_id -> profile}
            if not hasattr(self, "_config_snapshots"):
                self._config_snapshots: Dict[str, List[PluginConfigurationSnapshot]] = {}  # plugin_id -> list
            if not hasattr(self, "_config_history"):
                self._config_history: Dict[str, List[PluginConfigurationHistory]] = {}  # plugin_id -> list
            if not hasattr(self, "_config_migrations"):
                self._config_migrations: Dict[str, List[PluginConfigurationMigration]] = {}  # plugin_id -> list

    def register_config_schema(self, schema: PluginConfigurationSchema) -> None:
        """Saves a configuration schema."""
        with self._lock:
            self.init_config_storage()
            self._config_schemas[schema.plugin_id] = schema

    def get_config_schema(self, plugin_id: str) -> Optional[PluginConfigurationSchema]:
        """Gets the configuration schema matching plugin_id."""
        with self._lock:
            self.init_config_storage()
            return self._config_schemas.get(plugin_id)

    def set_config_values(self, plugin_id: str, values: Dict[str, Any]) -> None:
        """Saves active configuration values dictionary."""
        with self._lock:
            self.init_config_storage()
            self._config_values[plugin_id] = dict(values)

    def get_config_values(self, plugin_id: str) -> Dict[str, Any]:
        """Gets active configuration settings dictionary."""
        with self._lock:
            self.init_config_storage()
            return dict(self._config_values.get(plugin_id, {}))

    def save_config_profile(self, profile: PluginConfigurationProfile) -> None:
        """Saves a named configuration profile override."""
        with self._lock:
            self.init_config_storage()
            if profile.plugin_id not in self._config_profiles:
                self._config_profiles[profile.plugin_id] = {}
            self._config_profiles[profile.plugin_id][profile.profile_id] = profile

    def get_config_profiles(self, plugin_id: str) -> List[PluginConfigurationProfile]:
        """Gets all profiles registered for a specific plugin."""
        with self._lock:
            self.init_config_storage()
            return list(self._config_profiles.get(plugin_id, {}).values())

    def save_config_snapshot(self, snapshot: PluginConfigurationSnapshot) -> None:
        """Appends a configuration settings snapshot."""
        with self._lock:
            self.init_config_storage()
            if snapshot.plugin_id not in self._config_snapshots:
                self._config_snapshots[snapshot.plugin_id] = []
            self._config_snapshots[snapshot.plugin_id].append(snapshot)

    def get_config_snapshots(self, plugin_id: str) -> List[PluginConfigurationSnapshot]:
        """Gets all snapshots matching plugin_id."""
        with self._lock:
            self.init_config_storage()
            return list(self._config_snapshots.get(plugin_id, []))

    def record_config_history(self, record: PluginConfigurationHistory) -> None:
        """Appends a configuration updates history entry."""
        with self._lock:
            self.init_config_storage()
            if record.plugin_id not in self._config_history:
                self._config_history[record.plugin_id] = []
            self._config_history[record.plugin_id].append(record)

    def get_config_history(self, plugin_id: str) -> List[PluginConfigurationHistory]:
        """Gets config change history records matching plugin_id."""
        with self._lock:
            self.init_config_storage()
            return list(self._config_history.get(plugin_id, []))

    def record_config_migration(self, migration: PluginConfigurationMigration) -> None:
        """Saves a configuration migration step log."""
        with self._lock:
            self.init_config_storage()
            if migration.plugin_id not in self._config_migrations:
                self._config_migrations[migration.plugin_id] = []
            self._config_migrations[migration.plugin_id].append(migration)

    def get_config_migrations(self, plugin_id: str) -> List[PluginConfigurationMigration]:
        """Gets config migrations matching plugin_id."""
        with self._lock:
            self.init_config_storage()
            return list(self._config_migrations.get(plugin_id, []))

    def clear_config(self, plugin_id: str) -> None:
        """Clears all configuration data for the plugin."""
        with self._lock:
            self.init_config_storage()
            self._config_schemas.pop(plugin_id, None)
            self._config_values.pop(plugin_id, None)
            self._config_profiles.pop(plugin_id, None)
            self._config_snapshots.pop(plugin_id, None)
            self._config_history.pop(plugin_id, None)
            self._config_migrations.pop(plugin_id, None)

    # ---------------------------------------------------------------------------
    # Phase 8 — Plugin Certification Registry Storage
    # ---------------------------------------------------------------------------

    def init_certification_storage(self) -> None:
        """Initializes internal structures for plugin certification reports."""
        with self._lock:
            if not hasattr(self, "_certification_reports"):
                self._certification_reports: Dict[str, List[PluginCertificationReport]] = {}  # plugin_id -> list of reports

    def save_certification_report(self, report: PluginCertificationReport) -> None:
        """Saves a certification execution report in history."""
        with self._lock:
            self.init_certification_storage()
            if report.plugin_id not in self._certification_reports:
                self._certification_reports[report.plugin_id] = []
            self._certification_reports[report.plugin_id].append(report)

    def query_certification_reports(self, plugin_id: str) -> List[PluginCertificationReport]:
        """Queries historical certification reports matching plugin_id."""
        with self._lock:
            self.init_certification_storage()
            return list(self._certification_reports.get(plugin_id, []))

    def clear_certification_history(self, plugin_id: str) -> None:
        """Clears certification history logs for the plugin."""
        with self._lock:
            self.init_certification_storage()
            self._certification_reports.pop(plugin_id, None)

    # ---------------------------------------------------------------------------
    # Phase 9 — Plugin CLI & Workspace Registry Storage
    # ---------------------------------------------------------------------------

    def init_cli_storage(self) -> None:
        """Initializes internal structures for CLI history log entries and workspaces."""
        with self._lock:
            if not hasattr(self, "_cli_history"):
                self._cli_history: List[PluginCommandHistory] = []
            if not hasattr(self, "_workspaces"):
                self._workspaces: Dict[str, PluginWorkspace] = {}
            if not hasattr(self, "_templates"):
                self._templates: Dict[str, PluginTemplate] = {}
            if not hasattr(self, "_scaffolds"):
                self._scaffolds: Dict[str, List[PluginScaffold]] = {}

    def record_command_history(self, record: PluginCommandHistory) -> None:
        """Appends CLI command execution logs to history."""
        with self._lock:
            self.init_cli_storage()
            self._cli_history.append(record)

    def get_command_history(self) -> List[PluginCommandHistory]:
        """Gets all command executions history log records."""
        with self._lock:
            self.init_cli_storage()
            return list(self._cli_history)

    def save_workspace(self, workspace: PluginWorkspace) -> None:
        """Saves workspace metadata snapshots."""
        with self._lock:
            self.init_cli_storage()
            self._workspaces[workspace.workspace_id] = workspace

    def get_workspace(self, workspace_id: str) -> Optional[PluginWorkspace]:
        """Gets active workspace matching workspace_id."""
        with self._lock:
            self.init_cli_storage()
            return self._workspaces.get(workspace_id)

    def list_workspaces(self) -> List[PluginWorkspace]:
        """Lists all registered workspaces."""
        with self._lock:
            self.init_cli_storage()
            return list(self._workspaces.values())

    def save_template(self, template: PluginTemplate) -> None:
        """Registers a named plugin template framework."""
        with self._lock:
            self.init_cli_storage()
            self._templates[template.template_id] = template

    def get_template(self, template_id: str) -> Optional[PluginTemplate]:
        """Gets active template matching template_id."""
        with self._lock:
            self.init_cli_storage()
            return self._templates.get(template_id)

    def save_scaffold(self, scaffold: PluginScaffold) -> None:
        """Saves generated plugin scaffold details logs."""
        with self._lock:
            self.init_cli_storage()
            if scaffold.plugin_id not in self._scaffolds:
                self._scaffolds[scaffold.plugin_id] = []
            self._scaffolds[scaffold.plugin_id].append(scaffold)

    def get_scaffolds(self, plugin_id: str) -> List[PluginScaffold]:
        """Gets generated scaffold files details mapping matching plugin_id."""
        with self._lock:
            self.init_cli_storage()
            return list(self._scaffolds.get(plugin_id, []))

    def clear_cli_history(self) -> None:
        """Resets CLI execution history metrics streams."""
        with self._lock:
            self.init_cli_storage()
            self._cli_history.clear()









