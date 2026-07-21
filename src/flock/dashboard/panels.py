"""Dashboard Panel Registry.

Manages registration, retrieval, and access-control checks for
dashboard panels.  Each panel aggregates one or more widget IDs and
carries an optional list of roles that are permitted to view it.
"""

import threading
from typing import Dict, List, Optional

from flock.dashboard.exceptions import PanelNotFoundError, PermissionDeniedError
from flock.dashboard.models import PanelDefinition


class PanelRegistry:
    """Thread-safe registry for dashboard panel definitions.

    Panels group widgets into logical views.  They optionally declare
    ``required_roles`` so that the authentication layer can gate access
    without coupling to the security subsystem directly.

    Attributes:
        _lock: Reentrant lock protecting the internal panel store.
        _panels: Mapping of panel_id to PanelDefinition instances.
    """

    def __init__(self) -> None:
        """Initialise an empty panel registry."""
        self._lock: threading.RLock = threading.RLock()
        self._panels: Dict[str, PanelDefinition] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, panel: PanelDefinition) -> None:
        """Register a panel definition.

        Args:
            panel: The :class:`PanelDefinition` to register.
        """
        with self._lock:
            self._panels[panel.panel_id] = panel

    def unregister(self, panel_id: str) -> None:
        """Remove a panel from the registry.

        Args:
            panel_id: Identifier of the panel to remove.

        Raises:
            PanelNotFoundError: If ``panel_id`` is not registered.
        """
        with self._lock:
            if panel_id not in self._panels:
                raise PanelNotFoundError(
                    f"Panel '{panel_id}' is not registered."
                )
            del self._panels[panel_id]

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get(self, panel_id: str) -> PanelDefinition:
        """Return the panel definition for a given identifier.

        Args:
            panel_id: Identifier to look up.

        Returns:
            The matching :class:`PanelDefinition`.

        Raises:
            PanelNotFoundError: If ``panel_id`` is not registered.
        """
        with self._lock:
            if panel_id not in self._panels:
                raise PanelNotFoundError(
                    f"Panel '{panel_id}' is not registered."
                )
            return self._panels[panel_id]

    def get_optional(self, panel_id: str) -> Optional[PanelDefinition]:
        """Return the panel or ``None`` if not found.

        Args:
            panel_id: Identifier to look up.

        Returns:
            The :class:`PanelDefinition` or ``None``.
        """
        with self._lock:
            return self._panels.get(panel_id)

    def list_all(self) -> List[PanelDefinition]:
        """Return all registered panel definitions."""
        with self._lock:
            return list(self._panels.values())

    def exists(self, panel_id: str) -> bool:
        """Check whether a panel identifier is registered."""
        with self._lock:
            return panel_id in self._panels

    def count(self) -> int:
        """Return the number of registered panels."""
        with self._lock:
            return len(self._panels)

    # ------------------------------------------------------------------
    # Access control
    # ------------------------------------------------------------------

    def check_access(self, panel_id: str, user_roles: List[str]) -> None:
        """Verify that a user holds a required role for the panel.

        If the panel has no ``required_roles`` configured access is
        granted unconditionally.

        Args:
            panel_id: Identifier of the panel to check.
            user_roles: Roles held by the requesting user.

        Raises:
            PanelNotFoundError: If ``panel_id`` is not registered.
            PermissionDeniedError: If the user holds none of the
                required roles.
        """
        panel = self.get(panel_id)
        if not panel.required_roles:
            return
        if not any(role in panel.required_roles for role in user_roles):
            raise PermissionDeniedError(
                f"User lacks permission to view panel '{panel_id}'."
            )

    def find_accessible(self, user_roles: List[str]) -> List[PanelDefinition]:
        """Return all panels accessible to a user with the given roles.

        Args:
            user_roles: Roles held by the requesting user.

        Returns:
            Panels the user is allowed to view.
        """
        with self._lock:
            result: List[PanelDefinition] = []
            for panel in self._panels.values():
                if not panel.required_roles:
                    result.append(panel)
                elif any(r in panel.required_roles for r in user_roles):
                    result.append(panel)
            return result

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def register_many(self, panels: List[PanelDefinition]) -> None:
        """Register multiple panel definitions atomically."""
        with self._lock:
            for panel in panels:
                self._panels[panel.panel_id] = panel

    def clear(self) -> None:
        """Remove all registered panels."""
        with self._lock:
            self._panels.clear()
