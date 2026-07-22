"""GA Finalization Coordinator linking compliance scanners, certifiers, and documentation builders."""

from __future__ import annotations

import threading
from flock.release.finalization.audits import SBOMAndComplianceAuditor
from flock.release.finalization.certification import ReleaseCertifier
from flock.release.finalization.notes import ReleaseNotesBuilder
from flock.release.finalization.audit import GAAuditLogger


class GAFinalizationCoordinator:
    """Consolidates SBOM compliances, release certifiers, and notes builders."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        
        # Initialize finalization subsystems
        self.auditor = SBOMAndComplianceAuditor()
        self.certifier = ReleaseCertifier()
        self.notes = ReleaseNotesBuilder()
        self.audit = GAAuditLogger()
