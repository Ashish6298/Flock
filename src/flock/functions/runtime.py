"""Runtime Engine executing code within isolated environments."""

from __future__ import annotations

from typing import Any
from flock.functions.exceptions import RuntimeExecutionError
from flock.functions.models import FunctionDefinition, InvocationRequest, InvocationResult


class RuntimeEngine:
    """Executes Python code scripts dynamically."""

    def __init__(self) -> None:
        pass

    def execute_handler(self, definition: FunctionDefinition, request: InvocationRequest) -> InvocationResult:
        """Evaluate string code inside local variables namespace.

        Raises:
            RuntimeExecutionError: If execution throws Python Exception.
        """
        local_scope: dict[str, Any] = {}
        try:
            # Compile and execute handler string to expose functions
            exec(definition.handler_code, {}, local_scope)
            handler = local_scope.get("handler")
            if not handler:
                raise RuntimeExecutionError("Handler code is missing 'handler' function entrypoint.")

            output = handler(*request.args, **request.kwargs)
            return InvocationResult(
                invocation_id=request.invocation_id,
                success=True,
                output=output,
            )
        except Exception as exc:
            return InvocationResult(
                invocation_id=request.invocation_id,
                success=False,
                error=str(exc),
            )
