"""Unit tests for AutonomousOptimizationEngine."""

from flock.ai.optimizer import AutonomousOptimizationEngine


def test_optimizer_actions_generation() -> None:
    engine = AutonomousOptimizationEngine()

    # High CPU triggers scale and task migration actions
    plan = engine.generate_plan({"cpu_load": 0.85, "memory_load": 0.5})
    assert "SCALE_UP_REPLICAS" in plan.actions
    assert "MIGRATE_HEAVY_TASKS" in plan.actions

    # High memory triggers cache purge
    plan_mem = engine.generate_plan({"cpu_load": 0.3, "memory_load": 0.9})
    assert "PURGE_EXPIRED_CACHES" in plan_mem.actions
