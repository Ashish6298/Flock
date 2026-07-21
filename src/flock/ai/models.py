"""AI Subsystem Models."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Represents a submitted prediction query."""
    predictor_name: str
    features: List[float] = Field(default_factory=list)

    model_config = {
        "frozen": True
    }


class PredictionResult(BaseModel):
    """Represents output returned by prediction engines."""
    prediction_value: float
    confidence: float

    model_config = {
        "frozen": True
    }


class OptimizationPlan(BaseModel):
    """Represents recommended tuning actions plan."""
    actions: List[str] = Field(default_factory=list)

    model_config = {
        "frozen": True
    }


class ClusterAnalysis(BaseModel):
    """Represents telemetry metrics analysis."""
    metrics_map: Dict[str, float] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class ForecastModel(BaseModel):
    """Represents registered forecast profiles."""
    model_name: str

    model_config = {
        "frozen": True
    }


class ForecastResult(BaseModel):
    """Represents predicted future telemetry values."""
    forecasted_values: List[float] = Field(default_factory=list)

    model_config = {
        "frozen": True
    }


class Recommendation(BaseModel):
    """Represents recommended config settings suggestions."""
    recommendation_id: str
    description: str

    model_config = {
        "frozen": True
    }


class LearningSnapshot(BaseModel):
    """Represents metrics collected from active learning iterations."""
    loss: float
    iterations: int

    model_config = {
        "frozen": True
    }


class ModelStatistics(BaseModel):
    """Represents prediction precision scores."""
    accuracy: float

    model_config = {
        "frozen": True
    }


class NodePrediction(BaseModel):
    """Represents predicted nodes failures probability."""
    node_id: str
    failure_probability: float

    model_config = {
        "frozen": True
    }


class WorkloadProfile(BaseModel):
    """Represents recorded workloads CPU and memory profiles."""
    cpu_load: float
    memory_load: float

    model_config = {
        "frozen": True
    }


class ResourceResourceForecast(BaseModel):
    """Represents forecasted CPU and memory capacity resources."""
    forecasted_cpu: float
    forecasted_memory: float

    model_config = {
        "frozen": True
    }


class AnomalyReport(BaseModel):
    """Represents anomalous metrics detections logs."""
    metric_name: str
    value: float
    threshold: float

    model_config = {
        "frozen": True
    }


class OptimizationMetrics(BaseModel):
    """Represents estimated resource savings gains."""
    savings_percentage: float

    model_config = {
        "frozen": True
    }


class ClusterIntelligenceReport(BaseModel):
    """Represents AI recommendations cluster summary."""
    recommendations: List[str] = Field(default_factory=list)

    model_config = {
        "frozen": True
    }


class ModelMetadata(BaseModel):
    """Represents serialized models metadata attributes."""
    version: str

    model_config = {
        "frozen": True
    }
