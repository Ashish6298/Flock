"""Unit tests for StructuredLogger – Phase 34."""

import pytest

from flock.observability.logging import LogLevel, LogRecord, StructuredLogger


def test_logger_records_info() -> None:
    logger = StructuredLogger()
    rec = logger.info("api", "Request received", method="GET")
    assert rec is not None
    assert rec.level == LogLevel.INFO
    assert rec.component == "api"
    assert rec.message == "Request received"
    assert rec.fields["method"] == "GET"


def test_logger_respects_min_level() -> None:
    logger = StructuredLogger(min_level=LogLevel.WARNING)
    rec = logger.debug("comp", "ignored")
    assert rec is None
    assert logger.count() == 0


def test_logger_records_all_levels() -> None:
    logger = StructuredLogger()
    logger.debug("c", "d")
    logger.info("c", "i")
    logger.warning("c", "w")
    logger.error("c", "e")
    logger.critical("c", "crit")
    assert logger.count() == 5


def test_logger_search_by_level() -> None:
    logger = StructuredLogger()
    logger.info("x", "msg1")
    logger.error("x", "msg2")
    errors = logger.search(level=LogLevel.ERROR)
    assert len(errors) == 1
    assert errors[0].level == LogLevel.ERROR


def test_logger_search_by_component() -> None:
    logger = StructuredLogger()
    logger.info("mesh", "route updated")
    logger.info("api", "request")
    mesh_logs = logger.search(component="mesh")
    assert len(mesh_logs) == 1


def test_logger_search_by_message_contains() -> None:
    logger = StructuredLogger()
    logger.info("comp", "Connection refused by peer")
    logger.info("comp", "Request succeeded")
    results = logger.search(message_contains="refused")
    assert len(results) == 1


def test_logger_search_by_correlation_id() -> None:
    logger = StructuredLogger()
    logger.record(
        LogLevel.INFO, "comp", "msg", correlation_id="trace-abc"
    )
    logger.record(LogLevel.INFO, "comp", "other")
    results = logger.search(correlation_id="trace-abc")
    assert len(results) == 1
    assert results[0].correlation_id == "trace-abc"


def test_logger_pagination() -> None:
    logger = StructuredLogger()
    for i in range(25):
        logger.info("comp", f"message {i}")
    page0 = logger.search(page=0, page_size=10)
    page1 = logger.search(page=1, page_size=10)
    page2 = logger.search(page=2, page_size=10)
    assert len(page0) == 10
    assert len(page1) == 10
    assert len(page2) == 5


def test_logger_clear() -> None:
    logger = StructuredLogger()
    logger.info("c", "msg")
    logger.clear()
    assert logger.count() == 0


def test_log_record_to_dict() -> None:
    rec = LogRecord(
        level=LogLevel.WARNING,
        component="test",
        message="hello",
        correlation_id="cid-1",
        fields={"key": "value"},
    )
    d = rec.to_dict()
    assert d["level"] == "WARNING"
    assert d["correlation_id"] == "cid-1"
    assert d["fields"]["key"] == "value"


def test_log_record_to_json() -> None:
    rec = LogRecord(level=LogLevel.INFO, component="x", message="y")
    import json
    parsed = json.loads(rec.to_json())
    assert parsed["level"] == "INFO"


def test_logger_export_batch() -> None:
    logger = StructuredLogger()
    for i in range(10):
        logger.info("comp", f"msg {i}")
    batch = logger.export_batch(max_records=5)
    assert len(batch) == 5


def test_logger_set_min_level() -> None:
    logger = StructuredLogger()
    logger.set_min_level(LogLevel.ERROR)
    logger.info("c", "ignored")
    assert logger.count() == 0
    logger.error("c", "kept")
    assert logger.count() == 1


def test_logger_ring_buffer_bounded() -> None:
    logger = StructuredLogger(max_records=5)
    for i in range(10):
        logger.info("c", f"msg {i}")
    assert logger.count() == 5
