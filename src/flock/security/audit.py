"""Security Audit Logger capturing events in immutable records."""

from __future__ import annotations

import time
from typing import Any, Dict, List

import structlog

from flock.events.bus import EventBus
from flock.security.models import SecurityAuditRecord

logger = structlog.get_logger()


class SecurityAuditLogger:
    """Consumes and logs security-related events for compliance monitoring."""

    def __init__(self, event_bus: EventBus) -> None:
        self._events = event_bus
        self.audit_records: List[SecurityAuditRecord] = []

    def log_event(self, event_name: str, details: Dict[str, str]) -> None:
        """Create and append an immutable audit trail entry."""
        record = SecurityAuditRecord(
            event_name=event_name,
            timestamp=time.time(),
            details=details,
        )
        self.audit_records.append(record)
        logger.info("Security audit log entry", security_event=event_name, details=details)

        # Notify EventBus
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                self._events.publish(
                    "security.audit.logged",
                    {"event_name": event_name, "details": details},
                )
            )
        except RuntimeError:
            pass
