"""Plugin Sandbox executing code within restricted permission scopes."""

from __future__ import annotations

from typing import Any, Callable

from flock.plugins.exceptions import PluginSandboxError
from flock.plugins.models import PluginContext, PermissionScope
from flock.plugins.security import PluginSecurityManager


class PluginSandbox:
    """Invokes callable plugin extensions within permission boundaries."""

    def __init__(self, security_manager: PluginSecurityManager) -> None:
        self._security = security_manager

    def execute_in_sandbox(
        self,
        context: PluginContext,
        action: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Call plugin execution code.

        Raises:
            PluginSandboxError: If execution exceeds context permissions limits.
        """
        # Ensure plugin has execution permission coordinates
        # Check permissions in security manager using the EXECUTE scope
        plugin_id = context.plugin_id
        
        # In Phase 4, we perform formal permission check on the execution scope.
        if not self._security.check_permission(plugin_id, PermissionScope.EXECUTE, "execution_context"):
            raise PluginSandboxError("Permission denied: Action requires 'EXECUTE' capability context.")

        try:
            return action(*args, **kwargs)
        except Exception as exc:
            raise PluginSandboxError(f"Plugin execution runtime error inside sandbox: {exc}") from exc
