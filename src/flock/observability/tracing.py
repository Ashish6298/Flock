"""Tracing Engine (APM tracking)."""

from __future__ import annotations

import threading
import time
import uuid
from typing import Dict, List, Optional

from flock.events.bus import EventBus
from flock.observability.models import Span


class TracingEngine:
    """Manages distributed traces, span hierarchies, and execution context tracking."""

    def __init__(self, event_bus: EventBus) -> None:
        self._events = event_bus
        self._lock = threading.Lock()

        # Active traces: trace_id -> List of Spans
        self._spans: Dict[str, List[Span]] = {}

    def start_span(
        self,
        name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> Span:
        """Start a new execution span.

        Args:
            name: Human-readable trace span descriptor.
            trace_id: Shared context identifier. Generated if not supplied.
            parent_span_id: Optional parent identifier.

        Returns:
            The started Span metadata object.
        """
        tid = trace_id or str(uuid.uuid4())
        sid = str(uuid.uuid4())

        span = Span(
            span_id=sid,
            parent_span_id=parent_span_id,
            trace_id=tid,
            name=name,
            start_time=time.time(),
        )

        with self._lock:
            self._spans.setdefault(tid, []).append(span)

        # Publish EventBus alert asynchronously
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                self._events.publish(
                    "trace.span.created",
                    {"trace_id": tid, "span_id": sid, "name": name},
                )
            )
        except RuntimeError:
            pass

        return span

    def finish_span(self, span: Span) -> Span:
        """Close an active execution span, marking completion timestamp.

        Args:
            span: The Span metadata to finish.

        Returns:
            The finished Span containing end_time.
        """
        finished = Span(
            span_id=span.span_id,
            parent_span_id=span.parent_span_id,
            trace_id=span.trace_id,
            name=span.name,
            start_time=span.start_time,
            end_time=time.time(),
            annotations=span.annotations,
        )

        with self._lock:
            # Replace placeholder span with finished span
            trace_spans = self._spans.get(span.trace_id, [])
            for idx, s in enumerate(trace_spans):
                if s.span_id == span.span_id:
                    trace_spans[idx] = finished
                    break

        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                self._events.publish(
                    "trace.span.finished",
                    {
                        "trace_id": span.trace_id,
                        "span_id": span.span_id,
                        "duration_sec": finished.end_time - finished.start_time,  # type: ignore[operator]
                    },
                )
            )
        except RuntimeError:
            pass

        return finished

    def get_trace_spans(self, trace_id: str) -> List[Span]:
        """Fetch all execution spans associated with a trace_id."""
        with self._lock:
            return list(self._spans.get(trace_id, []))
