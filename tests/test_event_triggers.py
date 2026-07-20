"""Unit tests for event-driven triggers matching."""

from flock.events.bus import EventBus
from flock.scheduling.models import EventTrigger
from flock.scheduling.trigger import EventTriggerEngine


def test_trigger_matching_evaluations() -> None:
    events = EventBus()
    engine = EventTriggerEngine(events)

    t1 = EventTrigger(trigger_id="t1", event_pattern="workflow.completed", target_schedule_id="sch-9")
    engine.register_trigger(t1)

    matched = engine.match_event("workflow.completed")
    assert len(matched) == 1
    assert matched[0].target_schedule_id == "sch-9"
