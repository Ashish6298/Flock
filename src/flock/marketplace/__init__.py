"""Init for marketplace package. Exposes all Package Registry and Ecosystem interfaces."""

from flock.marketplace.exceptions import (
    MarketplaceError,
    PackagePublishError,
    SignatureVerificationError,
    CompatibilityError,
    LicenseValidationError,
    InstallationError,
    RollbackError,
)
from flock.marketplace.models import (
    PublisherInfo,
    PackageManifest,
    PackageVersionInfo,
    InstallationReceipt,
    MarketplaceMetricsReport,
)
from flock.marketplace.catalog import MarketplaceCatalog
from flock.marketplace.search import MarketplaceSearchIndex
from flock.marketplace.publisher import PublisherIdentityManager
from flock.marketplace.signatures import PublisherIdentityManager as PublisherIdentityManagerAlias
from flock.marketplace.dependency import DependencyResolver
from flock.marketplace.dependencies import DependencyResolver as DependencyResolverAlias
from flock.marketplace.validation import MarketplaceValidator, SemanticVersionManager
from flock.marketplace.versions import SemanticVersionManager as SemanticVersionManagerAlias
from flock.marketplace.installer import PackageInstaller
from flock.marketplace.updater import PackageUpdater
from flock.marketplace.rollback import PackageUpdater as PackageUpdaterAlias
from flock.marketplace.licensing import LicenseManager
from flock.marketplace.analytics import MarketplaceAnalyticsEngine
from flock.marketplace.synchronization import RegistrySynchronizer
from flock.marketplace.audit import MarketplaceAuditLogger
from flock.marketplace.coordinator import MarketplaceCoordinator
from flock.marketplace.service import MarketplaceService

__all__ = [
    # Exceptions
    "MarketplaceError",
    "PackagePublishError",
    "SignatureVerificationError",
    "CompatibilityError",
    "LicenseValidationError",
    "InstallationError",
    "RollbackError",
    
    # Models
    "PublisherInfo",
    "PackageManifest",
    "PackageVersionInfo",
    "InstallationReceipt",
    "MarketplaceMetricsReport",
    
    # Engines & Managers
    "MarketplaceCatalog",
    "MarketplaceSearchIndex",
    "PublisherIdentityManager",
    "DependencyResolver",
    "MarketplaceValidator",
    "SemanticVersionManager",
    "PackageInstaller",
    "PackageUpdater",
    "LicenseManager",
    "MarketplaceAnalyticsEngine",
    "RegistrySynchronizer",
    "MarketplaceAuditLogger",
    "MarketplaceCoordinator",
    "MarketplaceService",
]
