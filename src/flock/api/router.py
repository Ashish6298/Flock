"""HTTP endpoint router tracking registered path structures."""

from __future__ import annotations

import threading
from typing import Any, Callable, Dict, Optional

from flock.api.exceptions import RouteNotFoundError
from flock.api.models import ApiRoute


class ApiRouter:
    """Thread-safe route dispatcher catalog matching paths to handlers."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # key: (method, path) -> handler callback
        self._routes: Dict[tuple[str, str], Callable[..., Any]] = {}

    def register_route(self, route: ApiRoute, handler: Callable[..., Any]) -> None:
        """Register a path endpoint routing configuration mapping."""
        with self._lock:
            key = (route.method.upper(), route.path)
            self._routes[key] = handler

    def match_and_dispatch(self, method: str, path: str) -> Callable[..., Any]:
        """Dispatch handler callback matching request parameter coordinates.

        Raises:
            RouteNotFoundError: If path pattern registry is empty.
        """
        with self._lock:
            key = (method.upper(), path)
            handler = self._routes.get(key)
            if not handler:
                raise RouteNotFoundError(f"Endpoint '{method} {path}' is not registered.")
            return handler
