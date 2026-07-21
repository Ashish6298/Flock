"""Dashboard Export Engine.

Serialises dashboard panel data to portable formats: JSON, CSV, and a
plain-text stub for PDF/PNG (which in production would delegate to a
headless renderer such as Playwright or WeasyPrint but here produces a
structured text representation to avoid external dependencies).
"""

from __future__ import annotations

import csv
import io
import json
import time
from typing import Any, Dict, List

from flock.dashboard.exceptions import ExportError
from flock.dashboard.models import DataSourceResult, ExportRequest, ExportResult


class ExportEngine:
    """Converts :class:`DataSourceResult` payloads into exportable bytes.

    Supported formats
    -----------------
    * ``json`` – Pretty-printed JSON of the data points.
    * ``csv``  – RFC 4180 CSV with header row.
    * ``pdf``  – Structured text report (headless renderer stub).
    * ``png``  – Structured text report (headless renderer stub).
    """

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def export(
        self,
        request: ExportRequest,
        result: DataSourceResult,
    ) -> ExportResult:
        """Export a data source result to the requested format.

        Args:
            request: The :class:`ExportRequest` containing panel_id and
                format_type.
            result: The :class:`DataSourceResult` to export.

        Returns:
            An :class:`ExportResult` with the serialised payload.

        Raises:
            ExportError: If ``result.success`` is ``False`` or the
                format_type is not supported.
        """
        if not result.success:
            raise ExportError(
                f"Cannot export panel '{request.panel_id}': "
                f"data source error – {result.error}"
            )

        handlers: Dict[str, Any] = {
            "json": self._to_json,
            "csv": self._to_csv,
            "pdf": self._to_pdf_stub,
            "png": self._to_png_stub,
        }

        handler = handlers.get(request.format_type)
        if handler is None:
            raise ExportError(
                f"Unsupported export format '{request.format_type}'. "
                f"Supported: {', '.join(handlers.keys())}."
            )

        payload: bytes = handler(result)
        return ExportResult(
            panel_id=request.panel_id,
            format_type=request.format_type,
            payload=payload,
            success=True,
        )

    # ------------------------------------------------------------------
    # Format serialisers
    # ------------------------------------------------------------------

    def _to_json(self, result: DataSourceResult) -> bytes:
        """Serialise data points to pretty-printed JSON bytes."""
        records: List[Dict[str, Any]] = [
            {
                "timestamp": p.timestamp,
                "metric_name": p.metric_name,
                "value": p.value,
                "labels": p.labels,
            }
            for p in result.data_points
        ]
        data = {
            "source_name": result.source_name,
            "exported_at": time.time(),
            "records": records,
        }
        return json.dumps(data, indent=2).encode("utf-8")

    def _to_csv(self, result: DataSourceResult) -> bytes:
        """Serialise data points to RFC 4180 CSV bytes."""
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["timestamp", "metric_name", "value"])
        for p in result.data_points:
            writer.writerow([p.timestamp, p.metric_name, p.value])
        return buf.getvalue().encode("utf-8")

    def _to_pdf_stub(self, result: DataSourceResult) -> bytes:
        """Return a structured text report as a PDF stub."""
        lines = [
            f"FLOCK DASHBOARD EXPORT – PDF",
            f"Source: {result.source_name}",
            f"Exported at: {time.time():.3f}",
            "=" * 60,
        ]
        for p in result.data_points:
            lines.append(
                f"  [{p.timestamp:.3f}] {p.metric_name} = {p.value}"
            )
        return "\n".join(lines).encode("utf-8")

    def _to_png_stub(self, result: DataSourceResult) -> bytes:
        """Return a structured text report as a PNG stub."""
        lines = [
            f"FLOCK DASHBOARD EXPORT – PNG",
            f"Source: {result.source_name}",
            f"Exported at: {time.time():.3f}",
            "=" * 60,
        ]
        for p in result.data_points:
            lines.append(
                f"  [{p.timestamp:.3f}] {p.metric_name} = {p.value}"
            )
        return "\n".join(lines).encode("utf-8")

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def supported_formats() -> List[str]:
        """Return the list of supported export format strings."""
        return ["json", "csv", "pdf", "png"]
