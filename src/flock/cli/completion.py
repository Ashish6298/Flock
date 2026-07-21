"""Auto-Completion Engine."""

from __future__ import annotations

from typing import List

from flock.cli.models import CompletionCandidate


class AutoCompleteEngine:
    """Matches available action names against prefix inputs."""

    def __init__(self, candidates: List[str]) -> None:
        self.candidates = candidates

    def get_completions(self, prefix: str) -> List[CompletionCandidate]:
        """Filter matching inputs prefix."""
        matches = []
        for name in self.candidates:
            if name.startswith(prefix):
                matches.append(CompletionCandidate(value=name, display=name))
        return matches
