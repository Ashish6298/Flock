"""Unit tests for AIRecommendationEngine."""

from flock.ai.recommendation import AIRecommendationEngine


def test_recommendation_tuning() -> None:
    engine = AIRecommendationEngine()

    recs = engine.get_recommendations({"cpu_load": 0.95})
    assert len(recs) == 1
    assert recs[0].recommendation_id == "rec-cpu-scale"
