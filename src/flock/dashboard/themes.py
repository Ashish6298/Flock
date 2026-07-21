"""Dashboard Theme Manager.

Provides a registry of UI themes for the web dashboard.  Themes
control colour palette, typography, and overall visual style.
The default ``dark`` and ``light`` themes are always pre-registered.
"""

import threading
from typing import Dict, List, Optional

from flock.dashboard.exceptions import ThemeNotFoundError
from flock.dashboard.models import DashboardTheme

_DEFAULT_THEMES: List[DashboardTheme] = [
    DashboardTheme(
        theme_name="dark",
        primary_color="#6C63FF",
        background_color="#0D0D1A",
        font_family="Inter, sans-serif",
    ),
    DashboardTheme(
        theme_name="light",
        primary_color="#5A54E8",
        background_color="#F5F7FA",
        font_family="Inter, sans-serif",
    ),
    DashboardTheme(
        theme_name="midnight",
        primary_color="#00D4FF",
        background_color="#060714",
        font_family="Outfit, sans-serif",
    ),
]


class ThemeManager:
    """Thread-safe registry for dashboard UI themes.

    The default ``dark``, ``light``, and ``midnight`` themes are
    registered at construction time.  Additional themes can be added
    at runtime.

    Attributes:
        _lock: Reentrant lock protecting the theme store.
        _themes: Mapping of theme_name to DashboardTheme.
        _active_theme: Name of the currently active theme.
    """

    def __init__(self) -> None:
        """Initialise the theme manager with built-in themes."""
        self._lock: threading.RLock = threading.RLock()
        self._themes: Dict[str, DashboardTheme] = {}
        self._active_theme: str = "dark"

        for theme in _DEFAULT_THEMES:
            self._themes[theme.theme_name] = theme

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, theme: DashboardTheme) -> None:
        """Register a new theme, overwriting any existing entry.

        Args:
            theme: The :class:`DashboardTheme` to register.
        """
        with self._lock:
            self._themes[theme.theme_name] = theme

    def unregister(self, theme_name: str) -> None:
        """Remove a theme from the registry.

        Args:
            theme_name: Name of the theme to remove.

        Raises:
            ThemeNotFoundError: If ``theme_name`` is not registered.
        """
        with self._lock:
            if theme_name not in self._themes:
                raise ThemeNotFoundError(
                    f"Theme '{theme_name}' is not registered."
                )
            del self._themes[theme_name]

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get(self, theme_name: str) -> DashboardTheme:
        """Return a theme by name.

        Args:
            theme_name: Name to look up.

        Returns:
            The matching :class:`DashboardTheme`.

        Raises:
            ThemeNotFoundError: If the theme is not registered.
        """
        with self._lock:
            if theme_name not in self._themes:
                raise ThemeNotFoundError(
                    f"Theme '{theme_name}' is not registered."
                )
            return self._themes[theme_name]

    def get_optional(self, theme_name: str) -> Optional[DashboardTheme]:
        """Return a theme or ``None`` if not registered."""
        with self._lock:
            return self._themes.get(theme_name)

    def list_all(self) -> List[DashboardTheme]:
        """Return all registered themes."""
        with self._lock:
            return list(self._themes.values())

    def exists(self, theme_name: str) -> bool:
        """Return ``True`` if the named theme is registered."""
        with self._lock:
            return theme_name in self._themes

    # ------------------------------------------------------------------
    # Active theme
    # ------------------------------------------------------------------

    def set_active(self, theme_name: str) -> None:
        """Set the active theme.

        Args:
            theme_name: Name of the theme to activate.

        Raises:
            ThemeNotFoundError: If the theme is not registered.
        """
        with self._lock:
            if theme_name not in self._themes:
                raise ThemeNotFoundError(
                    f"Theme '{theme_name}' is not registered."
                )
            self._active_theme = theme_name

    def get_active(self) -> DashboardTheme:
        """Return the currently active :class:`DashboardTheme`."""
        with self._lock:
            return self._themes[self._active_theme]

    def active_name(self) -> str:
        """Return the name of the currently active theme."""
        with self._lock:
            return self._active_theme

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def count(self) -> int:
        """Return the number of registered themes."""
        with self._lock:
            return len(self._themes)
