"""Observability models."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MetricType(str, Enum):
    """Supported metric registration categories."""
    COUNTER = "COUNTER"
    GAUGE = "GAUGE"
    HISTOGRAM = "HISTOGRAM"
    SUMMARY = "SUMMARY"
    TIMER = "TIMER"


class MetricValue(BaseModel):
    """Represents a measured telemetry metric data point."""
    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = Field(default_factory=dict)
    timestamp: float

    model_config = {
        "frozen": True
    }


class Span(BaseModel):
    """Represents a single trace execution timeline span (Tracing/APM)."""
    span_id: str
    parent_span_id: Optional[str] = None
    trace_id: str
    name: str
    start_time: float
    end_time: Optional[float] = None
    annotations: Dict[str, str] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class NodeHealthReport(BaseModel):
    """Self-monitoring liveness report mapping for local nodes."""
    node_id: str
    status: str  # "HEALTHY", "DEGRADED", "UNHEALTHY"
    metrics: Dict[str, float]
    timestamp: float

    model_config = {
        "frozen": True
    }


class ClusterHealthReport(BaseModel):
    """Combined report of node statuses across the active cluster."""
    status: str
    node_reports: Dict[str, NodeHealthReport]
    timestamp: float

    model_config = {
        "frozen": True
    }
