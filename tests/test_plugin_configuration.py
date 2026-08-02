"""Unit and integration tests for Plugin Configuration Management & Persistence."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from flock.plugins.models import (
    PluginConfigurationField,
    PluginConfigurationProfile,
    PluginConfigurationSchema,
)
from flock.plugins.registry import PluginRegistry
from flock.plugins.configuration import PluginConfigurationEngine
from flock.plugins.exceptions import (
    PluginConfigurationValidationError,
    PluginConfigurationMigrationError,
    PluginConfigurationImportError,
)


@pytest.fixture
def mock_schema() -> PluginConfigurationSchema:
    fields = {
        "db_host": PluginConfigurationField(
            name="db_host",
            type_name="string",
            default_value="localhost",
            is_required=True,
        ),
        "db_port": PluginConfigurationField(
            name="db_port",
            type_name="int",
            default_value=5432,
            is_required=False,
        ),
        "enable_cache": PluginConfigurationField(
            name="enable_cache",
            type_name="bool",
            default_value=True,
        )
    }
    return PluginConfigurationSchema(
        plugin_id="plugin-db",
        version="1.0.0",
        fields=fields,
    )


def test_schema_registration_and_defaults(mock_schema: PluginConfigurationSchema) -> None:
    registry = PluginRegistry()
    engine = PluginConfigurationEngine(registry)

    engine.register_schema(mock_schema)

    schema = registry.get_config_schema("plugin-db")
    assert schema is not None
    assert schema.version == "1.0.0"

    # Default configuration values should be loaded
    config = engine.retrieve_configuration("plugin-db")
    assert config["db_host"] == "localhost"
    assert config["db_port"] == 5432
    assert config["enable_cache"] is True


def test_validation_fails_on_type_mismatch(mock_schema: PluginConfigurationSchema) -> None:
    registry = PluginRegistry()
    engine = PluginConfigurationEngine(registry)
    engine.register_schema(mock_schema)

    # db_port must be an integer
    with pytest.raises(PluginConfigurationValidationError):
        engine.update_configuration("plugin-db", {"db_port": "not-an-int"})


def test_validation_fails_on_missing_required(mock_schema: PluginConfigurationSchema) -> None:
    registry = PluginRegistry()
    engine = PluginConfigurationEngine(registry)
    engine.register_schema(mock_schema)

    # db_host is required but set to None
    with pytest.raises(PluginConfigurationValidationError):
        engine.update_configuration("plugin-db", {"db_host": None})


def test_update_and_rollback(mock_schema: PluginConfigurationSchema) -> None:
    registry = PluginRegistry()
    engine = PluginConfigurationEngine(registry)
    engine.register_schema(mock_schema)

    engine.update_configuration("plugin-db", {"db_host": "127.0.0.1"})
    assert engine.retrieve_configuration("plugin-db")["db_host"] == "127.0.0.1"

    # Roll back to localhost default
    success = engine.rollback("plugin-db")
    assert success is True
    assert engine.retrieve_configuration("plugin-db")["db_host"] == "localhost"


def test_config_migrations(mock_schema: PluginConfigurationSchema) -> None:
    registry = PluginRegistry()
    engine = PluginConfigurationEngine(registry)
    engine.register_schema(mock_schema)

    def migration_handler(old_config: dict) -> dict:
        new_config = dict(old_config)
        new_config["db_url"] = f"postgresql://{old_config['db_host']}:{old_config['db_port']}"
        return new_config

    engine.execute_migration("plugin-db", "1.1.0", migration_handler)

    migrated_vals = engine.retrieve_configuration("plugin-db")
    assert migrated_vals["db_url"] == "postgresql://localhost:5432"

    migrations = registry.get_config_migrations("plugin-db")
    assert len(migrations) == 1
    assert migrations[0].from_version == "1.0.0"
    assert migrations[0].to_version == "1.1.0"


def test_export_import_loop(mock_schema: PluginConfigurationSchema) -> None:
    registry = PluginRegistry()
    engine = PluginConfigurationEngine(registry)
    engine.register_schema(mock_schema)

    engine.update_configuration("plugin-db", {"db_host": "remote-host", "db_port": 9999})
    export_bundle = engine.export_configuration("plugin-db")

    # Clear config and register schema again to reset
    registry.clear_config("plugin-db")
    engine.register_schema(mock_schema)

    # Import back to verify state restoration
    engine.import_configuration(export_bundle)
    imported_vals = engine.retrieve_configuration("plugin-db")
    assert imported_vals["db_host"] == "remote-host"
    assert imported_vals["db_port"] == 9999


def test_profile_activation(mock_schema: PluginConfigurationSchema) -> None:
    registry = PluginRegistry()
    engine = PluginConfigurationEngine(registry)
    engine.register_schema(mock_schema)

    prod_profile = PluginConfigurationProfile(
        profile_id="prod",
        profile_name="Production Profile",
        plugin_id="plugin-db",
        settings={"db_host": "prod-db-server", "db_port": 5432, "enable_cache": True},
        is_active=False
    )
    engine.save_profile(prod_profile)

    engine.activate_profile("plugin-db", "prod")

    active_config = engine.retrieve_configuration("plugin-db")
    assert active_config["db_host"] == "prod-db-server"

    # Profile state in registry should reflect active
    profiles = registry.get_config_profiles("plugin-db")
    assert len(profiles) == 1
    assert profiles[0].is_active is True


def test_reset_to_defaults(mock_schema: PluginConfigurationSchema) -> None:
    registry = PluginRegistry()
    engine = PluginConfigurationEngine(registry)
    engine.register_schema(mock_schema)

    engine.update_configuration("plugin-db", {"db_host": "custom-host"})
    engine.reset_to_defaults("plugin-db")

    assert engine.retrieve_configuration("plugin-db")["db_host"] == "localhost"
