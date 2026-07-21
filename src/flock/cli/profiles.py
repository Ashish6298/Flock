"""Profile Manager managing user identity contexts."""

from __future__ import annotations

from typing import Dict

from flock.cli.exceptions import ProfileNotFoundError
from flock.cli.models import ProfileDefinition


class ProfileManager:
    """Controls roles assignments permissions templates."""

    def __init__(self) -> None:
        self.profiles: Dict[str, ProfileDefinition] = {}
        self.active_profile_name: str = ""

    def add_profile(self, name: str, definition: ProfileDefinition) -> None:
        """Register identity definition."""
        self.profiles[name] = definition
        if not self.active_profile_name:
            self.active_profile_name = name

    def switch_profile(self, name: str) -> None:
        """Switch operational identity.

        Raises:
            ProfileNotFoundError: If identity name is not registered.
        """
        if name not in self.profiles:
            raise ProfileNotFoundError(f"Identity profile '{name}' not found.")
        self.active_profile_name = name
