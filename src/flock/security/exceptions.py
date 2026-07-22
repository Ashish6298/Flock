"""Security Exceptions."""

from flock.exceptions import FlockError

class SecurityError(FlockError):
    """Base exception for all security operations."""
    pass

class AuthenticationError(SecurityError):
    """Raised when authentication credentials verification fails."""
    pass

class AuthorizationError(SecurityError):
    """Raised when access rules deny operation permissions."""
    pass

class SignatureVerificationError(SecurityError):
    """Raised when signature hashing validation fails."""
    pass

class TokenExpiredError(SecurityError):
    """Raised when access token expiry check fails."""
    pass

class KeyRotationError(SecurityError):
    """Raised when cryptographic key rotation update fails."""
    pass

class PolicyEvaluationError(SecurityError):
    """Raised when security policy evaluation fails or is blocked."""
    pass

class CertificateValidationError(SecurityError):
    """Raised when x509 or trust chain validation fails."""
    pass

class SecretStorageError(SecurityError):
    """Raised when secret retrieval, writing, or provider access fails."""
    pass

class TamperDetectionError(SecurityError):
    """Raised when audit log or data tampering is detected."""
    pass

class ComplianceControlError(SecurityError):
    """Raised when a compliance rule or control validation fails."""
    pass

class IntrusionDetectionAlert(SecurityError):
    """Raised/triggered when suspicious behaviors or attack signatures are matched."""
    pass

class QuarantineError(SecurityError):
    """Raised when quarantine isolation or recovery fails."""
    pass

class SecurityHardeningError(SecurityError):
    """Raised when runtime hardening or environment validation fails."""
    pass

