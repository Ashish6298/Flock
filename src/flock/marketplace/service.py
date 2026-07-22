"""High-level MarketplaceService orchestrating package publishing, updates, and indexing."""

from __future__ import annotations

import time
import threading
from typing import Any, Dict, Optional, List

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.security.encryption import CryptographyEngine
from flock.marketplace.coordinator import MarketplaceCoordinator
from flock.marketplace.models import PackageManifest

logger = structlog.get_logger()


class MarketplaceService:
    """Coordinates package publish queries, dependency resolutions, and installations on MessageBus."""

    def __init__(
        self,
        platform_version: str,
        active_features: List[str],
        crypto: CryptographyEngine,
        message_bus: MessageBus,
        event_bus: EventBus,
    ) -> None:
        self._bus = message_bus
        self._events = event_bus
        self._lock = threading.RLock()

        self.coordinator = MarketplaceCoordinator(platform_version, active_features, crypto)
        self._running = False

    async def start(self) -> None:
        """Start the marketplace service and register MessageBus query listeners."""
        with self._lock:
            if self._running:
                return
            self._running = True

        self._register_handlers()
        
        await self._events.publish(
            "marketplace.initialized",
            {
                "timestamp": time.time(),
            }
        )
        logger.info("MarketplaceService started")

    async def stop(self) -> None:
        """Stop marketplace operations."""
        with self._lock:
            if not self._running:
                return
            self._running = False

        await self._events.publish(
            "marketplace.service.synchronized",
            {
                "timestamp": time.time(),
            }
        )
        logger.info("MarketplaceService stopped")

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register query verification endpoints on MessageBus."""
        router = self._bus.router

        async def handle_package_publish(context: Any) -> None:
            payload = context.payload or {}
            package_id = payload.get("package_id")
            name = payload.get("name")
            publisher_id = payload.get("publisher_id")
            version = payload.get("version", "0.0.1")
            description = payload.get("description", "")
            dependencies = payload.get("dependencies", [])
            required_features = payload.get("required_features", [])
            license_key = payload.get("license_key")
            sig = payload.get("signature")
            
            reply_target = context.sender
            try:
                # 1. Signature check
                self.coordinator.publisher.verify_package_signature(
                    package_id=package_id or "",
                    version=version,
                    signature=sig or "",
                    publisher_id=publisher_id or "",
                )
                
                # 2. Build manifest
                manifest = PackageManifest(
                    package_id=package_id or "",
                    name=name or "",
                    publisher_id=publisher_id or "",
                    version=version,
                    description=description,
                    dependencies=dependencies,
                    required_features=required_features,
                    license_key=license_key,
                    signature=sig or "",
                )
                
                # 3. Validate compatibility
                self.coordinator.validator.validate_package_compatibility(manifest)
                self.coordinator.validator.validate_package_license(manifest)
                
                # 4. Save manifest and index search
                self.coordinator.catalog.register_manifest(manifest)
                self.coordinator.search.index_package(manifest)
                self.coordinator.dependency.register_package_version(manifest.package_id, manifest.version)
                
                await self._events.publish(
                    "package.published",
                    {"package_id": package_id, "timestamp": time.time()}
                )
                
                await self._bus.send(
                    reply_target,
                    MessageType.MARKETPLACE_HEALTH_REPORT,
                    {"success": True},
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.MARKETPLACE_HEALTH_REPORT,
                    {"success": False, "error": str(exc)},
                )

        async def handle_package_install(context: Any) -> None:
            payload = context.payload or {}
            package_id = payload.get("package_id")
            
            reply_target = context.sender
            try:
                manifest = self.coordinator.catalog.get_manifest(package_id or "")
                
                # Transactional installation
                receipt = self.coordinator.installer.install_package(manifest)
                self.coordinator.analytics.record_download(package_id or "")
                
                await self._events.publish(
                    "package.installed",
                    {"package_id": package_id, "version": manifest.version, "timestamp": time.time()}
                )
                
                await self._bus.send(
                    reply_target,
                    MessageType.MARKETPLACE_HEALTH_REPORT,
                    {"success": True, "transaction_id": receipt.transaction_id},
                )
            except Exception as exc:
                self.coordinator.analytics.record_install_failure()
                await self._events.publish(
                    "package.install.failed",
                    {"package_id": package_id, "error": str(exc), "timestamp": time.time()}
                )
                await self._bus.send(
                    reply_target,
                    MessageType.MARKETPLACE_HEALTH_REPORT,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.MARKETPLACE_PUBLISH,
            _MpQueryHandler(handle_package_publish),
        )
        router.register(
            MessageType.MARKETPLACE_INSTALL,
            _MpQueryHandler(handle_package_install),
        )


class _MpQueryHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
