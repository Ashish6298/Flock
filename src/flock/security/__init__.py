"""Init for security package. Exposes all Zero-Trust security and compliance models and services."""

from flock.security.exceptions import (
    SecurityError,
    AuthenticationError,
    AuthorizationError,
    SignatureVerificationError,
    TokenExpiredError,
    KeyRotationError,
    PolicyEvaluationError,
    CertificateValidationError,
    SecretStorageError,
    TamperDetectionError,
    ComplianceControlError,
    IntrusionDetectionAlert,
    QuarantineError,
    SecurityHardeningError,
)
from flock.security.models import (
    NodeIdentity,
    SessionToken,
    AccessDecision,
    SecurityAuditRecord,
    SecurityPolicy,
    CertificateDetails,
    SecretEnvelope,
    ComplianceReport,
    QuarantineStatus,
)
from flock.security.encryption import CryptographyEngine
from flock.security.identity import IdentityManager
from flock.security.authorization import AuthorizationEngine
from flock.security.token import TokenManager
from flock.security.handshake import SecureHandshakeManager
from flock.security.audit import SecurityAuditLogger
from flock.security.service import SecurityService

from flock.security.certificates import CertificateManager
from flock.security.authentication import AuthenticationEngine
from flock.security.policy import PolicyManager
from flock.security.secrets import SecretsManager, VaultProvider, InMemoryVaultProvider
from flock.security.compliance import ComplianceEngine
from flock.security.intrusion import IntrusionDetector
from flock.security.quarantine import QuarantineManager
from flock.security.rotation import CredentialRotationEngine
from flock.security.hardening import HardeningEngine

__all__ = [
    # Exceptions
    "SecurityError",
    "AuthenticationError",
    "AuthorizationError",
    "SignatureVerificationError",
    "TokenExpiredError",
    "KeyRotationError",
    "PolicyEvaluationError",
    "CertificateValidationError",
    "SecretStorageError",
    "TamperDetectionError",
    "ComplianceControlError",
    "IntrusionDetectionAlert",
    "QuarantineError",
    "SecurityHardeningError",
    
    # Models
    "NodeIdentity",
    "SessionToken",
    "AccessDecision",
    "SecurityAuditRecord",
    "SecurityPolicy",
    "CertificateDetails",
    "SecretEnvelope",
    "ComplianceReport",
    "QuarantineStatus",
    
    # Engines & Managers
    "CryptographyEngine",
    "IdentityManager",
    "AuthorizationEngine",
    "TokenManager",
    "SecureHandshakeManager",
    "SecurityAuditLogger",
    "SecurityService",
    "CertificateManager",
    "AuthenticationEngine",
    "PolicyManager",
    "SecretsManager",
    "VaultProvider",
    "InMemoryVaultProvider",
    "ComplianceEngine",
    "IntrusionDetector",
    "QuarantineManager",
    "CredentialRotationEngine",
    "HardeningEngine",
]
