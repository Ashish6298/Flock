"""Functions Subsystem Models."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FunctionDefinition(BaseModel):
    """Represents a registered serverless function definition spec."""
    function_id: str
    name: str
    version: str = "1.0.0"
    handler_code: str
    env: Dict[str, str] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class InvocationRequest(BaseModel):
    """Represents parameters package sent to execution engine."""
    invocation_id: str
    function_id: str
    args: List[Any] = Field(default_factory=list)
    kwargs: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class InvocationResult(BaseModel):
    """Represents execution engine result package."""
    invocation_id: str
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None

    model_config = {
        "frozen": True
    }


class TriggerDefinition(BaseModel):
    """Represents event source trigger definitions."""
    trigger_id: str
    source: str  # "HTTP", "EVENT", "STREAM"
    target_function: str

    model_config = {
        "frozen": True
    }


class FunctionMetrics(BaseModel):
    """Represents execution tracker measurements."""
    function_id: str
    invocation_count: int = 0
    error_count: int = 0
    avg_latency: float = 0.0

    model_config = {
        "frozen": True
    }
