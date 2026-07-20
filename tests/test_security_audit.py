"""Unit tests for SecurityAuditLogger."""

import asyncio
from typing import Dict, Any
import pytest
from flock.events.bus import EventBus
from flock.security.audit import SecurityAuditLogger


@pytest.mark.asyncio
async def test_audit_logs_publish_events() -> None:
    events = EventBus()
    logger = SecurityAuditLogger(events)

    audits = []

    async def on_audit_log(data: Dict[str, Any]) -> None:
        audits.append(data)

    events.subscribe("security.audit.logged", on_audit_log)

    logger.log_event("authentication.succeeded", {"node_id": "node-12"})

    # Let event loop run tasks
    await asyncio.sleep(0.01)

    assert len(audits) == 1
    assert audits[0]["event_name"] == "authentication.succeeded"
    assert audits[0]["details"]["node_id"] == "node-12"
