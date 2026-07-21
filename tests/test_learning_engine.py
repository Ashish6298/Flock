"""Unit tests for LearningEngine."""

import pytest
from flock.ai.exceptions import LearningError
from flock.ai.learning import LearningEngine


def test_learning_engine_updates_parameters() -> None:
    engine = LearningEngine()

    snap = engine.learn_step([1.0, 2.0])
    assert snap.iterations == 1
    assert snap.loss < 0.5


def test_learning_empty_feedback_raises() -> None:
    engine = LearningEngine()
    with pytest.raises(LearningError):
        engine.learn_step([])
