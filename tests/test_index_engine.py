"""Unit tests for IndexEngine."""

from flock.datagrid.indexing import IndexEngine


def test_index_references_lookup() -> None:
    engine = IndexEngine()

    engine.add_index_value("role", "admin", "user-1")
    engine.add_index_value("role", "admin", "user-2")
    engine.add_index_value("role", "member", "user-3")

    # Lookup returns sorted list of matching keys
    assert engine.lookup_index("role", "admin") == ["user-1", "user-2"]
    assert engine.lookup_index("role", "member") == ["user-3"]

    # Mismatched lookup returns empty list
    assert engine.lookup_index("role", "guest") == []
