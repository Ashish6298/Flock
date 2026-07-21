"""Unit tests for ClusterIntelligenceEngine."""

from flock.ai.analyzer import ClusterIntelligenceEngine


def test_cluster_intelligence_averages() -> None:
    engine = ClusterIntelligenceEngine()
    samples = [
        {"cpu_load": 0.8, "memory_load": 0.4},
        {"cpu_load": 0.6, "memory_load": 0.6},
    ]

    analysis = engine.analyze_utilization(samples)
    assert analysis.metrics_map["cpu_load"] == 0.7
    assert analysis.metrics_map["memory_load"] == 0.5
