"""Pydantic v2 Models for Plugin Dependency Management.

Defines schemas for constraints, specs, graphs, results, and installation plans.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class VersionOperator(str, Enum):
    """Supported version comparison operators."""

    EQ = "=="
    NE = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    TILDE_ARROW = "~>"


class DependencyConstraint(BaseModel):
    """Represents a single version constraint for a dependency."""

    operator: VersionOperator = Field(..., description="The comparison operator.")
    version: str = Field(..., description="The target version string to compare against.")

    model_config = {
        "frozen": True
    }


class DependencySpec(BaseModel):
    """Parsed dependency spec detailing requirements and constraints."""

    plugin_id: str = Field(..., description="The identifier of the required plugin.")
    is_optional: bool = Field(default=False, description="Whether this dependency is optional.")
    constraints: List[DependencyConstraint] = Field(
        default_factory=list, description="List of version constraints that must be satisfied."
    )

    model_config = {
        "frozen": True
    }


class DependencyResolutionResult(BaseModel):
    """The result of running the dependency resolver."""

    success: bool = Field(..., description="True if resolution succeeded completely.")
    resolved_order: List[str] = Field(
        default_factory=list, description="Deterministic load order of plugin IDs."
    )
    missing_dependencies: List[str] = Field(
        default_factory=list, description="Required plugin IDs that were missing."
    )
    version_conflicts: Dict[str, str] = Field(
        default_factory=dict, description="Plugin IDs that failed validation mapped to violation detail."
    )
    unresolved_optional: List[str] = Field(
        default_factory=list, description="Optional dependencies that were missing and ignored."
    )

    model_config = {
        "frozen": True
    }


class PlanStepType(str, Enum):
    """Type of installation step."""

    REGISTER = "REGISTER"
    VALIDATE = "VALIDATE"
    ACTIVATE = "ACTIVATE"


class InstallationStep(BaseModel):
    """A single step in a dependency installation plan."""

    step_type: PlanStepType = Field(..., description="The type of action to perform.")
    plugin_id: str = Field(..., description="The plugin ID target of the step.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata parameters for the step.")

    model_config = {
        "frozen": True
    }


class DependencyInstallationPlan(BaseModel):
    """Structured, reproducible plan for validating and activating plugins."""

    steps: List[InstallationStep] = Field(
        default_factory=list, description="Ordered steps to install dependencies."
    )

    model_config = {
        "frozen": True
    }
