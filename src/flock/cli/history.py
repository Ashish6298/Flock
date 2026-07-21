"""History Logger preserving command executions."""

from __future__ import annotations

from typing import List


class HistoryLogger:
    """Appends elements to local buffer storage lists."""

    def __init__(self) -> None:
        self.history: List[str] = []

    def append_command(self, line: str) -> None:
        """Add to history list."""
        self.history.append(line)

    def get_lines(self) -> List[str]:
        """Retrieve historical log entries."""
        return list(self.history)
