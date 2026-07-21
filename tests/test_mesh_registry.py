"""Unit tests for ServiceRegistry."""

import pytest
from flock.mesh.exceptions import ServiceNotFoundError
from flock.mesh.models import MeshService, ServiceEndpoint
from flock.mesh.registry import ServiceRegistry


def test_registry_add_and_list() -> None:
    registry = ServiceRegistry()
    service = MeshService(
        service_id="service-1",
        name="auth-service",
        endpoints=[
            ServiceEndpoint(endpoint_id="ep-1", host="127.0.0.1", port=8080),
        ],
    )

    registry.register_service(service)
    assert registry.get_service("service-1") == service
    assert len(registry.list_services()) == 1

    registry.unregister_service("service-1")
    with pytest.raises(ServiceNotFoundError):
        registry.get_service("service-1")
