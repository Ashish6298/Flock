"""Dashboard subsystem exceptions."""


class DashboardError(Exception):
    """Base exception for all dashboard subsystem errors."""


class DashboardStartupError(DashboardError):
    """Raised when the dashboard server fails to start."""


class DashboardShutdownError(DashboardError):
    """Raised when the dashboard server fails to stop cleanly."""


class WidgetNotFoundError(DashboardError):
    """Raised when a requested dashboard widget cannot be located."""


class PanelNotFoundError(DashboardError):
    """Raised when a requested dashboard panel cannot be located."""


class DataSourceError(DashboardError):
    """Raised when a data source fails to return metrics."""


class AlertRuleError(DashboardError):
    """Raised when an alert rule configuration is invalid."""


class ThemeNotFoundError(DashboardError):
    """Raised when a requested UI theme does not exist."""


class SessionExpiredError(DashboardError):
    """Raised when a dashboard session token has expired."""


class PermissionDeniedError(DashboardError):
    """Raised when a user lacks permission to view a panel."""


class RenderError(DashboardError):
    """Raised when a widget or chart fails to render."""


class ExportError(DashboardError):
    """Raised when a dashboard export operation fails."""


class WebSocketError(DashboardError):
    """Raised when a real-time WebSocket connection encounters an error."""
