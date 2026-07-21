"""Service Mesh Models."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ServiceEndpoint(BaseModel):
    """Represents an active server endpoint coordinate."""
    endpoint_id: str
    host: str
    port: int
    weight: int = 1
    is_healthy: bool = True

    model_config = {
        "frozen": True
    }


class MeshService(BaseModel):
    """Represents registered services inside the mesh."""
    service_id: str
    name: str
    endpoints: List[ServiceEndpoint] = Field(default_factory=list)

    model_config = {
        "frozen": True
    }


class VirtualService(BaseModel):
    """Represents logical route path rules mapping."""
    name: str
    target_routes: Dict[str, str] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class CircuitBreaker(BaseModel):
    """Represents failure boundary configs."""
    service_id: str
    max_failures: int = 3
    cooldown: float = 5.0

    model_config = {
        "frozen": True
    }


class ConnectionSession(BaseModel):
    """Represents established session metadata."""
    session_id: str
    host_source: str
    target_host: str

    model_config = {
        "frozen": True
    }
