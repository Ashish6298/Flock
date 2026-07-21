"""Query Subsystem Models."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Query(BaseModel):
    """Represents a submitted query specification."""
    query_id: str
    raw_sql: str

    model_config = {
        "frozen": True
    }


class QueryResult(BaseModel):
    """Represents the results returned after execution completes."""
    query_id: str
    success: bool
    rows: List[List[Any]] = Field(default_factory=list)
    columns: List[str] = Field(default_factory=list)
    error: Optional[str] = None

    model_config = {
        "frozen": True
    }


class ExecutionStage(BaseModel):
    """Represents a discrete stage of the logical plan execution."""
    stage_id: str
    operation_type: str  # "SCAN", "FILTER", "PROJECTION", "AGGREGATE", "SORT"
    properties: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class ExecutionPlan(BaseModel):
    """Represents an execution plan containing sequential stages."""
    stages: List[ExecutionStage] = Field(default_factory=list)

    model_config = {
        "frozen": True
    }


class ExecutionStatistics(BaseModel):
    """Represents measurements collected during query plan execution."""
    rows_processed: int = 0
    execution_time_ms: float = 0.0

    model_config = {
        "frozen": True
    }


class TableSchema(BaseModel):
    """Represents columns schema map metadata."""
    columns_map: Dict[str, str] = Field(default_factory=dict)  # name -> type

    model_config = {
        "frozen": True
    }


class CatalogEntry(BaseModel):
    """Represents catalog lookup registrations metadata."""
    name: str
    schema_def: TableSchema = Field(alias="schema")

    model_config = {
        "frozen": True,
        "populate_by_name": True
    }


class QueryProgress(BaseModel):
    """Represents percentage completion rates indicators."""
    percent_complete: float = 0.0

    model_config = {
        "frozen": True
    }


class QueryMetrics(BaseModel):
    """Represents query execution latency metrics."""
    avg_latency: float = 0.0

    model_config = {
        "frozen": True
    }


class QueryContext(BaseModel):
    """Represents evaluation parameters context maps."""
    parameters: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class FunctionMetadata(BaseModel):
    """Represents built-in registered functions metadata."""
    name: str
    arity: int

    model_config = {
        "frozen": True
    }


class AggregationResult(BaseModel):
    """Represents grouped reduced aggregates values."""
    groups_values: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }
