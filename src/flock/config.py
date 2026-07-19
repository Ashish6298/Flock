"""Centralized configuration management for Flock using Pydantic."""

from typing import Dict, Any
from pydantic import BaseModel, Field

class TransportConfig(BaseModel):
    """Configuration options for network transport."""
    host: str = Field(default="127.0.0.1", description="Binding interface/IP address")
    port: int = Field(default=8000, description="Port to listen for incoming connections")
    max_connections: int = Field(default=1024, description="Maximum concurrent active connections")

class DiscoveryConfig(BaseModel):
    """Configuration options for the discovery service."""
    enabled: bool = Field(default=True, description="Enable automatic peer discovery")
    interval_seconds: float = Field(default=5.0, description="Interval between discovery/heartbeat checks")
    multicast_group: str = Field(default="224.0.0.1", description="Multicast IP for peer discoverability")

class ClusterConfig(BaseModel):
    """Overall configuration cluster options."""
    node_id: str = Field(..., description="Unique identifier for this cluster node")
    transport: TransportConfig = Field(default_factory=TransportConfig)
    discovery: DiscoveryConfig = Field(default_factory=DiscoveryConfig)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom node metadata")
