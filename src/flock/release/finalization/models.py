"""Immutable Pydantic data models for the General Availability (GA) stabilization plane."""

from __future__ import annotations

from typing import Dict, List, Any
from pydantic import BaseModel, Field


class SBOMReport(BaseModel):
    """Software Bill of Materials (SBOM) details indexing system libraries and licenses."""
    release_version: str
    timestamp: float
    dependencies: List[Dict[str, str]] = Field(default_factory=list)  # list of package name + version + license
    hashes: Dict[str, str] = Field(default_factory=dict)  # file checksums mapping

    model_config = {
        "frozen": True
    }


class ReleaseCertification(BaseModel):
    """Official release certificate validation records."""
    release_version: str
    certified_at: float
    sbom_verified: bool
    api_compatible: bool
    license_clean: bool
    compliance_score: float

    model_config = {
        "frozen": True
    }


class BenchmarkSummary(BaseModel):
    """Performance benchmarks records compiled for the GA release notes."""
    total_tx_processed: int
    avg_latency_ms: float
    raft_consensus_status: str

    model_config = {
        "frozen": True
    }
