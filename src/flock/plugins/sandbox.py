"""Plugin Sandbox executing code within restricted permission scopes."""

from __future__ import annotations

from typing import Any, Callable

from flock.plugins.exceptions import PluginSandboxError
from flock.plugins.models import PluginContext


class PluginSandbox:
    """Invokes callable plugin extensions within permission boundaries."""

    def __init__(self) -> None:
        pass

    def execute_in_sandbox(self, context: PluginContext, action: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Call plugin execution code.

        Raises:
            PluginSandboxError: If execution exceeds context permissions limits.
        """
        # Ensure plugin has execution permission coordinates
        if "EXECUTE" not in context.permissions:
            raise PluginSandboxError(f"Permission denied: Action requires 'EXECUTE' capability context.")

        try:
            return action(*args, **kwargs)
        except Exception as exc:
            raise PluginSandboxError(f"Plugin execution runtime error inside sandbox: {exc}") from exc
