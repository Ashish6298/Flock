"""Unit tests for Phase 42 GA Release, Final Stabilization & Enterprise Certification Subsystem."""

import time
import pytest
from unittest.mock import MagicMock, AsyncMock

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.protocol.packet import MessageType
from flock.release.finalization.exceptions import (
    GAError,
    LicenseAuditError,
    SBOMGenerationError,
    PublicAPIViolationError,
    CertificationError,
)
from flock.release.finalization.models import (
    SBOMReport,
    ReleaseCertification,
    BenchmarkSummary,
)
from flock.release.finalization.audits import SBOMAndComplianceAuditor
from flock.release.finalization.certification import ReleaseCertifier
from flock.release.finalization.notes import ReleaseNotesBuilder
from flock.release.finalization.audit import GAAuditLogger
from flock.release.finalization.coordinator import GAFinalizationCoordinator
from flock.release.finalization.service import GAFinalizationService


# -----------------------------------------------------------------------------
# Audits, SBOM & License scans Tests
# -----------------------------------------------------------------------------

def test_sbom_and_licenses() -> None:
    auditor = SBOMAndComplianceAuditor()
    
    auditor.register_dependency("pydantic", "2.6.1", "MIT")
    auditor.register_dependency("structlog", "24.1.0", "Apache-2.0")
    
    # SBOM Gen
    report = auditor.generate_sbom("1.0.0")
    assert report.release_version == "1.0.0"
    assert len(report.dependencies) == 2
    
    # License scans
    assert auditor.audit_licenses(["GPLv3"]) is True
    with pytest.raises(LicenseAuditError):
        auditor.audit_licenses(["MIT"])


# -----------------------------------------------------------------------------
# API Compatibility Tests
# -----------------------------------------------------------------------------

def test_api_compatibility() -> None:
    auditor = SBOMAndComplianceAuditor()
    
    expected = ["RaftConsensus", "DistributedDataGrid", "PolicyService"]
    actual = ["RaftConsensus", "DistributedDataGrid", "PolicyService", "ExtraSymbol"]
    
    assert auditor.verify_api_compatibility(expected, actual) is True
    
    # Broken API compatibility
    broken_actual = ["RaftConsensus", "PolicyService"]
    with pytest.raises(PublicAPIViolationError):
        auditor.verify_api_compatibility(expected, broken_actual)


# -----------------------------------------------------------------------------
# Release Certifier & Documentation Tests
# -----------------------------------------------------------------------------

def test_certifier_and_notes() -> None:
    certifier = ReleaseCertifier()
    notes_builder = ReleaseNotesBuilder()
    
    cert = certifier.certify_release(
        version="1.0.0",
        sbom_verified=True,
        api_compatible=True,
        license_clean=True,
    )
    assert cert.compliance_score == 100.0
    
    # Check failure
    with pytest.raises(CertificationError):
        certifier.certify_release(
            version="1.0.0",
            sbom_verified=False,
            api_compatible=True,
            license_clean=True,
        )
        
    # Notes compilation
    benchmarks = BenchmarkSummary(
        total_tx_processed=50000,
        avg_latency_ms=1.2,
        raft_consensus_status="healthy",
    )
    text = notes_builder.compile_release_notes("1.0.0", benchmarks)
    assert "total_tx_processed" not in text  # Value is formatted
    assert "50000" in text


# -----------------------------------------------------------------------------
# GAFinalization Service Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ga_service_integration() -> None:
    bus = MagicMock(spec=MessageBus)
    bus.router = MagicMock()
    bus.send = AsyncMock()
    
    events = EventBus()
    event_list = []
    
    async def on_init(data: dict) -> None: # type: ignore[type-arg]
        event_list.append(data)
        
    events.subscribe("ga.initialized", on_init)
    
    service = GAFinalizationService(bus, events)
    await service.start()
    
    assert service._running is True
    assert len(event_list) == 1
    assert service._bus.router.register.call_count == 1
    
    await service.stop()
    assert service._running is False
