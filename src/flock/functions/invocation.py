"""Invocation Router executing handlers or delegating calls."""

from __future__ import annotations

import structlog

from flock.functions.exceptions import InvocationFailedError
from flock.functions.models import InvocationRequest, InvocationResult
from flock.functions.registry import FunctionRegistry
from flock.functions.runtime import RuntimeEngine

logger = structlog.get_logger()


class InvocationEngine:
    """Coordinates local executions and logs results."""

    def __init__(self, registry: FunctionRegistry, runtime: RuntimeEngine) -> None:
        self._registry = registry
        self._runtime = runtime

    def invoke(self, request: InvocationRequest) -> InvocationResult:
        """Route execution to local runtime compiler.

        Raises:
            InvocationFailedError: If target function is not registered.
        """
        try:
            func = self._registry.get_function(request.function_id)
        except Exception as exc:
            raise InvocationFailedError(f"Function lookup failed: {exc}") from exc

        if not func:
            raise InvocationFailedError(f"Function '{request.function_id}' not found in registry.")

        logger.info(
            "Invoking serverless function",
            function_id=request.function_id,
            invocation_id=request.invocation_id,
        )
        return self._runtime.execute_handler(func, request)
