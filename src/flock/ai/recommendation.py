"""AI Recommendation Engine."""

from __future__ import annotations

from typing import Dict, List

from flock.ai.exceptions import RecommendationError
from flock.ai.models import Recommendation


class AIRecommendationEngine:
    """Builds tuning recommendations based on resource utilization metrics."""

    def __init__(self) -> None:
        pass

    def get_recommendations(self, metrics: Dict[str, float]) -> List[Recommendation]:
        """Generate configurations recommendation list."""
        recommendations = []
        
        cpu_load = metrics.get("cpu_load", 0.0)
        if cpu_load > 0.9:
            recommendations.append(
                Recommendation(
                    recommendation_id="rec-cpu-scale",
                    description="Increase cluster worker pool node count.",
                )
            )

        return recommendations
