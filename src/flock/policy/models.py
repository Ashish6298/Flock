"""Immutable Pydantic data models for the Policy-as-Code engine."""

from __future__ import annotations

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class PolicyRule(BaseModel):
    """Represents a single policy validation rule."""
    name: str
    condition: str  # e.g., "resource.type == 'db' and resource.encryption == True"
    remediation_plan: str

    model_config = {
        "frozen": True
    }


class PolicyDefinition(BaseModel):
    """Represents a compiled Policy-as-Code document definition."""
    policy_id: str
    version: str
    target_selectors: Dict[str, str] = Field(default_factory=dict)  # labels filter
    rules: List[PolicyRule] = Field(default_factory=list)
    parent_policy_id: Optional[str] = None

    model_config = {
        "frozen": True
    }


class ComplianceFrameworkReport(BaseModel):
    """Compliance assessment result mapping framework profiles (SOC2, NIST, CIS)."""
    framework_name: str
    timestamp: float
    total_checks: int
    passed_checks: int
    failed_checks: int
    remediations: Dict[str, str] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class PolicyMetricsReport(BaseModel):
    """Aggregated policy telemetry metrics report."""
    timestamp: float
    total_policies_loaded: int
    total_evaluations: int
    failed_evaluations: int
    violations_detected: int

    model_config = {
        "frozen": True
    }
