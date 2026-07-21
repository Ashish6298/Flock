"""Unit tests for TriggerEngine."""

from flock.functions.models import TriggerDefinition
from flock.functions.triggers import TriggerEngine


def test_trigger_matching() -> None:
    engine = TriggerEngine()
    t = TriggerDefinition(trigger_id="t1", source="HTTP", target_function="f1")

    engine.register_trigger(t)
    matches = engine.match_triggers("HTTP")
    assert matches == [t]

    # Mismatched source returns empty list
    assert engine.match_triggers("STREAM") == []
