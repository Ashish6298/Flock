"""Versioning Manager validating release weight routes."""

from __future__ import annotations

import random
from typing import Dict

from flock.functions.exceptions import FunctionValidationError


class FunctionVersionManager:
    """Computes traffic splitting matches across function version targets."""

    def __init__(self) -> None:
        pass

    def resolve_version_route(self, splits: Dict[str, float]) -> str:
        """Select version string using weighted random criteria.

        Raises:
            FunctionValidationError: If split weights are invalid.
        """
        if not splits:
            raise FunctionValidationError("Traffic split map cannot be empty.")

        total_weight = sum(splits.values())
        if not (99.0 <= total_weight <= 101.0):
            raise FunctionValidationError("Traffic split weights must sum to approximately 100.")

        val = random.uniform(0, 100.0)
        current = 0.0
        for version, weight in splits.items():
            current += weight
            if val <= current:
                return version

        return list(splits.keys())[0]
