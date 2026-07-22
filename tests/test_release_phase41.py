"""Unit tests for Phase 41 Enterprise Production Readiness, System Integration & Release Candidate Framework Subsystem."""

import time
import pytest
from unittest.mock import MagicMock, AsyncMock

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.protocol.packet import MessageType
from flock.release.exceptions import (
    ReleaseError,
    DependencyVerificationError,
    ConfigurationValidationError,
    SubsystemLifecycleError,
)
from flock.release.models import (
    ReleaseManifest,
    SubsystemStatus,
)
from flock.release.manifests import ReleaseManifestRegistry
from flock.release.validation import IntegrationValidator
from flock.release.lifecycle import SubsystemLifecycleCoordinator
from flock.release.readiness import ProductionReadinessAssessor
from flock.release.diagnostics import ReleaseDiagnostics
from flock.release.audit import ReleaseAuditLogger
from flock.release.coordinator import ReleaseCoordinator
from flock.release.service import ReleaseService


# -----------------------------------------------------------------------------
# Manifests & Diagnostics Tests
# -----------------------------------------------------------------------------

def test_manifests_and_diagnostics() -> None:
    registry = ReleaseManifestRegistry()
    diagnostics = ReleaseDiagnostics()
    
    manifest = ReleaseManifest(
        version="1.0.0-rc1",
        commit_sha="abc12345",
        built_at=time.time(),
        features_included=["Consensus", "Federation", "Policy"],
        metadata={"builder": "CI"},
    )
    registry.register_release_candidate(manifest)
    assert registry.get_release_candidate("1.0.0-rc1").commit_sha == "abc12345"
    
    # Check diagnostics
    info = diagnostics.inspect_environment()
    assert info["status"] == "healthy"
    assert info["api_version"] == "1.0.0-rc1"


# -----------------------------------------------------------------------------
# Dependencies & Configuration Tests
# -----------------------------------------------------------------------------

def test_dependencies_and_configuration() -> None:
    val = IntegrationValidator()
    
    val.register_subsystem_dependency("Consensus", "Networking")
    val.register_subsystem_dependency("Storage", "Consensus")
    
    # Graph verify should pass
    val.validate_dependency_graph()
    
    # Introduce cycle
    val.register_subsystem_dependency("Networking", "Storage")
    with pytest.raises(DependencyVerificationError):
        val.validate_dependency_graph()
        
    # Configuration mandatory validation
    val.validate_configuration({"host": "127.0.0.1", "port": "8080"}, ["host", "port"])
    with pytest.raises(ConfigurationValidationError):
        val.validate_configuration({"host": "127.0.0.1"}, ["host", "port"])


# -----------------------------------------------------------------------------
# Lifecycle & Readiness Assessor Tests
# -----------------------------------------------------------------------------

def test_lifecycle_and_readiness_assessor() -> None:
    lc = SubsystemLifecycleCoordinator()
    assessor = ProductionReadinessAssessor()
    
    lc.register_subsystem("Consensus")
    lc.register_subsystem("Storage")
    
    lc.set_subsystem_state("Consensus", "running")
    lc.set_subsystem_state("Storage", "running")
    
    subsystems = lc.list_subsystems()
    report = assessor.assess_readiness("1.0.0-rc1", True, True, subsystems)
    
    assert report.dependency_status is True
    assert report.configuration_status is True
    assert report.subsystems_healthy is True
    assert report.overall_readiness_score == 100.0
    
    # Set one subsystem degraded
    lc.set_subsystem_state("Storage", "degraded")
    report_deg = assessor.assess_readiness("1.0.0-rc1", True, True, lc.list_subsystems())
    assert report_deg.subsystems_healthy is False
    assert report_deg.overall_readiness_score == 66.6


# -----------------------------------------------------------------------------
# Release Service Integration Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_release_service_integration() -> None:
    bus = MagicMock(spec=MessageBus)
    bus.router = MagicMock()
    bus.send = AsyncMock()
    
    events = EventBus()
    event_list = []
    
    async def on_init(data: dict) -> None: # type: ignore[type-arg]
        event_list.append(data)
        
    events.subscribe("release.initialized", on_init)
    
    service = ReleaseService(bus, events)
    await service.start()
    
    assert service._running is True
    assert len(event_list) == 1
    assert service._bus.router.register.call_count == 1
    
    await service.stop()
    assert service._running is False
