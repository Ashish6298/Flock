"""Security Models."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NodeIdentity(BaseModel):
    """Represents a node's cryptographic identity."""
    node_id: str
    public_key: str
    certificate_pem: str

    model_config = {
        "frozen": True
    }


class SessionToken(BaseModel):
    """Represents an HMAC-signed authentication session token."""
    token_id: str
    subject: str
    expires_at: float
    signature: str

    model_config = {
        "frozen": True
    }


class AccessDecision(BaseModel):
    """Represents an access policy authorization decision."""
    allowed: bool
    reason: str
    required_permission: str

    model_config = {
        "frozen": True
    }


class SecurityAuditRecord(BaseModel):
    """Represents an immutable record in the security audit trail."""
    event_name: str
    timestamp: float
    details: Dict[str, str] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class SecurityPolicy(BaseModel):
    """Represents a Zero-Trust security policy with subject/resource matchers."""
    policy_id: str
    effect: str  # "allow" or "deny"
    subjects: List[str]  # Glob patterns or specific IDs
    resources: List[str]  # Glob patterns
    actions: List[str]  # e.g., ["read", "write", "*"]
    conditions: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class CertificateDetails(BaseModel):
    """Detailed model representing a public-key certificate."""
    subject: str
    issuer: str
    valid_from: float
    valid_to: float
    serial_number: str
    signature: str

    model_config = {
        "frozen": True
    }


class SecretEnvelope(BaseModel):
    """Represents an encrypted secret storage envelope."""
    secret_id: str
    ciphertext: str
    iv: str
    tag: Optional[str] = None
    created_at: float
    version: int

    model_config = {
        "frozen": True
    }


class ComplianceReport(BaseModel):
    """Summary of compliance audit check evaluations."""
    timestamp: float
    passed_controls: List[str]
    failed_controls: List[str]
    score: float
    remediations: Dict[str, str] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class QuarantineStatus(BaseModel):
    """Quarantine node status and isolation parameters."""
    node_id: str
    isolated: bool
    reason: str
    isolated_at: Optional[float] = None
    quarantine_until: Optional[float] = None

    model_config = {
        "frozen": True
    }

