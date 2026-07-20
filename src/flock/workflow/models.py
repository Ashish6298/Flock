"""Workflow Models."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class WorkflowNode(BaseModel):
    """Represents a single step or task task node in a workflow DAG."""
    node_id: str
    task_payload: bytes
    retries_left: int = 3

    model_config = {
        "frozen": True
    }


class WorkflowEdge(BaseModel):
    """Represents a dependency connection between two workflow tasks."""
    source_id: str
    target_id: str

    model_config = {
        "frozen": True
    }


class WorkflowDefinition(BaseModel):
    """Represents the blueprint of a task DAG workflow."""
    workflow_id: str
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]

    model_config = {
        "frozen": True
    }


class WorkflowCheckpoint(BaseModel):
    """Represents the persisted snapshot checkpoint for a running workflow."""
    instance_id: str
    completed_nodes: List[str] = Field(default_factory=list)
    pending_nodes: List[str] = Field(default_factory=list)
    variables: Dict[str, str] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class WorkflowResult(BaseModel):
    """Represents the final execution outcome of a workflow."""
    instance_id: str
    success: bool
    errors: Dict[str, str] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }
