"""Dashboard HTTP API Handler.

Provides a clean interface that the HTTP server layer (e.g. aiohttp,
FastAPI, or a custom handler) can call to service dashboard REST
requests.  Every method is synchronous and transport-independent;
callers are responsible for JSON serialisation and response routing.
"""

from __future__ import annotations

from typing import Any, Dict, List

from flock.dashboard.alerts import AlertEngine
from flock.dashboard.datasources import DataSourceManager
from flock.dashboard.exporter import ExportEngine
from flock.dashboard.models import (
    ClusterOverview,
    ExportRequest,
    ExportResult,
    NodeStatus,
    SessionToken,
)
from flock.dashboard.panels import PanelRegistry
from flock.dashboard.renderer import DashboardRenderer
from flock.dashboard.sessions import SessionManager
from flock.dashboard.themes import ThemeManager
from flock.dashboard.widgets import WidgetRegistry


class DashboardApiHandler:
    """Facade exposing all dashboard REST operations.

    Every method returns a plain dict or Pydantic model instance that
    the HTTP layer serialises.  No framework-specific objects are
    imported here; this keeps the handler fully testable without a
    running HTTP server.

    Attributes:
        _widgets: Widget definition registry.
        _panels: Panel definition registry.
        _datasources: Data source manager.
        _renderer: Widget payload renderer.
        _alerts: Alert rule evaluator.
        _sessions: Session manager.
        _themes: Theme registry.
        _exporter: Export engine.
    """

    def __init__(
        self,
        widgets: WidgetRegistry,
        panels: PanelRegistry,
        datasources: DataSourceManager,
        renderer: DashboardRenderer,
        alerts: AlertEngine,
        sessions: SessionManager,
        themes: ThemeManager,
        exporter: ExportEngine,
    ) -> None:
        """Initialise the API handler with all required dependencies."""
        self._widgets = widgets
        self._panels = panels
        self._datasources = datasources
        self._renderer = renderer
        self._alerts = alerts
        self._sessions = sessions
        self._themes = themes
        self._exporter = exporter

    # ------------------------------------------------------------------
    # Overview
    # ------------------------------------------------------------------

    def get_cluster_overview(self) -> Dict[str, Any]:
        """Return a synthetic cluster health overview.

        In production this delegates to the Observability and Resource
        Manager subsystems; here it aggregates data from registered
        sources with the names ``node_count``, ``healthy_nodes``,
        ``active_tasks``, ``cpu_pct``, and ``memory_pct``.

        Returns:
            Serialisable dict representing a :class:`ClusterOverview`.
        """
        def _val(name: str) -> float:
            res = self._datasources.query_safe(name)
            if res.data_points:
                return res.data_points[-1].value
            return 0.0

        overview = ClusterOverview(
            total_nodes=int(_val("node_count")),
            healthy_nodes=int(_val("healthy_nodes")),
            active_tasks=int(_val("active_tasks")),
            cpu_utilization_pct=_val("cpu_pct"),
            memory_utilization_pct=_val("memory_pct"),
        )
        return overview.model_dump()

    def list_nodes(self) -> List[Dict[str, Any]]:
        """Return a list of node status summaries.

        Returns:
            List of serialisable dicts representing :class:`NodeStatus`.
        """
        res = self._datasources.query_safe("nodes")
        statuses: List[Dict[str, Any]] = []
        for point in res.data_points:
            status = NodeStatus(
                node_id=point.metric_name,
                is_healthy=point.value > 0,
                cpu_load=point.value,
                memory_load=point.value * 0.8,
                task_count=int(point.value * 10),
            )
            statuses.append(status.model_dump())
        return statuses

    # ------------------------------------------------------------------
    # Widgets
    # ------------------------------------------------------------------

    def list_widgets(self) -> List[Dict[str, Any]]:
        """Return all registered widget definitions."""
        return [w.model_dump() for w in self._widgets.list_all()]

    def render_widget(self, widget_id: str) -> Dict[str, Any]:
        """Render a widget using its registered data source.

        Args:
            widget_id: Identifier of the widget to render.

        Returns:
            Rendered widget payload dict.
        """
        widget = self._widgets.get(widget_id)
        result = self._datasources.query_safe(widget.data_source)
        return self._renderer.render(widget, result)

    # ------------------------------------------------------------------
    # Panels
    # ------------------------------------------------------------------

    def list_panels(self, user_roles: List[str]) -> List[Dict[str, Any]]:
        """Return all panels accessible to the given roles.

        Args:
            user_roles: Roles of the requesting user.

        Returns:
            List of accessible :class:`PanelDefinition` dicts.
        """
        return [
            p.model_dump()
            for p in self._panels.find_accessible(user_roles)
        ]

    def render_panel(
        self, panel_id: str, user_roles: List[str]
    ) -> List[Dict[str, Any]]:
        """Render all widgets in a panel after access-control check.

        Args:
            panel_id: Panel to render.
            user_roles: Roles of the requesting user.

        Returns:
            List of rendered widget payloads.
        """
        self._panels.check_access(panel_id, user_roles)
        panel = self._panels.get(panel_id)
        payloads: List[Dict[str, Any]] = []
        for wid in panel.widgets:
            if self._widgets.exists(wid):
                payloads.append(self.render_widget(wid))
        return payloads

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------

    def list_alert_rules(self) -> List[Dict[str, Any]]:
        """Return all registered alert rule definitions."""
        return [r.model_dump() for r in self._alerts.list_rules()]

    def get_triggered_alerts(self) -> List[Dict[str, Any]]:
        """Return all alert events fired in this session."""
        return [e.model_dump() for e in self._alerts.get_triggered_events()]

    # ------------------------------------------------------------------
    # Themes
    # ------------------------------------------------------------------

    def list_themes(self) -> List[Dict[str, Any]]:
        """Return all registered UI themes."""
        return [t.model_dump() for t in self._themes.list_all()]

    def get_active_theme(self) -> Dict[str, Any]:
        """Return the currently active UI theme."""
        return self._themes.get_active().model_dump()

    def set_theme(self, theme_name: str) -> Dict[str, Any]:
        """Set the active theme by name and return the new theme.

        Args:
            theme_name: Name of the theme to activate.

        Returns:
            The newly active theme dict.
        """
        self._themes.set_active(theme_name)
        return self._themes.get_active().model_dump()

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def create_session(
        self, username: str, roles: List[str]
    ) -> Dict[str, Any]:
        """Create a new dashboard session.

        Args:
            username: Authenticated user identity.
            roles: Roles granted to the session.

        Returns:
            Serialisable :class:`SessionToken` dict.
        """
        token: SessionToken = self._sessions.create_session(username, roles)
        return token.model_dump()

    def validate_session(self, session_id: str) -> Dict[str, Any]:
        """Validate and return an active session token.

        Args:
            session_id: Session identifier to validate.

        Returns:
            Serialisable :class:`SessionToken` dict.
        """
        return self._sessions.validate(session_id).model_dump()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_panel(
        self, panel_id: str, format_type: str
    ) -> ExportResult:
        """Export a panel to the requested format.

        Args:
            panel_id: Panel to export.
            format_type: One of ``json``, ``csv``, ``pdf``, ``png``.

        Returns:
            The :class:`ExportResult` containing the payload bytes.
        """
        req = ExportRequest(panel_id=panel_id, format_type=format_type)
        result = self._datasources.query_safe(panel_id)
        return self._exporter.export(req, result)
