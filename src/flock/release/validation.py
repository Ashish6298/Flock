"""Release candidate dependency and configuration validators."""

from __future__ import annotations

import threading
from typing import Dict, List, Set
from flock.release.exceptions import DependencyVerificationError, ConfigurationValidationError


class IntegrationValidator:
    """Verifies subsystem configurations and validates startup dependencies ordering."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._dependencies: Dict[str, Set[str]] = {}

    def register_subsystem_dependency(self, subsystem: str, depends_on: str) -> None:
        """Register a dependency requirement (subsystem depends_on target)."""
        with self._lock:
            deps = self._dependencies.setdefault(subsystem, set())
            deps.add(depends_on)

    def validate_dependency_graph(self) -> None:
        """Verify startup dependency ordering graph for cycles.
        
        Raises:
            DependencyVerificationError: If a cyclic loop is detected.
        """
        with self._lock:
            # Standard cycle check using DFS
            visited: Dict[str, str] = {}  # name -> "visiting" or "visited"
            
            def dfs(node: str) -> None:
                visited[node] = "visiting"
                for neighbor in self._dependencies.get(node, []):
                    if visited.get(neighbor) == "visiting":
                        raise DependencyVerificationError(f"Subsystem dependency cycle detected on '{node}' -> '{neighbor}'.")
                    if neighbor not in visited:
                        dfs(neighbor)
                visited[node] = "visited"
                
            for node in list(self._dependencies.keys()):
                if node not in visited:
                    dfs(node)

    def validate_configuration(self, config: Dict[str, str], required_keys: List[str]) -> None:
        """Assert configuration overrides contain mandatory keys.
        
        Raises:
            ConfigurationValidationError: If mandatory parameters are missing.
        """
        with self._lock:
            for rk in required_keys:
                if rk not in config or not config[rk]:
                    raise ConfigurationValidationError(f"Required configuration parameter '{rk}' is missing or empty.")
