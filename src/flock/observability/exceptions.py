"""Observability exceptions."""

from flock.exceptions import FlockError

class TelemetryError(FlockError):
    """Base exception for all telemetry operations."""
    pass

class ExporterError(TelemetryError):
    """Raised when structured telemetry export fails."""
    pass

class InvalidMetricError(TelemetryError):
    """Raised when registering or fetching a metric with mismatched parameters."""
    pass

class AggregationError(TelemetryError):
    """Raised when metrics calculations or summaries fail."""
    pass
