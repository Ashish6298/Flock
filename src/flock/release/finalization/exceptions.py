"""Typed exceptions for General Availability (GA) finalization, SBOM audits, and certification checks."""

from flock.exceptions import FlockError

class GAError(FlockError):
    """Base exception for all GA stabilization and finalization errors."""
    pass

class LicenseAuditError(GAError):
    """Raised when repository license verification audits detect compliance issues."""
    pass

class SBOMGenerationError(GAError):
    """Raised when parsing system packages or writing SBOM reports fails."""
    pass

class PublicAPIViolationError(GAError):
    """Raised when signature checks find public API compatibility violations."""
    pass

class CertificationError(GAError):
    """Raised when release candidate fails certification score thresholds."""
    pass
