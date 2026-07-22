"""Certificate lifecycle, validation and mock trust chains management using standard Python parsing."""

from __future__ import annotations

import time
import uuid
from typing import Dict, List, Optional
from flock.security.exceptions import CertificateValidationError
from flock.security.models import CertificateDetails, NodeIdentity
from flock.security.encryption import CryptographyEngine


class CertificateManager:
    """Manages generation, certificate validity verification, and trust root authority chains."""

    def __init__(self, crypto: CryptographyEngine, ca_name: str = "Flock Root CA") -> None:
        self._crypto = crypto
        self._ca_name = ca_name
        self._revocation_list: List[str] = []

    def issue_certificate(
        self,
        subject: str,
        validity_days: int = 365,
    ) -> CertificateDetails:
        """Issue a new cryptographic certificate under the Root CA authority."""
        now = time.time()
        expiry = now + (validity_days * 86000)
        serial = str(uuid.uuid4())
        
        # Build signing payload
        payload = f"{subject}:{self._ca_name}:{now}:{expiry}:{serial}".encode("utf-8")
        sig = self._crypto.sign_data(payload)
        
        return CertificateDetails(
            subject=subject,
            issuer=self._ca_name,
            valid_from=now,
            valid_to=expiry,
            serial_number=serial,
            signature=sig,
        )

    def validate_certificate(self, cert: CertificateDetails) -> bool:
        """Validate certificate validity dates, revocation state, and root signatures.
        
        Raises:
            CertificateValidationError: If the certificate fails validation checks.
        """
        now = time.time()
        if now < cert.valid_from:
            raise CertificateValidationError("Certificate is not valid yet.")
        if now > cert.valid_to:
            raise CertificateValidationError("Certificate has expired.")
            
        if cert.serial_number in self._revocation_list:
            raise CertificateValidationError("Certificate has been revoked.")
            
        # Reconstruct signature payload
        payload = f"{cert.subject}:{cert.issuer}:{cert.valid_from}:{cert.valid_to}:{cert.serial_number}".encode("utf-8")
        try:
            self._crypto.verify_signature(payload, cert.signature)
        except Exception as exc:
            raise CertificateValidationError(f"Invalid certificate signature check failed: {exc}") from exc
            
        return True

    def revoke_certificate(self, serial_number: str) -> None:
        """Revoke a certificate by serial number."""
        if serial_number not in self._revocation_list:
            self._revocation_list.append(serial_number)

    def is_revoked(self, serial_number: str) -> bool:
        """Return true if certificate serial is revoked."""
        return serial_number in self._revocation_list
