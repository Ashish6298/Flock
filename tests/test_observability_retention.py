"""Unit tests for RetentionManager – Phase 34."""

import time
import pytest

from flock.observability.retention import RetentionManager, RetentionPolicy, RetentionStore


def _make_policy(name: str, ttl: float = 3600.0, max_records: int = 0) -> RetentionPolicy:
    return RetentionPolicy(name=name, ttl_seconds=ttl, max_records=max_records)


def test_register_and_append() -> None:
    mgr = RetentionManager()
    mgr.register_policy(_make_policy("logs"))
    mgr.append("logs", {"msg": "hello"})
    assert mgr.store_count("logs") == 1


def test_get_records() -> None:
    mgr = RetentionManager()
    mgr.register_policy(_make_policy("events"))
    mgr.append("events", "event1")
    mgr.append("events", "event2")
    records = mgr.get_records("events")
    assert len(records) == 2


def test_purge_expired() -> None:
    mgr = RetentionManager()
    mgr.register_policy(_make_policy("fast", ttl=0.01))
    mgr.append("fast", "old")
    time.sleep(0.05)
    expired = mgr.expire("fast")
    assert len(expired) == 1
    assert mgr.store_count("fast") == 0


def test_run_cleanup_removes_expired() -> None:
    mgr = RetentionManager()
    mgr.register_policy(_make_policy("data", ttl=0.01))
    mgr.append("data", "x")
    time.sleep(0.05)
    removed = mgr.run_cleanup()
    assert removed["data"] >= 1


def test_capacity_enforcement() -> None:
    mgr = RetentionManager()
    mgr.register_policy(_make_policy("capped", ttl=3600.0, max_records=3))
    for i in range(5):
        mgr.append("capped", f"item{i}")
    mgr.run_cleanup()
    assert mgr.store_count("capped") <= 3


def test_cleanup_count_increments() -> None:
    mgr = RetentionManager()
    mgr.register_policy(_make_policy("x"))
    mgr.run_cleanup()
    mgr.run_cleanup()
    assert mgr.cleanup_count() == 2


def test_expire_unregistered_policy_returns_empty() -> None:
    mgr = RetentionManager()
    result = mgr.expire("ghost")
    assert result == []


def test_list_policies() -> None:
    mgr = RetentionManager()
    mgr.register_policy(_make_policy("a"))
    mgr.register_policy(_make_policy("b"))
    names = mgr.list_policies()
    assert "a" in names and "b" in names


def test_append_unregistered_raises() -> None:
    mgr = RetentionManager()
    with pytest.raises(KeyError):
        mgr.append("nonexistent", "data")


def test_archive_handler_called_on_expiry() -> None:
    archived: list = []
    policy = RetentionPolicy(
        name="archival",
        ttl_seconds=0.01,
        archive_handler=lambda records: archived.extend(records),
    )
    mgr = RetentionManager()
    mgr.register_policy(policy)
    mgr.append("archival", "important")
    time.sleep(0.05)
    mgr.expire("archival")
    assert "important" in archived


def test_clear_store() -> None:
    mgr = RetentionManager()
    mgr.register_policy(_make_policy("clearable"))
    mgr.append("clearable", "r1")
    mgr.clear_store("clearable")
    assert mgr.store_count("clearable") == 0


def test_get_records_empty_for_unknown_policy() -> None:
    mgr = RetentionManager()
    assert mgr.get_records("missing") == []
