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
