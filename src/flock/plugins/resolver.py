"""Plugin Dependency Resolver resolving dependency chains and version constraints.

Implements topological sorting, semantic version validation, cycle detection,
and optional dependency management.
"""

from __future__ import annotations

import re
from typing import Dict, List, Set, Tuple

from flock.plugins.exceptions import (
    PluginDependencyResolutionError,
    PluginMissingDependencyError,
    PluginDependencyVersionConflictError,
    PluginCircularDependencyError,
    PluginInvalidDependencySpecError,
)
from flock.plugins.models import PluginManifest
from flock.plugins.dependency_models import (
    DependencyConstraint,
    DependencySpec,
    DependencyResolutionResult,
    DependencyInstallationPlan,
    InstallationStep,
    PlanStepType,
    VersionOperator,
)


class PluginDependencyResolver:
    """Sorts dynamic modules topologically and asserts compatibility layers."""

    def __init__(self) -> None:
        pass

    @staticmethod
    def parse_version(version_str: str) -> Tuple[int, int, int, str]:
        """Parses a semver version string into (major, minor, patch, prerelease)."""
        version_str = version_str.strip()
        parts = version_str.split("-", 1)
        digits = parts[0].split(".")
        if len(digits) == 1:
            digits_str = f"{digits[0]}.0.0"
        elif len(digits) == 2:
            digits_str = f"{digits[0]}.{digits[1]}.0"
        else:
            digits_str = parts[0]
        if len(parts) > 1:
            version_str = f"{digits_str}-{parts[1]}"
        else:
            version_str = digits_str

        match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.]+))?$", version_str)
        if not match:
            raise ValueError(f"Invalid semver: {version_str}")
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        prerelease = match.group(4) or ""
        return major, minor, patch, prerelease

    @classmethod
    def compare_versions(cls, v1_str: str, op: VersionOperator, v2_str: str) -> bool:
        """Compares v1 against v2 according to the given operator."""
        try:
            major1, minor1, patch1, pre1 = cls.parse_version(v1_str)
            major2, minor2, patch2, pre2 = cls.parse_version(v2_str)
        except ValueError:
            return False

        t1 = (major1, minor1, patch1)
        t2 = (major2, minor2, patch2)

        if op == VersionOperator.EQ:
            return t1 == t2 and pre1 == pre2
        elif op == VersionOperator.NE:
            return not (t1 == t2 and pre1 == pre2)
        elif op == VersionOperator.GT:
            if t1 > t2:
                return True
            if t1 == t2 and pre1 and not pre2:
                return False
            if t1 == t2 and not pre1 and pre2:
                return True
            if t1 == t2 and pre1 and pre2:
                return pre1 > pre2
            return False
        elif op == VersionOperator.GTE:
            return cls.compare_versions(v1_str, VersionOperator.GT, v2_str) or (t1 == t2 and pre1 == pre2)
        elif op == VersionOperator.LT:
            return not cls.compare_versions(v1_str, VersionOperator.GTE, v2_str)
        elif op == VersionOperator.LTE:
            return not cls.compare_versions(v1_str, VersionOperator.GT, v2_str)
        elif op == VersionOperator.TILDE_ARROW:
            if not (cls.compare_versions(v1_str, VersionOperator.GTE, v2_str)):
                return False
            v2_clean = v2_str.strip()
            if "-" in v2_clean:
                v2_clean = v2_clean.split("-")[0]
            v2_parts = v2_clean.split(".")
            if len(v2_parts) >= 3:
                return major1 == major2 and minor1 == minor2
            else:
                return major1 == major2
        return False

    @classmethod
    def parse_dependency_spec(cls, spec_str: str, is_optional: bool = False) -> DependencySpec:
        """Parses a dependency specification string into a DependencySpec model."""
        spec_str = spec_str.strip()
        opt = is_optional
        if spec_str.endswith("?"):
            opt = True
            spec_str = spec_str[:-1].strip()

        match = re.match(r"^([a-zA-Z0-9_\-\.]+)(.*)$", spec_str)
        if not match:
            raise PluginInvalidDependencySpecError(f"Invalid dependency spec: '{spec_str}'")

        plugin_id = match.group(1)
        constraint_str = match.group(2).strip()

        constraints: List[DependencyConstraint] = []
        if constraint_str:
            parts = [p.strip() for p in constraint_str.split(",") if p.strip()]
            for part in parts:
                op_match = re.match(r"^(==|!=|>=|<=|>|<|~>)\s*([a-zA-Z0-9_\-\.\+]+)$", part)
                if not op_match:
                    raise PluginInvalidDependencySpecError(
                        f"Invalid constraint '{part}' in spec '{spec_str}'"
                    )
                op_val = VersionOperator(op_match.group(1))
                version_val = op_match.group(2)
                constraints.append(DependencyConstraint(operator=op_val, version=version_val))

        return DependencySpec(
            plugin_id=plugin_id,
            is_optional=opt,
            constraints=constraints,
        )

    def resolve_dependencies(self, manifests: List[PluginManifest]) -> List[str]:
        """Perform topological sort on plugin dependency mappings.

        Raises:
            PluginDependencyError: If dependency resolution fails (cycles or missing required dependencies).
        """
        result = self.resolve_dependencies_extended(manifests)
        if not result.success:
            if result.version_conflicts and "system" in result.version_conflicts:
                if "Circular dependency" in result.version_conflicts["system"]:
                    raise PluginCircularDependencyError(result.version_conflicts["system"])
            if result.missing_dependencies:
                raise PluginMissingDependencyError(
                    f"Missing dependencies: {', '.join(result.missing_dependencies)}"
                )
            if result.version_conflicts:
                conflict_details = [f"{k}: {v}" for k, v in result.version_conflicts.items()]
                raise PluginDependencyVersionConflictError(
                    f"Version conflicts: {'; '.join(conflict_details)}"
                )
            raise PluginDependencyResolutionError("Dependency resolution failed.")

        return result.resolved_order

    def resolve_dependencies_extended(self, manifests: List[PluginManifest]) -> DependencyResolutionResult:
        """Resolves dependencies and returns a detailed status/result without raising exceptions."""
        manifest_map = {m.plugin_id: m for m in manifests}
        
        # Parse all specs
        specs_map: Dict[str, List[DependencySpec]] = {}
        for m in manifests:
            specs: List[DependencySpec] = []
            for dep in m.dependencies:
                try:
                    specs.append(self.parse_dependency_spec(dep, is_optional=False))
                except PluginInvalidDependencySpecError as exc:
                    return DependencyResolutionResult(
                        success=False,
                        missing_dependencies=[],
                        version_conflicts={m.plugin_id: str(exc)},
                    )
            for dep in m.optional_dependencies:
                try:
                    specs.append(self.parse_dependency_spec(dep, is_optional=True))
                except PluginInvalidDependencySpecError as exc:
                    return DependencyResolutionResult(
                        success=False,
                        missing_dependencies=[],
                        version_conflicts={m.plugin_id: str(exc)},
                    )
            specs_map[m.plugin_id] = specs

        missing_deps: Set[str] = set()
        version_conflicts: Dict[str, str] = {}
        unresolved_opt: Set[str] = set()

        # Build adjacency lists and degrees
        # E.g. A depends on B means edge B -> A (B must be loaded before A)
        adj: Dict[str, List[str]] = {m.plugin_id: [] for m in manifests}
        in_degree: Dict[str, int] = {m.plugin_id: 0 for m in manifests}

        # Track valid dependencies for sorting
        valid_edges: List[Tuple[str, str]] = []

        for m in manifests:
            for spec in specs_map[m.plugin_id]:
                dep_id = spec.plugin_id
                if dep_id not in manifest_map:
                    if spec.is_optional:
                        unresolved_opt.add(dep_id)
                        continue
                    else:
                        missing_deps.add(dep_id)
                        continue

                # Validate constraints
                dep_manifest = manifest_map[dep_id]
                conflict_found = False
                for constraint in spec.constraints:
                    if not self.compare_versions(dep_manifest.version, constraint.operator, constraint.version):
                        err_msg = (
                            f"Plugin '{dep_id}' version '{dep_manifest.version}' "
                            f"does not satisfy constraint '{constraint.operator.value}{constraint.version}'"
                        )
                        version_conflicts[m.plugin_id] = err_msg
                        conflict_found = True
                        break
                
                if not conflict_found:
                    valid_edges.append((dep_id, m.plugin_id))

        if missing_deps or version_conflicts:
            return DependencyResolutionResult(
                success=False,
                missing_dependencies=sorted(list(missing_deps)),
                version_conflicts=version_conflicts,
                unresolved_optional=sorted(list(unresolved_opt)),
            )

        # Build the graph from valid edges
        for u, v in valid_edges:
            adj[u].append(v)
            in_degree[v] += 1

        # Kahn's algorithm
        # To make sorting deterministic, sort nodes alphabetically when degrees are equal
        queue = sorted([n for n in manifest_map if in_degree[n] == 0])
        order: List[str] = []

        while queue:
            curr = queue.pop(0)
            order.append(curr)
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
            # Re-sort queue to maintain deterministic order
            queue.sort()

        if len(order) != len(manifest_map):
            # Circular dependency detected
            # We raise PluginCircularDependencyError directly in resolve_dependencies
            # Or if called via extended API, we can report success=False
            return DependencyResolutionResult(
                success=False,
                missing_dependencies=[],
                version_conflicts={"system": "Circular dependency detected"},
            )

        return DependencyResolutionResult(
            success=True,
            resolved_order=order,
            unresolved_optional=sorted(list(unresolved_opt)),
        )

    def generate_installation_plan(self, manifests: List[PluginManifest]) -> DependencyInstallationPlan:
        """Generates a step-by-step reproducible installation plan."""
        # Resolve order first. This raises appropriate errors if resolution fails.
        order = self.resolve_dependencies(manifests)
        
        steps: List[InstallationStep] = []
        for plugin_id in order:
            steps.append(InstallationStep(step_type=PlanStepType.REGISTER, plugin_id=plugin_id))
            steps.append(InstallationStep(step_type=PlanStepType.VALIDATE, plugin_id=plugin_id))
            steps.append(InstallationStep(step_type=PlanStepType.ACTIVATE, plugin_id=plugin_id))
            
        return DependencyInstallationPlan(steps=steps)
