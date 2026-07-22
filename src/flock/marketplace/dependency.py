"""Extension packages dependency solver and version matchers."""

from __future__ import annotations

import re
import threading
from typing import Dict, List, Set
from flock.marketplace.exceptions import CompatibilityError


class DependencyResolver:
    """Resolves and validates transitive dependencies across extension packages."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # package_id -> list of version strings available
        self._versions_catalog: Dict[str, List[str]] = {}

    def register_package_version(self, package_id: str, version: str) -> None:
        with self._lock:
            versions = self._versions_catalog.setdefault(package_id, [])
            if version not in versions:
                versions.append(version)

    def resolve_dependencies(self, dependencies: List[str]) -> List[str]:
        """Validate if dependencies constraints are satisfied by available catalog versions.
        
        Args:
            dependencies: List of dependency rules, e.g. ["db-connector>=1.0.0", "scheduler"]
            
        Raises:
            CompatibilityError: If a dependency rule is not satisfied.
        """
        with self._lock:
            resolved = []
            for dep in dependencies:
                # Parse rule, e.g. db-connector>=1.0.0
                match = re.match(r"^([a-zA-Z0-9\-]+)(>=|>|<=|<|==)?([0-9\.]+)?$", dep.strip())
                if not match:
                    raise CompatibilityError(f"Invalid dependency constraint format: {dep}")
                    
                dep_id, op, target_ver = match.groups()
                
                # Check if package exists
                if dep_id not in self._versions_catalog:
                    raise CompatibilityError(f"Dependency package '{dep_id}' is not registered.")
                    
                avail_versions = self._versions_catalog[dep_id]
                
                # If no operator is defined, any version is ok
                if not op or not target_ver:
                    resolved.append(f"{dep_id}:{avail_versions[-1]}")
                    continue
                    
                # Find matching version
                matched_ver = None
                for ver in sorted(avail_versions, reverse=True):
                    # Simple comparison logic
                    if op == ">=":
                        if ver >= target_ver:
                            matched_ver = ver
                            break
                    elif op == "==":
                        if ver == target_ver:
                            matched_ver = ver
                            break
                            
                if not matched_ver:
                    raise CompatibilityError(f"No matching version found for constraint: {dep}")
                    
                resolved.append(f"{dep_id}:{matched_ver}")
            return resolved
