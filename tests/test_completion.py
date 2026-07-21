"""Unit tests for AutoCompleteEngine."""

from flock.cli.completion import AutoCompleteEngine


def test_completion_matches() -> None:
    engine = AutoCompleteEngine(candidates=["status", "start", "stop", "reboot"])
    
    matches = engine.get_completions("st")
    vals = [m.value for m in matches]
    assert "status" in vals
    assert "start" in vals
    assert "stop" in vals
    assert "reboot" not in vals
