"""Dashboard Data Source Manager.

Responsible for querying and aggregating metrics from the Flock
observability, AI, cluster, and node subsystems.  Every data source
is registered with a unique name and a callable that produces
:class:`~flock.dashboard.models.DataSourceResult` instances.
"""

import threading
import time
from typing import Callable, Dict, List, Optional

from flock.dashboard.exceptions import DataSourceError
from flock.dashboard.models import DataSourceResult, MetricDataPoint


# Type alias for data-source callables.
DataSourceCallable = Callable[[], DataSourceResult]


class DataSourceManager:
    """Thread-safe registry and executor for dashboard data sources.

    Data sources are registered as named callables that return a
    :class:`DataSourceResult`.  The manager can query one or all
    sources, accumulate results, and handle transient failures without
    propagating exceptions to callers.

    Attributes:
        _lock: Reentrant lock protecting the source registry.
        _sources: Mapping of source name to callable.
    """

    def __init__(self) -> None:
        """Initialise the data-source manager."""
        self._lock: threading.RLock = threading.RLock()
        self._sources: Dict[str, DataSourceCallable] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, name: str, source: DataSourceCallable) -> None:
        """Register a data source callable under a unique name.

        Args:
            name: Unique identifier for the data source.
            source: Callable that returns a :class:`DataSourceResult`.
        """
        with self._lock:
            self._sources[name] = source

    def unregister(self, name: str) -> None:
        """Remove a registered data source.

        Args:
            name: Name of the data source to remove.

        Raises:
            DataSourceError: If ``name`` is not registered.
        """
        with self._lock:
            if name not in self._sources:
                raise DataSourceError(
                    f"Data source '{name}' is not registered."
                )
            del self._sources[name]

    def exists(self, name: str) -> bool:
        """Return ``True`` if the data source is registered."""
        with self._lock:
            return name in self._sources

    def list_sources(self) -> List[str]:
        """Return the names of all registered data sources."""
        with self._lock:
            return list(self._sources.keys())

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def query(self, name: str) -> DataSourceResult:
        """Invoke a single data source and return its result.

        Args:
            name: Name of the data source to query.

        Returns:
            The :class:`DataSourceResult` produced by the source.

        Raises:
            DataSourceError: If ``name`` is not registered or the
                callable raises an exception.
        """
        with self._lock:
            if name not in self._sources:
                raise DataSourceError(
                    f"Data source '{name}' is not registered."
                )
            source = self._sources[name]

        try:
            return source()
        except Exception as exc:
            raise DataSourceError(
                f"Data source '{name}' failed: {exc}"
            ) from exc

    def query_safe(self, name: str) -> DataSourceResult:
        """Invoke a data source, returning an error result on failure.

        Unlike :meth:`query` this method never raises; failures are
        captured in the returned :class:`DataSourceResult`.

        Args:
            name: Name of the data source to query.

        Returns:
            A :class:`DataSourceResult` with ``success=False`` on error.
        """
        try:
            return self.query(name)
        except DataSourceError as exc:
            return DataSourceResult(
                source_name=name,
                data_points=[],
                success=False,
                error=str(exc),
            )

    def query_all(self) -> List[DataSourceResult]:
        """Invoke all registered data sources and return their results.

        Failures are captured as error results rather than propagated.

        Returns:
            List of :class:`DataSourceResult` instances, one per source.
        """
        with self._lock:
            names = list(self._sources.keys())
        return [self.query_safe(name) for name in names]

    # ------------------------------------------------------------------
    # Built-in synthetic source helpers
    # ------------------------------------------------------------------

    def make_constant_source(
        self, name: str, value: float
    ) -> DataSourceCallable:
        """Create and register a source that always returns a constant.

        Useful for testing and placeholder data during development.

        Args:
            name: Source name to register.
            value: Constant float value to emit.

        Returns:
            The registered callable.
        """

        def _source() -> DataSourceResult:
            point = MetricDataPoint(
                timestamp=time.time(),
                metric_name=name,
                value=value,
            )
            return DataSourceResult(source_name=name, data_points=[point])

        self.register(name, _source)
        return _source

    def get_source(self, name: str) -> Optional[DataSourceCallable]:
        """Return the registered callable or ``None``.

        Args:
            name: Source name to look up.

        Returns:
            The callable or ``None`` if not found.
        """
        with self._lock:
            return self._sources.get(name)

    def count(self) -> int:
        """Return the number of registered data sources."""
        with self._lock:
            return len(self._sources)

    def clear(self) -> None:
        """Remove all registered data sources."""
        with self._lock:
            self._sources.clear()
