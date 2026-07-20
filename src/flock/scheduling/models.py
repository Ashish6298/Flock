"""Scheduling Models."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ScheduleDefinition(BaseModel):
    """Represents a scheduled workflow or task trigger entry."""
    schedule_id: str
    cron_expression: str  # e.g. "*/5 * * * *"
    task_payload: bytes
    is_active: bool = True

    model_config = {
        "frozen": True
    }


class EventTrigger(BaseModel):
    """Represents an event pattern triggering a specific schedule."""
    trigger_id: str
    event_pattern: str
    target_schedule_id: str

    model_config = {
        "frozen": True
    }


class ScheduleExecution(BaseModel):
    """Represents a discrete execution run triggered by scheduling engine."""
    execution_id: str
    schedule_id: str
    triggered_at: float
    status: str  # "PENDING", "RUNNING", "COMPLETED", "FAILED"

    model_config = {
        "frozen": True
    }


class SchedulerSnapshot(BaseModel):
    """Represents replicated scheduler metadata state snapshot."""
    timestamp: float
    active_schedules_count: int
    last_leader_epoch: int

    model_config = {
        "frozen": True
    }
