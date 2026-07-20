"""Unit tests for TracingEngine."""

import asyncio
from typing import Dict, Any
import pytest
from flock.events.bus import EventBus
from flock.observability.tracing import TracingEngine


@pytest.mark.asyncio
async def test_tracing_engine_nesting_and_timelines() -> None:
    events = EventBus()
    tracing = TracingEngine(events)

    span_events = []

    async def on_span_created(data: Dict[str, Any]) -> None:
        span_events.append(data)

    events.subscribe("trace.span.created", on_span_created)

    # Start parent span
    parent = tracing.start_span(name="parent-op")
    assert parent.trace_id is not None
    assert parent.span_id is not None

    # Start child span nested
    child = tracing.start_span(
        name="child-op",
        trace_id=parent.trace_id,
        parent_span_id=parent.span_id,
    )
    assert child.trace_id == parent.trace_id
    assert child.parent_span_id == parent.span_id

    # Finish spans
    tracing.finish_span(child)
    tracing.finish_span(parent)

    # Let event loop run tasks
    await asyncio.sleep(0.01)

    assert len(span_events) == 2
    assert span_events[0]["name"] == "parent-op"
    assert span_events[1]["name"] == "child-op"

    all_spans = tracing.get_trace_spans(parent.trace_id)
    assert len(all_spans) == 2
