"""Dashboard Subsystem Models."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WidgetDefinition(BaseModel):
    """Represents a registered dashboard widget configuration."""

    widget_id: str
    widget_type: str  # 'chart', 'table', 'gauge', 'stat', 'log', 'map'
    title: str
    data_source: str
    refresh_interval_seconds: float = 5.0

    model_config = {"frozen": True}


class PanelDefinition(BaseModel):
    """Represents a dashboard panel containing multiple widgets."""

    panel_id: str
    panel_name: str
    widgets: List[str] = Field(default_factory=list)
    required_roles: List[str] = Field(default_factory=list)

    model_config = {"frozen": True}


class DashboardLayout(BaseModel):
    """Represents the full dashboard layout with ordered panels."""

    layout_id: str
    panels: List[str] = Field(default_factory=list)
    theme: str = "dark"

    model_config = {"frozen": True}


class MetricDataPoint(BaseModel):
    """Represents a single time-series metric data point."""

    timestamp: float
    metric_name: str
    value: float
    labels: Dict[str, str] = Field(default_factory=dict)

    model_config = {"frozen": True}


class ClusterOverview(BaseModel):
    """Represents an aggregated cluster health summary."""

    total_nodes: int
    healthy_nodes: int
    active_tasks: int
    cpu_utilization_pct: float
    memory_utilization_pct: float

    model_config = {"frozen": True}


class NodeStatus(BaseModel):
    """Represents a single node's reported health state."""

    node_id: str
    is_healthy: bool
    cpu_load: float
    memory_load: float
    task_count: int

    model_config = {"frozen": True}


class AlertDefinition(BaseModel):
    """Represents an alert rule with threshold and routing."""

    alert_id: str
    metric_name: str
    threshold: float
    severity: str  # 'info', 'warning', 'critical'
    recipients: List[str] = Field(default_factory=list)

    model_config = {"frozen": True}


class AlertEvent(BaseModel):
    """Represents a triggered alert notification."""

    alert_id: str
    triggered_at: float
    current_value: float
    message: str

    model_config = {"frozen": True}


class SessionToken(BaseModel):
    """Represents an authenticated dashboard session."""

    session_id: str
    username: str
    roles: List[str] = Field(default_factory=list)
    expires_at: float

    model_config = {"frozen": True}


class DashboardTheme(BaseModel):
    """Represents a UI colour and font theme definition."""

    theme_name: str
    primary_color: str
    background_color: str
    font_family: str

    model_config = {"frozen": True}


class ExportRequest(BaseModel):
    """Represents a request to export dashboard data."""

    panel_id: str
    format_type: str  # 'pdf', 'csv', 'json', 'png'
    time_range_seconds: float = 3600.0

    model_config = {"frozen": True}


class ExportResult(BaseModel):
    """Represents completed export output metadata."""

    panel_id: str
    format_type: str
    payload: bytes = Field(default_factory=bytes)
    success: bool = True

    model_config = {"frozen": True}


class DashboardMetrics(BaseModel):
    """Represents dashboard server operational metrics."""

    active_sessions: int
    connected_websockets: int
    panels_rendered: int

    model_config = {"frozen": True}


class DashboardStatistics(BaseModel):
    """Represents aggregated dashboard usage statistics."""

    total_page_views: int
    average_render_ms: float

    model_config = {"frozen": True}


class WebSocketMessage(BaseModel):
    """Represents a real-time update message sent over WebSocket."""

    channel: str
    payload: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}


class DataSourceResult(BaseModel):
    """Represents data returned by a metric data source query."""

    source_name: str
    data_points: List[MetricDataPoint] = Field(default_factory=list)
    success: bool = True
    error: Optional[str] = None

    model_config = {"frozen": True}
