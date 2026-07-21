"""Unit tests for ExportEngine."""

import json
import pytest

from flock.dashboard.exporter import ExportEngine
from flock.dashboard.models import DataSourceResult, ExportRequest, MetricDataPoint
from flock.dashboard.exceptions import ExportError


def _make_result() -> DataSourceResult:
    points = [
        MetricDataPoint(timestamp=1.0, metric_name="cpu", value=72.5),
        MetricDataPoint(timestamp=2.0, metric_name="cpu", value=68.3),
    ]
    return DataSourceResult(source_name="cpu_pct", data_points=points)


def test_export_json() -> None:
    engine = ExportEngine()
    req = ExportRequest(panel_id="p1", format_type="json")
    result = engine.export(req, _make_result())
    assert result.success is True
    parsed = json.loads(result.payload.decode("utf-8"))
    assert "records" in parsed
    assert len(parsed["records"]) == 2


def test_export_csv() -> None:
    engine = ExportEngine()
    req = ExportRequest(panel_id="p1", format_type="csv")
    result = engine.export(req, _make_result())
    assert result.success is True
    text = result.payload.decode("utf-8")
    assert "timestamp" in text
    assert "cpu" in text


def test_export_pdf_stub() -> None:
    engine = ExportEngine()
    req = ExportRequest(panel_id="p1", format_type="pdf")
    result = engine.export(req, _make_result())
    assert result.success is True
    assert b"FLOCK DASHBOARD EXPORT" in result.payload


def test_export_png_stub() -> None:
    engine = ExportEngine()
    req = ExportRequest(panel_id="p1", format_type="png")
    result = engine.export(req, _make_result())
    assert result.success is True
    assert b"FLOCK DASHBOARD EXPORT" in result.payload


def test_export_unsupported_format_raises() -> None:
    engine = ExportEngine()
    req = ExportRequest(panel_id="p1", format_type="xml")
    with pytest.raises(ExportError):
        engine.export(req, _make_result())


def test_export_failed_result_raises() -> None:
    engine = ExportEngine()
    req = ExportRequest(panel_id="p1", format_type="json")
    bad = DataSourceResult(source_name="x", success=False, error="timeout")
    with pytest.raises(ExportError):
        engine.export(req, bad)


def test_supported_formats() -> None:
    formats = ExportEngine.supported_formats()
    assert "json" in formats
    assert "csv" in formats
    assert "pdf" in formats
    assert "png" in formats
