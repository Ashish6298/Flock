"""Flock Dashboard Subsystem.

Phase 33 – Enterprise Web Dashboard & Distributed Cluster Management UI.

Public API
----------
:class:`DashboardService`
    Top-level lifecycle orchestrator.  Instantiate this class to get
    a fully wired dashboard subsystem.

:class:`WidgetRegistry`
    Register and retrieve :class:`WidgetDefinition` instances.

:class:`PanelRegistry`
    Register and retrieve :class:`PanelDefinition` instances.

:class:`DataSourceManager`
    Register named metric-source callables and query them safely.

:class:`DashboardRenderer`
    Convert :class:`DataSourceResult` payloads to widget render dicts.

:class:`AlertEngine`
    Evaluate :class:`MetricDataPoint` values against alert rules.

:class:`SessionManager`
    Create and validate authenticated dashboard sessions.

:class:`ThemeManager`
    Manage and switch between dashboard UI themes.

:class:`ExportEngine`
    Export panel data to JSON, CSV, PDF, or PNG formats.

:class:`WebSocketBroadcaster`
    Fan-out :class:`WebSocketMessage` payloads to channel subscribers.

:class:`DashboardApiHandler`
    Transport-independent REST facade wiring all subsystems together.

Models
------
All request/response Pydantic models are importable from
:mod:`flock.dashboard.models`.

Exceptions
----------
All subsystem exceptions are importable from
:mod:`flock.dashboard.exceptions`.
"""

from flock.dashboard.alerts import AlertEngine
from flock.dashboard.datasources import DataSourceManager
from flock.dashboard.exceptions import (
    AlertRuleError,
    DashboardError,
    DashboardShutdownError,
    DashboardStartupError,
    DataSourceError,
    ExportError,
    PanelNotFoundError,
    PermissionDeniedError,
    RenderError,
    SessionExpiredError,
    ThemeNotFoundError,
    WebSocketError,
    WidgetNotFoundError,
)
from flock.dashboard.exporter import ExportEngine
from flock.dashboard.handlers import DashboardApiHandler
from flock.dashboard.models import (
    AlertDefinition,
    AlertEvent,
    ClusterOverview,
    DashboardLayout,
    DashboardMetrics,
    DashboardStatistics,
    DashboardTheme,
    DataSourceResult,
    ExportRequest,
    ExportResult,
    MetricDataPoint,
    NodeStatus,
    PanelDefinition,
    SessionToken,
    WebSocketMessage,
    WidgetDefinition,
)
from flock.dashboard.panels import PanelRegistry
from flock.dashboard.renderer import DashboardRenderer
from flock.dashboard.service import DashboardService
from flock.dashboard.sessions import SessionManager
from flock.dashboard.themes import ThemeManager
from flock.dashboard.websocket import WebSocketBroadcaster
from flock.dashboard.widgets import WidgetRegistry

__all__ = [
    # Service
    "DashboardService",
    # Registries & Managers
    "WidgetRegistry",
    "PanelRegistry",
    "DataSourceManager",
    "SessionManager",
    "ThemeManager",
    # Engines
    "DashboardRenderer",
    "AlertEngine",
    "ExportEngine",
    "WebSocketBroadcaster",
    # Facade
    "DashboardApiHandler",
    # Models
    "WidgetDefinition",
    "PanelDefinition",
    "DashboardLayout",
    "MetricDataPoint",
    "ClusterOverview",
    "NodeStatus",
    "AlertDefinition",
    "AlertEvent",
    "SessionToken",
    "DashboardTheme",
    "ExportRequest",
    "ExportResult",
    "DashboardMetrics",
    "DashboardStatistics",
    "WebSocketMessage",
    "DataSourceResult",
    # Exceptions
    "DashboardError",
    "DashboardStartupError",
    "DashboardShutdownError",
    "WidgetNotFoundError",
    "PanelNotFoundError",
    "DataSourceError",
    "AlertRuleError",
    "ThemeNotFoundError",
    "SessionExpiredError",
    "PermissionDeniedError",
    "RenderError",
    "ExportError",
    "WebSocketError",
]
