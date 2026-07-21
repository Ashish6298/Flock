"""Interactive REPL Engine."""

from __future__ import annotations

from typing import Dict


class ReplEngine:
    """Maintains variables state context for prompt terminals sessions."""

    def __init__(self) -> None:
        self.variables: Dict[str, str] = {}

    def set_variable(self, name: str, value: str) -> None:
        """Assign variable value."""
        self.variables[name] = value

    def get_variable(self, name: str) -> str:
        """Retrieve variable value."""
        return self.variables.get(name, "")
