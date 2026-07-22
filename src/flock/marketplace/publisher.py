"""Publisher identities validations and signature checks."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional
from flock.marketplace.exceptions import SignatureVerificationError
from flock.marketplace.models import PublisherInfo
from flock.security.encryption import CryptographyEngine


class PublisherIdentityManager:
    """Manages verified publisher certificates and validates package signatures."""

    def __init__(self, crypto: CryptographyEngine) -> None:
        self._crypto = crypto
        self._lock = threading.RLock()
        # publisher_id -> PublisherInfo
        self._publishers: Dict[str, PublisherInfo] = {}

    def register_publisher(self, publisher: PublisherInfo) -> None:
        """Register a verified publisher profile."""
        with self._lock:
            self._publishers[publisher.publisher_id] = publisher

    def verify_package_signature(self, package_id: str, version: str, signature: str, publisher_id: str) -> bool:
        """Verify signature authenticity of an extension release payload.
        
        Raises:
            SignatureVerificationError: If verification checks fail.
        """
        with self._lock:
            pub = self._publishers.get(publisher_id)
            if not pub:
                raise SignatureVerificationError(f"Publisher '{publisher_id}' is not registered or verified.")
                
            if not pub.verified:
                raise SignatureVerificationError(f"Publisher '{publisher_id}' is not verified.")
                
            # Verify signature payload: package_id:version:publisher_id
            payload = f"{package_id}:{version}:{publisher_id}".encode("utf-8")
            try:
                self._crypto.verify_signature(payload, signature)
                return True
            except Exception as exc:
                raise SignatureVerificationError(f"Extension package signature verification failed: {exc}") from exc

    def get_publisher(self, publisher_id: str) -> Optional[PublisherInfo]:
        with self._lock:
            return self._publishers.get(publisher_id)
