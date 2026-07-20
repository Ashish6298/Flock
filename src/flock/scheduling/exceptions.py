"""Scheduling Exceptions."""

from flock.exceptions import FlockError

class SchedulingError(FlockError):
    """Base exception for all scheduling operations."""
    pass

class InvalidCronExpressionError(SchedulingError):
    """Raised when cron expression parsing fails."""
    pass

class ScheduleConflictError(SchedulingError):
    """Raised when schedule parameters overlap or conflict."""
    pass

class ScheduleExecutionError(SchedulingError):
    """Raised when a scheduled task execution fails."""
    pass

class TriggerValidationError(SchedulingError):
    """Raised when event trigger properties are invalid."""
    pass

class DuplicateScheduleError(SchedulingError):
    """Raised when schedule ID already exists in registry."""
    pass

class SchedulerRecoveryError(SchedulingError):
    """Raised when loading snapshot states fails."""
    pass
