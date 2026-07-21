"""Service Mesh Registry tracking live endpoints."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from flock.mesh.exceptions import ServiceNotFoundError
from flock.mesh.models import MeshService, ServiceEndpoint


class ServiceRegistry:
    """Thread-safe catalog indexing mesh services."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # service_id -> MeshService
        self._services: Dict[str, MeshService] = {}

    def register_service(self, service: MeshService) -> None:
        """Register or override a service profile configuration."""
        with self._lock:
            self._services[service.service_id] = service

    def unregister_service(self, service_id: str) -> None:
        """Unregister a service profile configuration."""
        with self._lock:
            self._services.pop(service_id, None)

    def get_service(self, service_id: str) -> Optional[MeshService]:
        """Fetch service configuration.

        Raises:
            ServiceNotFoundError: If service ID is missing.
        """
        with self._lock:
            service = self._services.get(service_id)
            if not service:
                raise ServiceNotFoundError(f"Mesh service '{service_id}' is not registered.")
            return service

    def list_services(self) -> List[MeshService]:
        """List all active services profiles."""
        with self._lock:
            return list(self._services.values())
