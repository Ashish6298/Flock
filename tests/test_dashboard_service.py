"""Unit tests for DashboardService lifecycle."""

import pytest

from flock.dashboard.service import DashboardService
from flock.dashboard.exceptions import DashboardStartupError, DashboardShutdownError


def test_service_starts_and_stops() -> None:
    svc = DashboardService()
    svc.start()
    assert svc.is_running is True
    svc.stop()
    assert svc.is_running is False


def test_service_double_start_raises() -> None:
    svc = DashboardService()
    svc.start()
    with pytest.raises(DashboardStartupError):
        svc.start()
    svc.stop()


def test_service_stop_without_start_raises() -> None:
    svc = DashboardService()
    with pytest.raises(DashboardShutdownError):
        svc.stop()


def test_service_metrics_after_start() -> None:
    svc = DashboardService()
    svc.start()
    metrics = svc.get_metrics()
    assert metrics.active_sessions >= 0
    assert metrics.connected_websockets >= 0
    svc.stop()


def test_service_statistics_page_views() -> None:
    svc = DashboardService()
    svc.start()
    svc.record_page_view()
    svc.record_page_view()
    stats = svc.get_statistics()
    assert stats.total_page_views == 2
    svc.stop()


def test_service_statistics_render_time() -> None:
    svc = DashboardService()
    svc.start()
    svc.record_render_time(12.5)
    svc.record_render_time(7.5)
    stats = svc.get_statistics()
    assert stats.average_render_ms == pytest.approx(10.0)
    svc.stop()
