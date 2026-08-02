"""Plugin Configuration & Persistence Management Engine.

Supports registering strongly typed configuration schemas, validation checks,
profiles activation, migration execution, and deterministic configuration import/export.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from flock.plugins.exceptions import (
    PluginConfigurationConflictError,
    PluginSettingsConfigurationError,
    PluginConfigurationImportError,
    PluginConfigurationMigrationError,
    PluginConfigurationValidationError,
)
from flock.plugins.models import (
    PluginConfigurationExport,
    PluginConfigurationHistory,
    PluginConfigurationMigration,
    PluginConfigurationProfile,
    PluginConfigurationSchema,
    PluginConfigurationSnapshot,
    PluginConfigurationValidationResult,
)
from flock.plugins.registry import PluginRegistry

logger = structlog.get_logger()


class PluginConfigurationEngine:
    """Manages active configuration values, profiles, history transitions, and migrations."""

    def __init__(self, registry: PluginRegistry) -> None:
        self._registry = registry

    def register_schema(self, schema: PluginConfigurationSchema) -> None:
        """Saves a configuration schema layout and initializes values to defaults."""
        self._registry.register_config_schema(schema)

        # Generate default configuration settings dictionary
        defaults: Dict[str, Any] = {}
        for f in schema.fields.values():
            defaults[f.name] = f.default_value

        self._registry.set_config_values(schema.plugin_id, defaults)

    def retrieve_configuration(self, plugin_id: str) -> Dict[str, Any]:
        """Gets active configuration values dictionary matching plugin_id."""
        return self._registry.get_config_values(plugin_id)

    def update_configuration(
        self,
        plugin_id: str,
        updates: Dict[str, Any],
        reason: Optional[str] = None,
    ) -> PluginConfigurationValidationResult:
        """Validates updates against schema, applies values, and records history change records."""
        schema = self._registry.get_config_schema(plugin_id)
        if schema is None:
            raise PluginSettingsConfigurationError(f"No configuration schema found for plugin '{plugin_id}'.")

        current = self._registry.get_config_values(plugin_id)
        proposed = dict(current)
        proposed.update(updates)

        # Validate proposed settings
        val_res = self.validate_settings(proposed, schema)
        if not val_res.success:
            raise PluginConfigurationValidationError(f"Configuration updates validation failed: {', '.join(val_res.errors)}")

        # Save settings and write to history
        self._registry.set_config_values(plugin_id, proposed)

        history_record = PluginConfigurationHistory(
            history_id=str(uuid.uuid4()),
            plugin_id=plugin_id,
            previous_settings=current,
            new_settings=proposed,
            changed_at=datetime.now(timezone.utc),
            reason=reason,
        )
        self._registry.record_config_history(history_record)

        return val_res

    def validate_settings(
        self,
        settings: Dict[str, Any],
        schema: PluginConfigurationSchema,
    ) -> PluginConfigurationValidationResult:
        """Audits target setting key types and matches schema rules."""
        errors: List[str] = []
        warnings: List[str] = []

        # Check required fields and type compatibility
        for f in schema.fields.values():
            val = settings.get(f.name)
            if val is None:
                if f.is_required:
                    errors.append(f"Missing required configuration field: '{f.name}'.")
                continue

            # Basic type verification helper
            t_name = f.type_name.lower()
            if t_name == "int" and not isinstance(val, int):
                errors.append(f"Type mismatch for field '{f.name}': expected 'int', found '{type(val).__name__}'.")
            elif t_name == "bool" and not isinstance(val, bool):
                errors.append(f"Type mismatch for field '{f.name}': expected 'bool', found '{type(val).__name__}'.")
            elif t_name == "float" and not isinstance(val, (float, int)):
                errors.append(f"Type mismatch for field '{f.name}': expected 'float', found '{type(val).__name__}'.")
            elif t_name == "string" and not isinstance(val, str):
                errors.append(f"Type mismatch for field '{f.name}': expected 'string', found '{type(val).__name__}'.")

        # Warn about unregistered config parameters
        for key in settings:
            if key not in schema.fields:
                warnings.append(f"Unrecognized configuration key: '{key}' not in schema.")

        return PluginConfigurationValidationResult(
            success=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def rollback(self, plugin_id: str) -> bool:
        """Rolls back the active configuration to the prior state recorded in history."""
        history = self._registry.get_config_history(plugin_id)
        if not history:
            return False

        last_change = history[-1]
        self._registry.set_config_values(plugin_id, last_change.previous_settings)

        # Append a recovery rollback history record
        rollback_record = PluginConfigurationHistory(
            history_id=str(uuid.uuid4()),
            plugin_id=plugin_id,
            previous_settings=last_change.new_settings,
            new_settings=last_change.previous_settings,
            changed_at=datetime.now(timezone.utc),
            reason="Rollback to previous configuration state",
        )
        self._registry.record_config_history(rollback_record)
        return True

    def execute_migration(
        self,
        plugin_id: str,
        target_version: str,
        migration_handler: Any,  # Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """Upgrades config version mapping applying custom mapper functions."""
        schema = self._registry.get_config_schema(plugin_id)
        if schema is None:
            raise PluginConfigurationMigrationError(f"No schema found for plugin '{plugin_id}' to migrate.")

        current_values = self._registry.get_config_values(plugin_id)
        try:
            migrated_values = migration_handler(current_values)
        except Exception as exc:
            raise PluginConfigurationMigrationError(f"Migration handler failed: {exc}") from exc

        # Update values and log migration step record
        self._registry.set_config_values(plugin_id, migrated_values)
        
        migration_record = PluginConfigurationMigration(
            migration_id=str(uuid.uuid4()),
            plugin_id=plugin_id,
            from_version=schema.version,
            to_version=target_version,
            migration_key=f"{schema.version}_to_{target_version}",
        )
        self._registry.record_config_migration(migration_record)

        # Update schema version reference
        updated_schema = PluginConfigurationSchema(
            plugin_id=plugin_id,
            version=target_version,
            fields=schema.fields,
        )
        self._registry.register_config_schema(updated_schema)

    def create_snapshot(self, plugin_id: str) -> PluginConfigurationSnapshot:
        """Generates an immutable snapshot containing current settings."""
        settings = self._registry.get_config_values(plugin_id)
        snap = PluginConfigurationSnapshot(
            snapshot_id=str(uuid.uuid4()),
            plugin_id=plugin_id,
            settings=dict(settings),
            created_at=datetime.now(timezone.utc),
        )
        self._registry.save_config_snapshot(snap)
        return snap

    def activate_profile(self, plugin_id: str, profile_id: str) -> None:
        """Applies configuration profile override settings."""
        profiles = self._registry.get_config_profiles(plugin_id)
        target_profile = None
        for p in profiles:
            if p.profile_id == profile_id:
                target_profile = p
                break

        if target_profile is None:
            raise PluginConfigurationConflictError(f"Configuration profile '{profile_id}' not found.")

        # Save profile as active and apply settings
        self.update_configuration(
            plugin_id,
            target_profile.settings,
            reason=f"Activated configuration profile '{target_profile.profile_name}'",
        )

        # Toggle is_active flag on profile records
        for p in profiles:
            updated_p = PluginConfigurationProfile(
                profile_id=p.profile_id,
                profile_name=p.profile_name,
                plugin_id=plugin_id,
                settings=p.settings,
                is_active=(p.profile_id == profile_id),
            )
            self._registry.save_config_profile(updated_p)

    def save_profile(self, profile: PluginConfigurationProfile) -> None:
        """Saves a named configuration profile override to registry."""
        self._registry.save_config_profile(profile)

    def reset_to_defaults(self, plugin_id: str) -> None:
        """Restores configuration settings to schema defaults."""
        schema = self._registry.get_config_schema(plugin_id)
        if schema is None:
            raise PluginSettingsConfigurationError(f"No schema found to reset defaults for plugin '{plugin_id}'.")

        defaults: Dict[str, Any] = {}
        for f in schema.fields.values():
            defaults[f.name] = f.default_value

        self.update_configuration(plugin_id, defaults, reason="Reset configuration settings to schema defaults")

    def export_configuration(self, plugin_id: str) -> PluginConfigurationExport:
        """Exports active configuration values mapped to export payload blocks."""
        schema = self._registry.get_config_schema(plugin_id)
        version = schema.version if schema else "1.0.0"
        settings = self._registry.get_config_values(plugin_id)

        return PluginConfigurationExport(
            plugin_id=plugin_id,
            version=version,
            exported_at=datetime.now(timezone.utc),
            settings=dict(settings),
        )

    def import_configuration(self, export_bundle: PluginConfigurationExport) -> None:
        """Imports configuration values from export payload blocks."""
        schema = self._registry.get_config_schema(export_bundle.plugin_id)
        if schema is None:
            raise PluginConfigurationImportError(f"Cannot import configuration: no schema registered for plugin '{export_bundle.plugin_id}'.")

        # Validate imported configuration settings
        val_res = self.validate_settings(export_bundle.settings, schema)
        if not val_res.success:
            raise PluginConfigurationImportError(f"Import configuration validation failed: {', '.join(val_res.errors)}")

        self.update_configuration(
            export_bundle.plugin_id,
            export_bundle.settings,
            reason="Imported configuration settings bundle",
        )
