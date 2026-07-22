"""Final Release Certification engine validating audits and compliance scores."""

from __future__ import annotations

import time
import threading
from flock.release.finalization.exceptions import CertificationError
from flock.release.finalization.models import ReleaseCertification


class ReleaseCertifier:
    """Certifies the General Availability release candidates and issues certificates."""

    def __init__(self) -> None:
        self._lock = threading.RLock()

    def certify_release(
        self,
        version: str,
        sbom_verified: bool,
        api_compatible: bool,
        license_clean: bool,
    ) -> ReleaseCertification:
        """Run validation rules and issue an official ReleaseCertification record.
        
        Raises:
            CertificationError: If any compliance check fails.
        """
        with self._lock:
            if not sbom_verified:
                raise CertificationError("Release certification failed: SBOM verification incomplete.")
            if not api_compatible:
                raise CertificationError("Release certification failed: API compatibility checks failed.")
            if not license_clean:
                raise CertificationError("Release certification failed: Non-compliant licenses detected.")
                
            return ReleaseCertification(
                release_version=version,
                certified_at=time.time(),
                sbom_verified=sbom_verified,
                api_compatible=api_compatible,
                license_clean=license_clean,
                compliance_score=100.0,
            )
