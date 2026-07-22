"""Dashboard Renderer.

Responsible for serialising widget data into the JSON payload
structure expected by the frontend.  The renderer is deliberately
transport-independent: it produces plain Python dicts that the
HTTP/WebSocket layer can serialise as needed.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List

from flock.dashboard.exceptions import RenderError
from flock.dashboard.models import (
    DataSourceResult,
    MetricDataPoint,
    WidgetDefinition,
)


class DashboardRenderer:
    """Converts raw metric data into structured widget render payloads.

    Each ``render_*`` method accepts the widget definition and its
    data-source result and returns a plain dict that maps directly to
    the JSON body sent to the frontend.

    The renderer supports four core widget types:

    * ``chart`` – time-series line/area chart
    * ``gauge`` – single numeric value with percentage fill
    * ``stat`` – scalar summary card
    * ``table`` – tabular row/column data
    * ``log``  – scrollable log stream (raw string data points)
    * ``map``  – placeholder for topology map widgets

    For unknown widget types :meth:`render` falls back to a raw dump.
    """

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def render(
        self,
        widget: WidgetDefinition,
        result: DataSourceResult,
    ) -> Dict[str, Any]:
        """Render a widget using the appropriate strategy.

        Args:
            widget: The :class:`WidgetDefinition` describing the widget.
            result: The :class:`DataSourceResult` containing metric data.

        Returns:
            A plain dict payload ready for JSON serialisation.

        Raises:
            RenderError: If ``result.success`` is ``False``.
        """
        if not result.success:
            raise RenderError(
                f"Cannot render widget '{widget.widget_id}': "
                f"data source error – {result.error}"
            )

        dispatch: Dict[
            str, Callable[[WidgetDefinition, DataSourceResult], Dict[str, Any]]
        ] = {
            "chart": self.render_chart,
            "gauge": self.render_gauge,
            "stat": self.render_stat,
            "table": self.render_table,
            "log": self.render_log,
            "map": self.render_map,
        }

        renderer = dispatch.get(widget.widget_type, self._render_raw)
        return renderer(widget, result)

    # ------------------------------------------------------------------
    # Type-specific renderers
    # ------------------------------------------------------------------

    def render_chart(
        self,
        widget: WidgetDefinition,
        result: DataSourceResult,
    ) -> Dict[str, Any]:
        """Render a time-series chart payload."""
        return {
            "widget_id": widget.widget_id,
            "widget_type": "chart",
            "title": widget.title,
            "rendered_at": time.time(),
            "series": [
                {
                    "timestamp": p.timestamp,
                    "value": p.value,
                    "labels": p.labels,
                }
                for p in result.data_points
            ],
        }

    def render_gauge(
        self,
        widget: WidgetDefinition,
        result: DataSourceResult,
    ) -> Dict[str, Any]:
        """Render a gauge payload using the latest data point."""
        latest = self._latest(result.data_points)
        return {
            "widget_id": widget.widget_id,
            "widget_type": "gauge",
            "title": widget.title,
            "rendered_at": time.time(),
            "value": latest,
            "percent": min(100.0, max(0.0, latest)),
        }

    def render_stat(
        self,
        widget: WidgetDefinition,
        result: DataSourceResult,
    ) -> Dict[str, Any]:
        """Render a scalar stat card payload."""
        values = [p.value for p in result.data_points]
        return {
            "widget_id": widget.widget_id,
            "widget_type": "stat",
            "title": widget.title,
            "rendered_at": time.time(),
            "current": self._latest(result.data_points),
            "average": sum(values) / len(values) if values else 0.0,
            "count": len(values),
        }

    def render_table(
        self,
        widget: WidgetDefinition,
        result: DataSourceResult,
    ) -> Dict[str, Any]:
        """Render a tabular payload from metric data points."""
        rows: List[Dict[str, Any]] = [
            {
                "timestamp": p.timestamp,
                "metric": p.metric_name,
                "value": p.value,
                **p.labels,
            }
            for p in result.data_points
        ]
        return {
            "widget_id": widget.widget_id,
            "widget_type": "table",
            "title": widget.title,
            "rendered_at": time.time(),
            "columns": ["timestamp", "metric", "value"],
            "rows": rows,
        }

    def render_log(
        self,
        widget: WidgetDefinition,
        result: DataSourceResult,
    ) -> Dict[str, Any]:
        """Render a log-stream payload."""
        entries = [
            f"[{p.timestamp:.3f}] {p.metric_name}={p.value}"
            for p in result.data_points
        ]
        return {
            "widget_id": widget.widget_id,
            "widget_type": "log",
            "title": widget.title,
            "rendered_at": time.time(),
            "entries": entries,
        }

    def render_map(
        self,
        widget: WidgetDefinition,
        result: DataSourceResult,
    ) -> Dict[str, Any]:
        """Render a topology map placeholder payload."""
        return {
            "widget_id": widget.widget_id,
            "widget_type": "map",
            "title": widget.title,
            "rendered_at": time.time(),
            "nodes": [
                {"id": p.metric_name, "value": p.value}
                for p in result.data_points
            ],
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _render_raw(
        self,
        widget: WidgetDefinition,
        result: DataSourceResult,
    ) -> Dict[str, Any]:
        """Fallback renderer for unknown widget types."""
        return {
            "widget_id": widget.widget_id,
            "widget_type": widget.widget_type,
            "title": widget.title,
            "rendered_at": time.time(),
            "raw_points": [
                {"timestamp": p.timestamp, "value": p.value}
                for p in result.data_points
            ],
        }

    @staticmethod
    def _latest(points: List[MetricDataPoint]) -> float:
        """Return the value of the most recent data point or zero."""
        if not points:
            return 0.0
        return max(points, key=lambda p: p.timestamp).value
