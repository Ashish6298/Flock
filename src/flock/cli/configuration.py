"""Configuration Manager tracks contexts."""

from __future__ import annotations

from typing import Dict

from flock.cli.exceptions import ContextSwitchError
from flock.cli.models import ClusterContext


class ConfigurationManager:
    """Manages active endpoint parameters maps."""

    def __init__(self) -> None:
        self.contexts: Dict[str, ClusterContext] = {}
        self.active_context_name: str = ""

    def add_context(self, context: ClusterContext) -> None:
        """Register context parameters."""
        self.contexts[context.context_name] = context
        if not self.active_context_name:
            self.active_context_name = context.context_name

    def switch_context(self, name: str) -> None:
        """Switch target endpoint.

        Raises:
            ContextSwitchError: If context name is not registered.
        """
        if name not in self.contexts:
            raise ContextSwitchError(f"Context '{name}' is not registered.")
        self.active_context_name = name
