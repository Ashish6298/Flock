"""AI Subsystem Exceptions."""

from flock.exceptions import FlockError

class AIError(FlockError):
    """Base exception for all AI operations."""
    pass

class PredictionError(AIError):
    """Raised when prediction logic fails."""
    pass

class OptimizationError(AIError):
    """Raised when plan optimizations fail."""
    pass

class ForecastError(AIError):
    """Raised when forecasting logic fails."""
    pass

class LearningError(AIError):
    """Raised when learning models fail to update."""
    pass

class RecommendationError(AIError):
    """Raised when recommendation logic fails."""
    pass

class ModelSynchronizationError(AIError):
    """Raised when model updates sync fails."""
    pass

class AnomalyDetectionError(AIError):
    """Raised when anomaly validation checks fail."""
    pass

class ClusterAnalysisError(AIError):
    """Raised when telemetry analyses fail."""
    pass

class TrainingDataError(AIError):
    """Raised when training data inputs fail schema checks."""
    pass

class InferenceError(AIError):
    """Raised when inference logic fails."""
    pass
