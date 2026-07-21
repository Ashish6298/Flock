"""Observability exceptions."""

from flock.exceptions import FlockError


class TelemetryError(FlockError):
    """Base exception for all telemetry operations."""


class ExporterError(TelemetryError):
    """Raised when structured telemetry export fails."""


class InvalidMetricError(TelemetryError):
    """Raised when registering or fetching a metric with mismatched parameters."""


class AggregationError(TelemetryError):
    """Raised when metrics calculations or summaries fail."""


class LoggingError(TelemetryError):
    """Raised when structured log recording or retrieval fails."""


class CollectorError(TelemetryError):
    """Raised when a telemetry collector fails to gather data."""


class RetentionError(TelemetryError):
    """Raised when retention policy execution encounters an error."""


class SamplingError(TelemetryError):
    """Raised when a sampling strategy cannot be applied."""


class AlertError(TelemetryError):
    """Base exception for alert management operations."""


class AlertRuleNotFoundError(AlertError):
    """Raised when an alert rule identifier cannot be found."""


class ProfilingError(TelemetryError):
    """Raised when a profiling snapshot operation fails."""


class HealthCheckError(TelemetryError):
    """Raised when a health-check evaluation encounters a fatal error."""


class DashboardAdapterError(TelemetryError):
    """Raised when the dashboard telemetry adapter fails to push data."""

