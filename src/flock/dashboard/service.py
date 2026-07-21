"""Dashboard Service.

Provides the top-level lifecycle orchestrator for the Flock Enterprise
Web Dashboard.  The service wires together all dashboard subsystems
(widgets, panels, data sources, renderer, alerts, sessions, themes,
exporter, WebSocket broadcaster, and the API handler) and exposes a
unified start/stop interface aligned with the Flock service contract
used across all phases.
"""

from __future__ import annotations

import threading
from typing import List, Optional

from flock.dashboard.alerts import AlertEngine
from flock.dashboard.datasources import DataSourceManager
from flock.dashboard.exceptions import DashboardStartupError, DashboardShutdownError
from flock.dashboard.exporter import ExportEngine
from flock.dashboard.handlers import DashboardApiHandler
from flock.dashboard.models import (
    AlertDefinition,
    DashboardLayout,
    DashboardMetrics,
    DashboardStatistics,
    PanelDefinition,
    WidgetDefinition,
)
from flock.dashboard.panels import PanelRegistry
from flock.dashboard.renderer import DashboardRenderer
from flock.dashboard.sessions import SessionManager
from flock.dashboard.themes import ThemeManager
from flock.dashboard.websocket import WebSocketBroadcaster
from flock.dashboard.widgets import WidgetRegistry


class DashboardService:
    """Top-level dashboard service for the Flock platform.

    Wires together every dashboard subsystem and exposes a minimal
    lifecycle interface (``start`` / ``stop``) compatible with the
    rest of the Flock service layer.  All state is kept in-process;
    external persistence (e.g. writing layout to the DataGrid) can be
    layered on top.

    Attributes:
        _lock: Reentrant lock protecting service-level state.
        _running: Whether the service is currently active.
        _page_views: Cumulative page-view counter.
        _render_times: List of recent widget render latencies in ms.
        widget_registry: Registered widget definitions.
        panel_registry: Registered panel definitions.
        datasources: Metric data source manager.
        renderer: Widget payload renderer.
        alerts: Alert rule evaluator.
        sessions: Session manager.
        themes: Theme registry.
        exporter: Export engine.
        broadcaster: WebSocket channel broadcaster.
        api: High-level REST API facade.
        layout: Active dashboard layout.
    """

    def __init__(self, ttl_seconds: float = 3600.0) -> None:
        """Initialise the dashboard service.

        Args:
            ttl_seconds: Default session TTL forwarded to the
                :class:`SessionManager`.
        """
        self._lock: threading.RLock = threading.RLock()
        self._running: bool = False
        self._page_views: int = 0
        self._render_times: List[float] = []

        # Core subsystems.
        self.widget_registry: WidgetRegistry = WidgetRegistry()
        self.panel_registry: PanelRegistry = PanelRegistry()
        self.datasources: DataSourceManager = DataSourceManager()
        self.renderer: DashboardRenderer = DashboardRenderer()
        self.alerts: AlertEngine = AlertEngine()
        self.sessions: SessionManager = SessionManager(ttl_seconds)
        self.themes: ThemeManager = ThemeManager()
        self.exporter: ExportEngine = ExportEngine()
        self.broadcaster: WebSocketBroadcaster = WebSocketBroadcaster()

        # Facade.
        self.api: DashboardApiHandler = DashboardApiHandler(
            widgets=self.widget_registry,
            panels=self.panel_registry,
            datasources=self.datasources,
            renderer=self.renderer,
            alerts=self.alerts,
            sessions=self.sessions,
            themes=self.themes,
            exporter=self.exporter,
        )

        # Active layout.
        self.layout: DashboardLayout = DashboardLayout(
            layout_id="default",
            panels=[],
            theme="dark",
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the dashboard service.

        Seeds built-in synthetic data sources for the overview panel
        and marks the service as running.

        Raises:
            DashboardStartupError: If the service is already running.
        """
        with self._lock:
            if self._running:
                raise DashboardStartupError(
                    "DashboardService is already running."
                )
            self._seed_default_sources()
            self._running = True

    def stop(self) -> None:
        """Stop the dashboard service cleanly.

        Purges expired sessions and marks the service as stopped.

        Raises:
            DashboardShutdownError: If the service is not running.
        """
        with self._lock:
            if not self._running:
                raise DashboardShutdownError(
                    "DashboardService is not running."
                )
            self.sessions.purge_expired()
            self.broadcaster.clear()
            self._running = False

    @property
    def is_running(self) -> bool:
        """Return ``True`` if the service is active."""
        with self._lock:
            return self._running

    # ------------------------------------------------------------------
    # Widget / Panel management helpers
    # ------------------------------------------------------------------

    def register_widget(self, widget: WidgetDefinition) -> None:
        """Register a widget with the service.

        Args:
            widget: The :class:`WidgetDefinition` to register.
        """
        self.widget_registry.register(widget)

    def register_panel(self, panel: PanelDefinition) -> None:
        """Register a panel with the service.

        Args:
            panel: The :class:`PanelDefinition` to register.
        """
        self.panel_registry.register(panel)
        with self._lock:
            existing = list(self.layout.panels)
            if panel.panel_id not in existing:
                self.layout = DashboardLayout(
                    layout_id=self.layout.layout_id,
                    panels=existing + [panel.panel_id],
                    theme=self.layout.theme,
                )

    def register_alert(self, rule: AlertDefinition) -> None:
        """Register an alert rule with the alert engine.

        Args:
            rule: The :class:`AlertDefinition` to register.
        """
        self.alerts.add_rule(rule)

    # ------------------------------------------------------------------
    # Metrics & statistics
    # ------------------------------------------------------------------

    def record_page_view(self) -> None:
        """Increment the cumulative page-view counter."""
        with self._lock:
            self._page_views += 1

    def record_render_time(self, latency_ms: float) -> None:
        """Record a widget render latency measurement.

        Args:
            latency_ms: Render duration in milliseconds.
        """
        with self._lock:
            self._render_times.append(latency_ms)
            if len(self._render_times) > 1000:
                self._render_times = self._render_times[-1000:]

    def get_metrics(self) -> DashboardMetrics:
        """Return current operational metrics.

        Returns:
            A :class:`DashboardMetrics` snapshot.
        """
        return DashboardMetrics(
            active_sessions=self.sessions.count_active(),
            connected_websockets=self.broadcaster.total_subscribers(),
            panels_rendered=self.panel_registry.count(),
        )

    def get_statistics(self) -> DashboardStatistics:
        """Return aggregated usage statistics.

        Returns:
            A :class:`DashboardStatistics` snapshot.
        """
        with self._lock:
            page_views = self._page_views
            times = list(self._render_times)

        avg = sum(times) / len(times) if times else 0.0
        return DashboardStatistics(
            total_page_views=page_views,
            average_render_ms=avg,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _seed_default_sources(self) -> None:
        """Register synthetic data sources for the overview panel."""
        self.datasources.make_constant_source("node_count", 8.0)
        self.datasources.make_constant_source("healthy_nodes", 7.0)
        self.datasources.make_constant_source("active_tasks", 42.0)
        self.datasources.make_constant_source("cpu_pct", 62.5)
        self.datasources.make_constant_source("memory_pct", 48.3)
        self.datasources.make_constant_source("nodes", 0.0)
