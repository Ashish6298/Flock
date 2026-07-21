"""API Gateway Models."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ApiRequest(BaseModel):
    """Represents an external REST call payload details."""
    request_id: str
    path: str
    method: str  # GET, POST, DELETE, etc.
    headers: Dict[str, str] = Field(default_factory=dict)
    query_params: Dict[str, str] = Field(default_factory=dict)
    body: Optional[bytes] = None

    model_config = {
        "frozen": True
    }


class ApiResponse(BaseModel):
    """Represents target result metadata sent back to API clients."""
    request_id: str
    status_code: int
    headers: Dict[str, str] = Field(default_factory=dict)
    body: bytes

    model_config = {
        "frozen": True
    }


class ApiError(BaseModel):
    """Represents a structured error payload formatted for API clients."""
    error_code: str
    message: str
    details: Dict[str, str] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class ApiRoute(BaseModel):
    """Represents an HTTP endpoint routing configuration registry."""
    path: str
    method: str
    handler_name: str
    version: str = "v1"

    model_config = {
        "frozen": True
    }


class ApiContext(BaseModel):
    """Represents caller metadata matching request pipelines."""
    client_ip: str
    auth_token: Optional[str] = None
    client_version: str = "1.0"

    model_config = {
        "frozen": True
    }


class ApiKey(BaseModel):
    """Represents external authorization API key credentials."""
    key_id: str
    token: str
    expires_at: float

    model_config = {
        "frozen": True
    }


class SdkRequest(BaseModel):
    """Represents client wrapper target service executions."""
    service_name: str
    method_name: str
    payload: bytes

    model_config = {
        "frozen": True
    }


class SdkResponse(BaseModel):
    """Represents client SDK response coordinates."""
    success: bool
    payload: bytes
    error: Optional[str] = None

    model_config = {
        "frozen": True
    }


class OpenApiDocument(BaseModel):
    """Represents generated Swagger documentation blueprints."""
    title: str
    version: str
    info: Dict[str, str] = Field(default_factory=dict)
    paths: List[str] = Field(default_factory=list)

    model_config = {
        "frozen": True
    }
