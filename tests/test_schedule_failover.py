"""Unit tests for scheduler failovers."""

from flock.events.bus import EventBus
from flock.scheduling.scheduler import SchedulingEngine


def test_leadership_handover_bounds() -> None:
    events = EventBus()
    engine = SchedulingEngine(events)

    engine.acquire_leadership()
    assert engine.is_leader is True

    engine.revoke_leadership()
    assert engine.is_leader is False
