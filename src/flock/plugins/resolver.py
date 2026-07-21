"""Plugin Dependency Resolver resolving dependency chains."""

from __future__ import annotations

from typing import Dict, List, Set

from flock.plugins.exceptions import PluginDependencyError
from flock.plugins.models import PluginManifest


class PluginDependencyResolver:
    """Sorts dynamic modules topologically and asserts compatibility layers."""

    def __init__(self) -> None:
        pass

    def resolve_dependencies(self, manifests: List[PluginManifest]) -> List[str]:
        """Perform Kahn's topological sort on plugin dependency mappings.

        Raises:
            PluginDependencyError: If circular dependencies are detected.
        """
        nodes = {m.plugin_id for m in manifests}
        adj: Dict[str, List[str]] = {m.plugin_id: [] for m in manifests}
        in_degree: Dict[str, int] = {m.plugin_id: 0 for m in manifests}

        # Index maps
        manifest_map = {m.plugin_id: m for m in manifests}

        for m in manifests:
            for dep in m.dependencies:
                # If dependency belongs to the set, build edges
                if dep in nodes:
                    adj[dep].append(m.plugin_id)
                    in_degree[m.plugin_id] += 1

        queue = [n for n in nodes if in_degree[n] == 0]
        order: List[str] = []

        while queue:
            curr = queue.pop(0)
            order.append(curr)
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(nodes):
            raise PluginDependencyError("Circular dependency detected in plugin list.")

        return order
