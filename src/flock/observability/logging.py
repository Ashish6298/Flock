"""Structured Logging Engine – Phase 34.

Provides severity-levelled, structured JSON log records with
correlation identifiers, component metadata, batch buffering,
retention-bounded storage, and paginated search.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from collections import deque
from enum import Enum
from typing import Any, Deque, Dict, List, Optional

from flock.observability.exceptions import LoggingError


class LogLevel(str, Enum):
    """Supported structured log severity levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogRecord:
    """Immutable structured log record.

    Attributes:
        record_id: Unique identifier.
        timestamp: Unix epoch seconds.
        level: Severity level.
        component: Source subsystem name.
        message: Human-readable message.
        correlation_id: Optional trace/request correlation identifier.
        fields: Arbitrary structured key-value context.
    """

    __slots__ = (
        "record_id",
        "timestamp",
        "level",
        "component",
        "message",
        "correlation_id",
        "fields",
    )

    def __init__(
        self,
        level: LogLevel,
        component: str,
        message: str,
        correlation_id: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        record_id: Optional[str] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        """Initialise a log record.

        Args:
            level: Severity level.
            component: Name of the originating subsystem.
            message: Human-readable description.
            correlation_id: Optional trace or request ID.
            fields: Additional structured context.
            record_id: Override record ID (auto-generated if omitted).
            timestamp: Override timestamp (current time if omitted).
        """
        self.record_id: str = record_id or str(uuid.uuid4())
        self.timestamp: float = timestamp if timestamp is not None else time.time()
        self.level: LogLevel = level
        self.component: str = component
        self.message: str = message
        self.correlation_id: Optional[str] = correlation_id
        self.fields: Dict[str, Any] = fields or {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the record to a plain dict."""
        return {
            "record_id": self.record_id,
            "timestamp": self.timestamp,
            "level": self.level.value,
            "component": self.component,
            "message": self.message,
            "correlation_id": self.correlation_id,
            "fields": self.fields,
        }

    def to_json(self) -> str:
        """Serialise the record to a JSON string."""
        return json.dumps(self.to_dict())


class StructuredLogger:
    """Thread-safe structured logging engine with retention and search.

    Log records are stored in an in-process ring buffer bounded by
    ``max_records``.  Records can be filtered by level, component, and
    correlation identifier, and retrieved in paginated slices.

    Attributes:
        _lock: Protects the record buffer.
        _records: Bounded deque of :class:`LogRecord` instances.
        _max_records: Buffer capacity.
        _min_level: Minimum level accepted for recording.
    """

    _LEVEL_ORDER: Dict[LogLevel, int] = {
        LogLevel.DEBUG: 0,
        LogLevel.INFO: 1,
        LogLevel.WARNING: 2,
        LogLevel.ERROR: 3,
        LogLevel.CRITICAL: 4,
    }

    def __init__(
        self,
        max_records: int = 10_000,
        min_level: LogLevel = LogLevel.DEBUG,
    ) -> None:
        """Initialise the structured logger.

        Args:
            max_records: Maximum records to retain in-memory.
            min_level: Minimum severity level to record.
        """
        self._lock: threading.RLock = threading.RLock()
        self._records: Deque[LogRecord] = deque(maxlen=max_records)
        self._max_records: int = max_records
        self._min_level: LogLevel = min_level

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def _should_record(self, level: LogLevel) -> bool:
        return self._LEVEL_ORDER[level] >= self._LEVEL_ORDER[self._min_level]

    def record(
        self,
        level: LogLevel,
        component: str,
        message: str,
        correlation_id: Optional[str] = None,
        **fields: Any,
    ) -> Optional[LogRecord]:
        """Record a structured log entry.

        Args:
            level: Severity level.
            component: Originating subsystem name.
            message: Human-readable description.
            correlation_id: Optional request/trace identifier.
            **fields: Additional structured key-value context.

        Returns:
            The created :class:`LogRecord`, or ``None`` if filtered.
        """
        if not self._should_record(level):
            return None
        log = LogRecord(
            level=level,
            component=component,
            message=message,
            correlation_id=correlation_id,
            fields=dict(fields),
        )
        with self._lock:
            self._records.append(log)
        return log

    def debug(self, component: str, message: str, **fields: Any) -> Optional[LogRecord]:
        """Record a DEBUG level entry."""
        return self.record(LogLevel.DEBUG, component, message, **fields)

    def info(self, component: str, message: str, **fields: Any) -> Optional[LogRecord]:
        """Record an INFO level entry."""
        return self.record(LogLevel.INFO, component, message, **fields)

    def warning(self, component: str, message: str, **fields: Any) -> Optional[LogRecord]:
        """Record a WARNING level entry."""
        return self.record(LogLevel.WARNING, component, message, **fields)

    def error(self, component: str, message: str, **fields: Any) -> Optional[LogRecord]:
        """Record an ERROR level entry."""
        return self.record(LogLevel.ERROR, component, message, **fields)

    def critical(self, component: str, message: str, **fields: Any) -> Optional[LogRecord]:
        """Record a CRITICAL level entry."""
        return self.record(LogLevel.CRITICAL, component, message, **fields)

    # ------------------------------------------------------------------
    # Search and retrieval
    # ------------------------------------------------------------------

    def search(
        self,
        level: Optional[LogLevel] = None,
        component: Optional[str] = None,
        correlation_id: Optional[str] = None,
        message_contains: Optional[str] = None,
        since: Optional[float] = None,
        page: int = 0,
        page_size: int = 100,
    ) -> List[LogRecord]:
        """Return a filtered, paginated view of log records.

        Args:
            level: Filter to records at exactly this level.
            component: Filter to records from this component.
            correlation_id: Filter to records with this correlation ID.
            message_contains: Filter to records whose message contains
                this substring (case-insensitive).
            since: Minimum timestamp (Unix epoch seconds).
            page: Zero-based page index.
            page_size: Records per page.

        Returns:
            Matching :class:`LogRecord` instances for the requested page.
        """
        with self._lock:
            records = list(self._records)

        filtered: List[LogRecord] = []
        for rec in records:
            if level is not None and rec.level != level:
                continue
            if component is not None and rec.component != component:
                continue
            if correlation_id is not None and rec.correlation_id != correlation_id:
                continue
            if message_contains is not None and message_contains.lower() not in rec.message.lower():
                continue
            if since is not None and rec.timestamp < since:
                continue
            filtered.append(rec)

        start = page * page_size
        return filtered[start: start + page_size]

    def get_all(self) -> List[LogRecord]:
        """Return all buffered records (newest last)."""
        with self._lock:
            return list(self._records)

    def count(self) -> int:
        """Return the current number of buffered records."""
        with self._lock:
            return len(self._records)

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Remove all buffered records."""
        with self._lock:
            self._records.clear()

    def set_min_level(self, level: LogLevel) -> None:
        """Update the minimum recording level.

        Args:
            level: New minimum :class:`LogLevel`.
        """
        with self._lock:
            self._min_level = level

    def get_min_level(self) -> LogLevel:
        """Return the current minimum recording level."""
        with self._lock:
            return self._min_level

    # ------------------------------------------------------------------
    # Batch export
    # ------------------------------------------------------------------

    def export_batch(self, max_records: int = 500) -> List[Dict[str, Any]]:
        """Export the most recent records as a list of plain dicts.

        Args:
            max_records: Maximum number of records to export.

        Returns:
            List of serialised record dicts (most recent last).
        """
        with self._lock:
            records = list(self._records)[-max_records:]
        return [r.to_dict() for r in records]
