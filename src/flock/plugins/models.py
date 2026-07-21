"""Plugin Subsystem Models."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class PluginManifest(BaseModel):
    """Represents a plugin metadata manifest descriptor."""
    plugin_id: str
    name: str
    version: str
    author: str
    dependencies: List[str] = Field(default_factory=list)

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

    model_config = {
        "frozen": True
    }
