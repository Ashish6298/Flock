"""SBOM generation, license auditing, and public API compatibility checkers."""

from __future__ import annotations

import hashlib
import threading
from typing import Dict, List, Any
from flock.release.finalization.exceptions import LicenseAuditError, SBOMGenerationError, PublicAPIViolationError
from flock.release.finalization.models import SBOMReport


class SBOMAndComplianceAuditor:
    """Manages active compilation of Software Bill of Materials and runs license compliance scans."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._licenses: Dict[str, str] = {}  # pkg -> license
        self._checksums: Dict[str, str] = {}  # file -> sha256

    def register_dependency(self, package: str, version: str, license_name: str) -> None:
        with self._lock:
            self._licenses[package] = license_name

    def generate_sbom(self, version: str) -> SBOMReport:
        """Compile a unified SBOM report for the target release.
        
        Raises:
            SBOMGenerationError: If no dependencies are registered.
        """
        with self._lock:
            if not self._licenses:
                raise SBOMGenerationError("No software dependencies registered to generate SBOM.")
                
            deps = []
            for pkg, lic in self._licenses.items():
                deps.append({"package": pkg, "version": "1.0.0", "license": lic})
                
            import time
            return SBOMReport(
                release_version=version,
                timestamp=time.time(),
                dependencies=deps,
                hashes=dict(self._checksums),
            )

    def audit_licenses(self, forbidden_licenses: List[str]) -> bool:
        """Scan registered licenses and assert no forbidden licensing names are present.
        
        Raises:
            LicenseAuditError: If non-compliant license types are detected.
        """
        with self._lock:
            for pkg, lic in self._licenses.items():
                if lic in forbidden_licenses:
                    raise LicenseAuditError(f"Dependency '{pkg}' uses non-compliant license '{lic}'.")
            return True

    def verify_api_compatibility(self, expected_symbols: List[str], actual_symbols: List[str]) -> bool:
        """Scan actual symbols to assert all mandatory expected symbols remain exported.
        
        Raises:
            PublicAPIViolationError: If public symbols are missing (breaking API compatibility).
        """
        with self._lock:
            missing = [sym for sym in expected_symbols if sym not in actual_symbols]
            if missing:
                raise PublicAPIViolationError(f"Public API compatibility broken! Missing symbols: {missing}")
            return True
