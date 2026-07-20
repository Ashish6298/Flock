"""Security Models."""

from typing import Dict, List, Optional
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
