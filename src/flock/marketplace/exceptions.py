"""Typed exceptions for the marketplace ecosystem and registry management plane."""

from flock.exceptions import FlockError

class MarketplaceError(FlockError):
    """Base exception for all marketplace operations."""
    pass

class PackagePublishError(MarketplaceError):
    """Raised when package manifest, publishing validation, or dependency parsing fails."""
    pass

class SignatureVerificationError(MarketplaceError):
    """Raised when signature checks or publisher identities cannot be verified."""
    pass

class CompatibilityError(MarketplaceError):
    """Raised when target cluster version or feature capabilities are incompatible with the extension package."""
    pass

class LicenseValidationError(MarketplaceError):
    """Raised when extension package license validation checks fail."""
    pass

class InstallationError(MarketplaceError):
    """Raised when file installation, compilation, or target loading fails."""
    pass

class RollbackError(MarketplaceError):
    """Raised when rolling back an extension package upgrade fails."""
    pass
