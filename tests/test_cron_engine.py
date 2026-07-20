"""Unit tests for CronEngine."""

import pytest
from flock.scheduling.cron import CronEngine
from flock.scheduling.exceptions import InvalidCronExpressionError


def test_cron_engine_parsing() -> None:
    engine = CronEngine()

    # Valid standard 5-field expression
    parts = engine.parse_expression("*/5 * * * *")
    assert len(parts) == 5

    # Invalid fields count raises
    with pytest.raises(InvalidCronExpressionError):
        engine.parse_expression("*/5 * * *")


def test_cron_next_execution_time() -> None:
    engine = CronEngine()
    now = 1718000000.0

    # Test basic increment projection
    next_run = engine.get_next_run("*/5 * * * *", now)
    assert next_run == now + 60.0
