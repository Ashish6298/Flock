"""Dashboard Widget Registry.

Manages registration, retrieval, and lifecycle of dashboard widgets.
Each widget maps to a data source and a rendering type used by the
frontend renderer and WebSocket broadcaster.
"""

import threading
from typing import Dict, List, Optional

from flock.dashboard.exceptions import WidgetNotFoundError
from flock.dashboard.models import WidgetDefinition


class WidgetRegistry:
    """Thread-safe registry for dashboard widget definitions.

    Widgets are registered with a unique ``widget_id``, a human-readable
    title, a ``data_source`` identifier, and a ``widget_type`` that
    instructs the frontend renderer how to visualise the data.

    Attributes:
        _lock: Reentrant threading lock protecting the internal store.
        _widgets: Mapping of widget_id to WidgetDefinition instances.
    """

    def __init__(self) -> None:
        """Initialise an empty widget registry."""
        self._lock: threading.RLock = threading.RLock()
        self._widgets: Dict[str, WidgetDefinition] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, widget: WidgetDefinition) -> None:
        """Register a widget definition.

        Args:
            widget: The :class:`WidgetDefinition` to register.
        """
        with self._lock:
            self._widgets[widget.widget_id] = widget

    def unregister(self, widget_id: str) -> None:
        """Remove a widget from the registry.

        Args:
            widget_id: Identifier of the widget to remove.

        Raises:
            WidgetNotFoundError: If ``widget_id`` is not registered.
        """
        with self._lock:
            if widget_id not in self._widgets:
                raise WidgetNotFoundError(
                    f"Widget '{widget_id}' is not registered."
                )
            del self._widgets[widget_id]

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get(self, widget_id: str) -> WidgetDefinition:
        """Return the widget definition for a given identifier.

        Args:
            widget_id: Identifier to look up.

        Returns:
            The matching :class:`WidgetDefinition`.

        Raises:
            WidgetNotFoundError: If ``widget_id`` is not registered.
        """
        with self._lock:
            if widget_id not in self._widgets:
                raise WidgetNotFoundError(
                    f"Widget '{widget_id}' is not registered."
                )
            return self._widgets[widget_id]

    def list_all(self) -> List[WidgetDefinition]:
        """Return all registered widget definitions.

        Returns:
            Snapshot list of all registered widgets.
        """
        with self._lock:
            return list(self._widgets.values())

    def find_by_type(self, widget_type: str) -> List[WidgetDefinition]:
        """Return all widgets of a given type.

        Args:
            widget_type: Type string to filter by (e.g. ``'chart'``).

        Returns:
            List of matching :class:`WidgetDefinition` instances.
        """
        with self._lock:
            return [
                w for w in self._widgets.values()
                if w.widget_type == widget_type
            ]

    def find_by_source(self, data_source: str) -> List[WidgetDefinition]:
        """Return all widgets that use the given data source.

        Args:
            data_source: Data source name to filter by.

        Returns:
            List of matching :class:`WidgetDefinition` instances.
        """
        with self._lock:
            return [
                w for w in self._widgets.values()
                if w.data_source == data_source
            ]

    def exists(self, widget_id: str) -> bool:
        """Check whether a widget identifier is registered.

        Args:
            widget_id: Identifier to check.

        Returns:
            ``True`` if the widget exists, ``False`` otherwise.
        """
        with self._lock:
            return widget_id in self._widgets

    def count(self) -> int:
        """Return the number of registered widgets."""
        with self._lock:
            return len(self._widgets)

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def register_many(self, widgets: List[WidgetDefinition]) -> None:
        """Register multiple widget definitions atomically.

        Args:
            widgets: Sequence of :class:`WidgetDefinition` instances.
        """
        with self._lock:
            for widget in widgets:
                self._widgets[widget.widget_id] = widget

    def clear(self) -> None:
        """Remove all registered widgets."""
        with self._lock:
            self._widgets.clear()

    # ------------------------------------------------------------------
    # Optional lookup
    # ------------------------------------------------------------------

    def get_optional(self, widget_id: str) -> Optional[WidgetDefinition]:
        """Return the widget or ``None`` if not found.

        Args:
            widget_id: Identifier to look up.

        Returns:
            The :class:`WidgetDefinition` or ``None``.
        """
        with self._lock:
            return self._widgets.get(widget_id)
