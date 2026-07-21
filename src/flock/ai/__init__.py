"""Init for ai package."""

from flock.ai.exceptions import (
    AIError,
    PredictionError,
    OptimizationError,
    ForecastError,
    LearningError,
    RecommendationError,
    ModelSynchronizationError,
    AnomalyDetectionError,
    ClusterAnalysisError,
    TrainingDataError,
    InferenceError,
)
from flock.ai.models import (
    PredictionRequest,
    PredictionResult,
    OptimizationPlan,
    ClusterAnalysis,
    ForecastModel,
    ForecastResult,
    Recommendation,
    LearningSnapshot,
    ModelStatistics,
    NodePrediction,
    WorkloadProfile,
    AnomalyReport,
    OptimizationMetrics,
    ClusterIntelligenceReport,
    ModelMetadata,
)
from flock.ai.predictor import MachineLearningPredictionEngine
from flock.ai.scheduler import PredictiveScheduler
from flock.ai.optimizer import AutonomousOptimizationEngine
from flock.ai.analyzer import ClusterIntelligenceEngine
from flock.ai.anomaly import AnomalyDetectionEngine
from flock.ai.forecast import ForecastEngine
from flock.ai.recommendation import AIRecommendationEngine
from flock.ai.learning import LearningEngine
from flock.ai.service import AIService

__all__ = [
    "AIError",
    "PredictionError",
    "OptimizationError",
    "ForecastError",
    "LearningError",
    "RecommendationError",
    "ModelSynchronizationError",
    "AnomalyDetectionError",
    "ClusterAnalysisError",
    "TrainingDataError",
    "InferenceError",
    "PredictionRequest",
    "PredictionResult",
    "OptimizationPlan",
    "ClusterAnalysis",
    "ForecastModel",
    "ForecastResult",
    "Recommendation",
    "LearningSnapshot",
    "ModelStatistics",
    "NodePrediction",
    "WorkloadProfile",
    "AnomalyReport",
    "OptimizationMetrics",
    "ClusterIntelligenceReport",
    "ModelMetadata",
    "MachineLearningPredictionEngine",
    "PredictiveScheduler",
    "AutonomousOptimizationEngine",
    "ClusterIntelligenceEngine",
    "AnomalyDetectionEngine",
    "ForecastEngine",
    "AIRecommendationEngine",
    "LearningEngine",
    "AIService",
]
