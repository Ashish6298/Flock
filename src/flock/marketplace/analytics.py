"""Marketplace analytics reports engine."""

from __future__ import annotations

import time
import threading
from flock.marketplace.models import MarketplaceMetricsReport


class MarketplaceAnalyticsEngine:
    """Aggregates installation metrics and reports marketplace health scores."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._total_packages = 0
        self._total_downloads = 0
        self._failed_installations = 0
        self._health_percentage = 100.0

    def record_download(self, package_id: str) -> None:
        with self._lock:
            self._total_downloads += 1

    def record_install_failure(self) -> None:
        with self._lock:
            self._failed_installations += 1

    def update_totals(self, total_packages: int, health_percentage: float) -> None:
        with self._lock:
            self._total_packages = total_packages
            self._health_percentage = health_percentage

    def generate_report(self) -> MarketplaceMetricsReport:
        """Produce a strongly typed metrics report snapshot."""
        with self._lock:
            return MarketplaceMetricsReport(
                timestamp=time.time(),
                total_packages=self._total_packages,
                total_downloads=self._total_downloads,
                failed_installations=self._failed_installations,
                health_percentage=self._health_percentage,
            )
