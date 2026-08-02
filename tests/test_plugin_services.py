"""Unit and integration tests for the Plugin Service Registry and Dependency Injection."""

from __future__ import annotations

import pytest
from typing import List

from flock.plugins.models import (
    InjectionContext,
    ServiceDependency,
    PluginManifest,
)
from flock.plugins.registry import PluginRegistry
from flock.plugins.services import PluginServiceRegistry
from flock.plugins.exceptions import (
    DuplicateServiceError,
    ServiceInjectionError,
    ServiceResolutionError,
)


class MockDatabaseService:
    def query(self) -> str:
        return "data"


class MockLoggingService:
    def log(self, message: str) -> str:
        return f"logged: {message}"


class TargetPluginInstance:
    def __init__(self) -> None:
        self.db_service = None
        self.logging_service = None


def test_service_registration_and_resolution() -> None:
    registry = PluginRegistry()
    services = PluginServiceRegistry(registry)

    db_instance = MockDatabaseService()
    reg_id = services.register_service(
        service_id="db-service-1",
        interface_name="DbService",
        provider_plugin_id="plugin-db",
        instance=db_instance,
    )
    assert reg_id is not None

    resolved = services.resolve_service("DbService")
    assert resolved == db_instance
    assert services.service_exists("DbService") is True


def test_duplicate_registration_rejection() -> None:
    registry = PluginRegistry()
    services = PluginServiceRegistry(registry)

    db_instance1 = MockDatabaseService()
    db_instance2 = MockDatabaseService()

    services.register_service(
        service_id="db-service-1",
        interface_name="DbService",
        provider_plugin_id="plugin-db",
        instance=db_instance1,
    )

    # Re-registering duplicate service_id under same interface should fail by default
    with pytest.raises(DuplicateServiceError):
        services.register_service(
            service_id="db-service-1",
            interface_name="DbService",
            provider_plugin_id="plugin-db-new",
            instance=db_instance2,
            allow_replace=False,
        )


def test_allow_replace_policy() -> None:
    registry = PluginRegistry()
    services = PluginServiceRegistry(registry)

    db_instance1 = MockDatabaseService()
    db_instance2 = MockDatabaseService()

    services.register_service(
        service_id="db-service-1",
        interface_name="DbService",
        provider_plugin_id="plugin-db",
        instance=db_instance1,
    )

    # With allow_replace=True, duplicate is replaced
    services.register_service(
        service_id="db-service-1",
        interface_name="DbService",
        provider_plugin_id="plugin-db",
        instance=db_instance2,
        allow_replace=True,
    )

    resolved = services.resolve_service("DbService")
    assert resolved == db_instance2


def test_dependency_injection() -> None:
    registry = PluginRegistry()
    services = PluginServiceRegistry(registry)

    db_instance = MockDatabaseService()
    log_instance = MockLoggingService()

    services.register_service("db-1", "DbService", "plugin-db", db_instance)
    services.register_service("log-1", "LoggingService", "plugin-log", log_instance)

    target = TargetPluginInstance()
    deps = [
        ServiceDependency(interface_name="DbService"),
        ServiceDependency(interface_name="LoggingService"),
    ]
    context = InjectionContext(
        target_plugin_id="plugin-target",
        target_class_name="TargetPluginInstance",
    )

    services.inject_dependencies(target, deps, context)

    # Fields should be resolved to mock services using snake_case converter
    assert target.db_service == db_instance
    assert target.logging_service == log_instance


def test_dependency_injection_missing_required_raises() -> None:
    registry = PluginRegistry()
    services = PluginServiceRegistry(registry)

    target = TargetPluginInstance()
    # Required dependency is missing
    deps = [ServiceDependency(interface_name="DbService", is_optional=False)]
    context = InjectionContext(
        target_plugin_id="plugin-target",
        target_class_name="TargetPluginInstance",
    )

    with pytest.raises(ServiceInjectionError):
        services.inject_dependencies(target, deps, context)


def test_dependency_injection_missing_optional_passes() -> None:
    registry = PluginRegistry()
    services = PluginServiceRegistry(registry)

    target = TargetPluginInstance()
    # Optional dependency is missing
    deps = [ServiceDependency(interface_name="DbService", is_optional=True)]
    context = InjectionContext(
        target_plugin_id="plugin-target",
        target_class_name="TargetPluginInstance",
    )

    services.inject_dependencies(target, deps, context)
    assert target.db_service is None


def test_resolve_all_implementations() -> None:
    registry = PluginRegistry()
    services = PluginServiceRegistry(registry)

    db1 = MockDatabaseService()
    db2 = MockDatabaseService()

    services.register_service("db-1", "DbService", "plugin-db1", db1)
    services.register_service("db-2", "DbService", "plugin-db2", db2)

    all_db = services.resolve_all("DbService")
    assert len(all_db) == 2
    assert db1 in all_db
    assert db2 in all_db
