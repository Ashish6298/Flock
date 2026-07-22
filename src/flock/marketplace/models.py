"""Immutable Pydantic data models for the marketplace package registry."""

from __future__ import annotations

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class PublisherInfo(BaseModel):
    """Represents the identity of an extension package author."""
    publisher_id: str
    name: str
    certificate_pem: str
    verified: bool

    model_config = {
        "frozen": True
    }


class PackageManifest(BaseModel):
    """Represents the metadata manifest describing an extension package."""
    package_id: str
    name: str
    publisher_id: str
    version: str  # Semantic version
    description: str
    dependencies: List[str] = Field(default_factory=list)  # e.g., ["core>=1.0.0", "service-mesh"]
    required_features: List[str] = Field(default_factory=list)
    license_key: Optional[str] = None
    signature: str

    model_config = {
        "frozen": True
    }


class PackageVersionInfo(BaseModel):
    """Details of a specific release version of an extension package."""
    version: str
    release_channel: str  # "stable", "beta", "nightly"
    released_at: float
    archive_checksum: str

    model_config = {
        "frozen": True
    }


class InstallationReceipt(BaseModel):
    """Represents a transaction record for a successfully installed package."""
    transaction_id: str
    package_id: str
    installed_version: str
    installed_at: float
    status: str  # "active", "degraded", "rolled_back"

    model_config = {
        "frozen": True
    }


class MarketplaceMetricsReport(BaseModel):
    """Aggregated statistics summarizing marketplace performance indices."""
    timestamp: float
    total_packages: int
    total_downloads: int
    failed_installations: int
    health_percentage: float

    model_config = {
        "frozen": True
    }
