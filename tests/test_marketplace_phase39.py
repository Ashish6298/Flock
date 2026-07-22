"""Unit tests for Phase 39 Enterprise Marketplace, Package Registry & Ecosystem Integration Framework Subsystem."""

import time
import pytest
from unittest.mock import MagicMock, AsyncMock

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.protocol.packet import MessageType
from flock.security.encryption import CryptographyEngine
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
    InstallationReceipt,
)
from flock.marketplace.catalog import MarketplaceCatalog
from flock.marketplace.search import MarketplaceSearchIndex
from flock.marketplace.publisher import PublisherIdentityManager
from flock.marketplace.dependency import DependencyResolver
from flock.marketplace.validation import MarketplaceValidator, SemanticVersionManager
from flock.marketplace.installer import PackageInstaller
from flock.marketplace.updater import PackageUpdater
from flock.marketplace.licensing import LicenseManager
from flock.marketplace.analytics import MarketplaceAnalyticsEngine
from flock.marketplace.synchronization import RegistrySynchronizer
from flock.marketplace.audit import MarketplaceAuditLogger
from flock.marketplace.coordinator import MarketplaceCoordinator
from flock.marketplace.service import MarketplaceService


# -----------------------------------------------------------------------------
# Catalog & Search Tests
# -----------------------------------------------------------------------------

def test_catalog_and_search() -> None:
    catalog = MarketplaceCatalog()
    search = MarketplaceSearchIndex()
    
    m = PackageManifest(
        package_id="ext-mesh",
        name="Service Mesh Extension",
        publisher_id="pub-1",
        version="1.0.0",
        description="Integrates premium routing topology.",
        dependencies=[],
        required_features=[],
        signature="sig-1",
    )
    catalog.register_manifest(m)
    assert catalog.get_manifest("ext-mesh").version == "1.0.0"
    
    search.index_package(m)
    assert "ext-mesh" in search.search("Service Mesh")
    assert "ext-mesh" in search.search("topology")
    assert len(search.search("nonexistent")) == 0


# -----------------------------------------------------------------------------
# Publisher & Signature Tests
# -----------------------------------------------------------------------------

def test_publisher_signatures() -> None:
    crypto = CryptographyEngine(b"marketplace_signing_secret_16bytes")
    pub_mgr = PublisherIdentityManager(crypto)
    
    pub = PublisherInfo(
        publisher_id="pub-1",
        name="Enterprise Devs",
        certificate_pem="cert-data",
        verified=True,
    )
    pub_mgr.register_publisher(pub)
    
    # Valid Signature
    sig = crypto.generate_hmac(b"ext-mesh:1.0.0:pub-1")
    assert pub_mgr.verify_package_signature("ext-mesh", "1.0.0", sig, "pub-1") is True
    
    # Invalid signature should raise
    with pytest.raises(SignatureVerificationError):
        pub_mgr.verify_package_signature("ext-mesh", "1.0.0", "wrong-sig", "pub-1")


# -----------------------------------------------------------------------------
# Dependency Resolver Tests
# -----------------------------------------------------------------------------

def test_dependency_resolver() -> None:
    resolver = DependencyResolver()
    resolver.register_package_version("db-driver", "1.1.0")
    resolver.register_package_version("db-driver", "1.2.0")
    
    # Resolution passes
    res = resolver.resolve_dependencies(["db-driver>=1.1.0"])
    assert res == ["db-driver:1.2.0"]
    
    # No matching versions raises
    with pytest.raises(CompatibilityError):
        resolver.resolve_dependencies(["db-driver>=2.0.0"])


# -----------------------------------------------------------------------------
# Validator & Semver Tests
# -----------------------------------------------------------------------------

def test_compatibility_and_licensing() -> None:
    val = MarketplaceValidator("1.0.0", ["ServiceMesh", "DataGrid"])
    val.register_valid_license("ext-grid", "license-12345")
    
    m_ok = PackageManifest(
        package_id="ext-grid",
        name="Grid Extension",
        publisher_id="pub-1",
        version="1.0.0",
        description="DataGrid tool",
        dependencies=[],
        required_features=["DataGrid"],
        license_key="license-12345",
        signature="sig",
    )
    assert val.validate_package_compatibility(m_ok) is True
    assert val.validate_package_license(m_ok) is True
    
    # Missing required feature raises compatibility error
    m_fail = PackageManifest(
        package_id="ext-grid",
        name="Grid Extension",
        publisher_id="pub-1",
        version="1.0.0",
        description="Grid tool",
        dependencies=[],
        required_features=["KubernetesOperator"],
        signature="sig",
    )
    with pytest.raises(CompatibilityError):
        val.validate_package_compatibility(m_fail)
        
    assert SemanticVersionManager.is_valid_semver("1.2.3") is True
    assert SemanticVersionManager.is_valid_semver("invalid-version") is False


# -----------------------------------------------------------------------------
# Installer & Updater/Rollback Tests
# -----------------------------------------------------------------------------

def test_installation_and_upgrades() -> None:
    installer = PackageInstaller()
    updater = PackageUpdater(installer)
    
    m1 = PackageManifest(
        package_id="ext-1",
        name="Extension 1",
        publisher_id="pub-1",
        version="1.0.0",
        description="Ext",
        dependencies=[],
        required_features=[],
        signature="sig",
    )
    receipt = installer.install_package(m1)
    assert receipt.installed_version == "1.0.0"
    assert receipt.status == "active"
    
    # Upgrade
    m2 = PackageManifest(
        package_id="ext-1",
        name="Extension 1",
        publisher_id="pub-1",
        version="1.1.0",
        description="Ext",
        dependencies=[],
        required_features=[],
        signature="sig",
    )
    receipt_up = updater.upgrade_package(m2)
    assert receipt_up.installed_version == "1.1.0"
    
    # Rollback
    receipt_rb = updater.rollback_package("ext-1")
    assert receipt_rb.installed_version == "1.0.0"
    assert receipt_rb.status == "rolled_back"


# -----------------------------------------------------------------------------
# Marketplace Service Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_marketplace_service_integration() -> None:
    bus = MagicMock(spec=MessageBus)
    bus.router = MagicMock()
    bus.send = AsyncMock()
    
    events = EventBus()
    event_list = []
    
    async def on_init(data: dict) -> None: # type: ignore[type-arg]
        event_list.append(data)
        
    events.subscribe("marketplace.initialized", on_init)
    
    crypto = CryptographyEngine(b"marketplace_service_secret_16bytes")
    service = MarketplaceService("1.0.0", ["DataGrid"], crypto, bus, events)
    
    await service.start()
    assert service._running is True
    assert len(event_list) == 1
    assert service._bus.router.register.call_count == 2
    
    await service.stop()
    assert service._running is False
