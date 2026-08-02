"""Unit tests for Phase 3 Plugin Dependency Management & Resolution."""

from __future__ import annotations

import threading
import pytest
from typing import List

from flock.plugins.exceptions import (
    PluginDependencyResolutionError,
    PluginMissingDependencyError,
    PluginDependencyVersionConflictError,
    PluginCircularDependencyError,
    PluginInvalidDependencySpecError,
)
from flock.plugins.models import PluginManifest
from flock.plugins.registry import PluginRegistry
from flock.plugins.resolver import PluginDependencyResolver
from flock.plugins.dependency_models import (
    VersionOperator,
    DependencyConstraint,
    DependencySpec,
    DependencyResolutionResult,
    PlanStepType,
    InstallationStep,
    DependencyInstallationPlan,
)


def _manifest(plugin_id: str, version: str, deps: List[str] = None, opt_deps: List[str] = None) -> PluginManifest:
    return PluginManifest(
        plugin_id=plugin_id,
        name=plugin_id.upper(),
        version=version,
        author="tester",
        dependencies=deps or [],
        optional_dependencies=opt_deps or [],
    )


# ---------------------------------------------------------------------------
# Dependency Spec & Operator Verification
# ---------------------------------------------------------------------------


class TestDependencySpecAndComparison:
    def test_version_parsing(self) -> None:
        major, minor, patch, pre = PluginDependencyResolver.parse_version("1.2.3-alpha.1")
        assert (major, minor, patch) == (1, 2, 3)
        assert pre == "alpha.1"

        major, minor, patch, pre = PluginDependencyResolver.parse_version("0.1.0")
        assert (major, minor, patch) == (0, 1, 0)
        assert pre == ""

        with pytest.raises(ValueError):
            PluginDependencyResolver.parse_version("invalid-version")

    def test_version_comparisons(self) -> None:
        comp = PluginDependencyResolver.compare_versions
        assert comp("1.2.0", VersionOperator.EQ, "1.2.0")
        assert comp("1.2.0", VersionOperator.NE, "1.2.1")
        assert comp("1.3.0", VersionOperator.GT, "1.2.9")
        assert comp("1.2.5", VersionOperator.GTE, "1.2.5")
        assert comp("1.1.0", VersionOperator.LT, "1.2.0")
        assert comp("1.0.0", VersionOperator.LTE, "1.0.0")

        # Tilde-arrow operator tests (~>)
        assert comp("1.2.3", VersionOperator.TILDE_ARROW, "1.2.0")
        assert not comp("1.3.0", VersionOperator.TILDE_ARROW, "1.2.0")
        assert comp("2.5.0", VersionOperator.TILDE_ARROW, "2")
        assert not comp("3.0.0", VersionOperator.TILDE_ARROW, "2")

    def test_parse_dependency_spec(self) -> None:
        parse = PluginDependencyResolver.parse_dependency_spec
        spec = parse("telemetry-exporter>=1.0.0,!=1.1.0")
        assert spec.plugin_id == "telemetry-exporter"
        assert spec.is_optional is False
        assert len(spec.constraints) == 2
        assert spec.constraints[0].operator == VersionOperator.GTE
        assert spec.constraints[0].version == "1.0.0"
        assert spec.constraints[1].operator == VersionOperator.NE
        assert spec.constraints[1].version == "1.1.0"

        spec_opt = parse("auth-service<=2.0.0?")
        assert spec_opt.plugin_id == "auth-service"
        assert spec_opt.is_optional is True
        assert len(spec_opt.constraints) == 1
        assert spec_opt.constraints[0].operator == VersionOperator.LTE
        assert spec_opt.constraints[0].version == "2.0.0"

        with pytest.raises(PluginInvalidDependencySpecError):
            parse("!!!invalid_spec!!!")


# ---------------------------------------------------------------------------
# Resolution Engine Verification
# ---------------------------------------------------------------------------


class TestDependencyResolutionEngine:
    def test_successful_resolution_happy_path(self) -> None:
        resolver = PluginDependencyResolver()
        m1 = _manifest("db-driver", "1.0.0")
        m2 = _manifest("cache-service", "1.1.0", deps=["db-driver>=1.0.0"])
        m3 = _manifest("api-gateway", "2.0.0", deps=["cache-service~>1.1"])

        order = resolver.resolve_dependencies([m1, m2, m3])
        assert order == ["db-driver", "cache-service", "api-gateway"]

    def test_alphabetical_determinism(self) -> None:
        resolver = PluginDependencyResolver()
        # Z and A have zero dependencies. Resolved order should sort A before Z
        m1 = _manifest("z-plugin", "1.0.0")
        m2 = _manifest("a-plugin", "1.0.0")
        order = resolver.resolve_dependencies([m1, m2])
        assert order == ["a-plugin", "z-plugin"]

    def test_missing_dependency(self) -> None:
        resolver = PluginDependencyResolver()
        m1 = _manifest("app-service", "1.0.0", deps=["missing-service"])
        with pytest.raises(PluginMissingDependencyError) as excinfo:
            resolver.resolve_dependencies([m1])
        assert "Missing dependencies: missing-service" in str(excinfo.value)

    def test_version_conflict(self) -> None:
        resolver = PluginDependencyResolver()
        m1 = _manifest("db-driver", "0.9.0")
        m2 = _manifest("cache-service", "1.0.0", deps=["db-driver>=1.0.0"])
        with pytest.raises(PluginDependencyVersionConflictError) as excinfo:
            resolver.resolve_dependencies([m1, m2])
        assert "Version conflicts" in str(excinfo.value)

    def test_circular_dependency(self) -> None:
        resolver = PluginDependencyResolver()
        m1 = _manifest("p1", "1.0.0", deps=["p2"])
        m2 = _manifest("p2", "1.0.0", deps=["p1"])
        with pytest.raises(PluginCircularDependencyError):
            resolver.resolve_dependencies([m1, m2])

    def test_optional_dependencies(self) -> None:
        resolver = PluginDependencyResolver()
        # Optional present: included in resolution order
        m1 = _manifest("opt-plugin", "1.0.0")
        m2 = _manifest("main-plugin", "1.0.0", opt_deps=["opt-plugin"])
        order = resolver.resolve_dependencies([m1, m2])
        assert order == ["opt-plugin", "main-plugin"]

        # Optional missing: omitted, resolution succeeds
        m3 = _manifest("main-plugin-2", "1.0.0", opt_deps=["absent-plugin"])
        order2 = resolver.resolve_dependencies([m3])
        assert order2 == ["main-plugin-2"]


# ---------------------------------------------------------------------------
# Installation Plan Generation
# ---------------------------------------------------------------------------


class TestInstallationPlanGeneration:
    def test_generate_installation_plan(self) -> None:
        resolver = PluginDependencyResolver()
        m1 = _manifest("db-driver", "1.0.0")
        m2 = _manifest("cache-service", "1.1.0", deps=["db-driver"])
        
        plan = resolver.generate_installation_plan([m1, m2])
        assert len(plan.steps) == 6
        assert plan.steps[0].step_type == PlanStepType.REGISTER
        assert plan.steps[0].plugin_id == "db-driver"
        assert plan.steps[1].step_type == PlanStepType.VALIDATE
        assert plan.steps[1].plugin_id == "db-driver"
        assert plan.steps[2].step_type == PlanStepType.ACTIVATE
        assert plan.steps[2].plugin_id == "db-driver"
        assert plan.steps[3].step_type == PlanStepType.REGISTER
        assert plan.steps[3].plugin_id == "cache-service"


# ---------------------------------------------------------------------------
# Thread Safety Verification
# ---------------------------------------------------------------------------


class TestRegistryThreadSafetyIntegration:
    def test_concurrent_registration_and_validation(self) -> None:
        registry = PluginRegistry()
        barrier = threading.Barrier(3)
        exceptions: List[Exception] = []

        def worker1() -> None:
            barrier.wait()
            try:
                registry.register_plugin(_manifest("p1", "1.0.0"))
            except Exception as exc:
                exceptions.append(exc)

        def worker2() -> None:
            barrier.wait()
            try:
                registry.register_plugin(_manifest("p2", "1.0.0", deps=["p1"]))
            except Exception as exc:
                exceptions.append(exc)

        def worker3() -> None:
            barrier.wait()
            try:
                registry.validate_registry_dependencies()
            except Exception as exc:
                # Validation might fail depending on race, but shouldn't deadlock
                pass

        threads = [
            threading.Thread(target=worker1),
            threading.Thread(target=worker2),
            threading.Thread(target=worker3),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(exceptions) == 0
