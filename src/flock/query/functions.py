"""Functions Registry for Query Subsystem."""

from __future__ import annotations

import math
import threading
from typing import Any, Callable, Dict, Optional

from flock.query.exceptions import FunctionNotFoundError
from flock.query.models import FunctionMetadata


class QueryFunctionRegistry:
    """Manages mathematical and string functions registration thread-safely."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # name -> metadata
        self._metadata: Dict[str, FunctionMetadata] = {}
        
        # name -> callable function
        self._callables: Dict[str, Callable[..., Any]] = {}

        self._register_builtins()

    def register_function(self, name: str, arity: int, func: Callable[..., Any]) -> None:
        """Register custom scalar mapping function."""
        with self._lock:
            self._metadata[name] = FunctionMetadata(name=name, arity=arity)
            self._callables[name] = func

    def execute_function(self, name: str, *args: Any) -> Any:
        """Evaluate registered function.

        Raises:
            FunctionNotFoundError: If target function is missing.
        """
        with self._lock:
            meta = self._metadata.get(name)
            func = self._callables.get(name)
            if not meta or not func:
                raise FunctionNotFoundError(f"Scalar function '{name}' is not registered.")
            
            if len(args) != meta.arity:
                raise ValueError(
                    f"Function '{name}' expects {meta.arity} arguments, got {len(args)}."
                )

            return func(*args)

    def _register_builtins(self) -> None:
        """Register math and string built-in routines."""
        self.register_function("abs", 1, lambda x: abs(float(x)))
        self.register_function("upper", 1, lambda s: str(s).upper())
        self.register_function("lower", 1, lambda s: str(s).lower())
