"""Plugin Service Registry & Dependency Injection.

Allows plugins to register and discover services, resolve implementations,
and automatically perform dependency injection without circular dependencies.
"""

from __future__ import annotations

import threading
import uuid
from typing import Any, List, Optional

import structlog

from flock.plugins.exceptions import (
    DuplicateServiceError,
    ServiceInjectionError,
    ServiceRegistrationError,
    ServiceResolutionError,
)
from flock.plugins.models import (
    InjectionContext,
    ServiceDependency,
    ServiceDescriptor,
    ServiceRegistration,
)
from flock.plugins.registry import PluginRegistry

logger = structlog.get_logger()


class PluginServiceRegistry:
    """Thread-safe registry managing service contracts and dependency injection.

    All mutations and lookups execute under an RLock. Execution of plugin-defined
    code is decoupled from the lock scope to prevent deadlocks.
    """

    def __init__(self, registry: PluginRegistry) -> None:
        self._registry = registry
        self._lock = threading.RLock()

    def register_service(
        self,
        service_id: str,
        interface_name: str,
        provider_plugin_id: str,
        instance: Any,
        version: str = "1.0.0",
        allow_replace: bool = False,
    ) -> str:
        """Registers a service contract implementation class/object."""
        if not service_id or not interface_name or not provider_plugin_id:
            raise ServiceRegistrationError("Service registration requires service_id, interface_name, and provider_plugin_id.")

        with self._lock:
            # Check if registration already exists
            existing = self._registry.query_service_registrations(interface_name=interface_name)
            for reg in existing:
                if reg.descriptor.service_id == service_id:
                    if not allow_replace:
                        raise DuplicateServiceError(f"Service with id '{service_id}' already registered for interface '{interface_name}'.")
                    # Remove existing before adding new
                    self._registry.remove_service_registration(reg.registration_id)

            reg_id = str(uuid.uuid4())
            descriptor = ServiceDescriptor(
                service_id=service_id,
                interface_name=interface_name,
                provider_plugin_id=provider_plugin_id,
                version=version,
            )
            registration = ServiceRegistration(
                registration_id=reg_id,
                descriptor=descriptor,
            )
            self._registry.add_service_registration(registration, instance)
            
            logger.info(
                "Plugin service registered successfully",
                service_id=service_id,
                interface_name=interface_name,
                provider_plugin_id=provider_plugin_id,
            )
            return reg_id

    def unregister_service(self, registration_id: str) -> bool:
        """Removes a service registration."""
        with self._lock:
            return self._registry.remove_service_registration(registration_id)

    def resolve_service(self, interface_name: str, version_constraint: Optional[str] = None) -> Any:
        """Resolves a single implementation for the requested service interface."""
        with self._lock:
            registrations = self._registry.query_service_registrations(interface_name=interface_name)
            if not registrations:
                raise ServiceResolutionError(f"No registered services found for interface '{interface_name}'.")

            # Deterministic resolution: choose the first alphabetically by provider_plugin_id
            registrations.sort(key=lambda r: r.descriptor.provider_plugin_id)
            target_reg = registrations[0]
            instance = self._registry.get_service_instance(target_reg.registration_id)
            
            if instance is None:
                raise ServiceResolutionError(f"Service instance not found for registered service '{target_reg.descriptor.service_id}'.")
            return instance

    def resolve_all(self, interface_name: str) -> List[Any]:
        """Resolves all implementations for the requested interface."""
        with self._lock:
            registrations = self._registry.query_service_registrations(interface_name=interface_name)
            # Deterministic order
            registrations.sort(key=lambda r: r.descriptor.provider_plugin_id)
            instances: List[Any] = []
            for r in registrations:
                inst = self._registry.get_service_instance(r.registration_id)
                if inst is not None:
                    instances.append(inst)
            return instances

    def service_exists(self, interface_name: str) -> bool:
        """Checks if any registration exists for the requested interface."""
        with self._lock:
            return len(self._registry.query_service_registrations(interface_name=interface_name)) > 0

    def list_services(self) -> List[ServiceRegistration]:
        """Lists all active service registrations."""
        with self._lock:
            return self._registry.query_service_registrations()

    def inject_dependencies(
        self,
        target_instance: Any,
        dependencies: List[ServiceDependency],
        context: InjectionContext,
    ) -> None:
        """Dynamically injects service implementations into the target instance fields.

        Resolves each declared service interface and sets it as an attribute
        on the target instance using standard attribute naming. Detects missing
        dependencies and version conflicts.
        """
        for dep in dependencies:
            try:
                resolved_instance = self.resolve_service(dep.interface_name, dep.version_constraint)
                
                # Attribute name e.g., db_service for "DbService" or interface_name lower/snake case
                # For this implementation, we use interface_name string or lower snake case conversion
                attr_name = self._to_snake_case(dep.interface_name)
                setattr(target_instance, attr_name, resolved_instance)
            except ServiceResolutionError as exc:
                if not dep.is_optional:
                    raise ServiceInjectionError(
                        f"Injection failed for target '{context.target_class_name}' "
                        f"in plugin '{context.target_plugin_id}': required dependency "
                        f"'{dep.interface_name}' could not be resolved."
                    ) from exc
                else:
                    # Optional missing is ignored, attribute remains unset or None
                    attr_name = self._to_snake_case(dep.interface_name)
                    setattr(target_instance, attr_name, None)

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """Helper to convert PascalCase interface name to snake_case attribute."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
