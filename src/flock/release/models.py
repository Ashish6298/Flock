"""Immutable Pydantic data models for the release candidate integration control plane."""

from __future__ import annotations

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class ReleaseManifest(BaseModel):
    """Represents a compiled Release Candidate (RC) definition."""
    version: str  # e.g., "1.0.0-rc1"
    commit_sha: str
    built_at: float
    features_included: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class SubsystemStatus(BaseModel):
    """Detailed startup status info for a subsystem component."""
    name: str
    state: str  # "uninitialized", "starting", "running", "degraded", "stopped"
    errors: List[str] = Field(default_factory=list)

    model_config = {
        "frozen": True
    }


class ReadinessAssessmentReport(BaseModel):
    """Production readiness checklist score sheet."""
    timestamp: float
    manifest_version: str
    dependency_status: bool
    configuration_status: bool
    subsystems_healthy: bool
    overall_readiness_score: float  # Percentage score (e.g. 100.0)

    model_config = {
        "frozen": True
    }
