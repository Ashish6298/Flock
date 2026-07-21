"""Functions Registry tracking registered handlers and revisions."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from flock.functions.exceptions import FunctionNotFoundError
from flock.functions.models import FunctionDefinition


class FunctionRegistry:
    """Thread-safe catalog indexing dynamic functions."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # function_id -> FunctionDefinition
        self._functions: Dict[str, FunctionDefinition] = {}

    def register_function(self, function: FunctionDefinition) -> None:
        """Register function configuration spec."""
        with self._lock:
            self._functions[function.function_id] = function

    def unregister_function(self, function_id: str) -> None:
        """Remove function definition spec from catalogue."""
        with self._lock:
            self._functions.pop(function_id, None)

    def get_function(self, function_id: str) -> Optional[FunctionDefinition]:
        """Fetch function configuration spec.

        Raises:
            FunctionNotFoundError: If target function ID is missing.
        """
        with self._lock:
            func = self._functions.get(function_id)
            if not func:
                raise FunctionNotFoundError(f"Function '{function_id}' not found.")
            return func

    def list_functions(self) -> List[FunctionDefinition]:
        """List all active function configurations."""
        with self._lock:
            return list(self._functions.values())
