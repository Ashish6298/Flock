"""Unit tests for QueryParser."""

import pytest
from flock.query.exceptions import QuerySyntaxError
from flock.query.parser import QueryParser


def test_parser_extracts_select_clauses() -> None:
    parser = QueryParser()
    ast = parser.parse_sql("SELECT name, status FROM users WHERE status = 'active'")

    assert ast["projections"] == ["name", "status"]
    assert ast["table"] == "users"
    assert ast["filter"] == "status = 'active'"


def test_parser_malformed_sql_raises() -> None:
    parser = QueryParser()
    with pytest.raises(QuerySyntaxError):
        parser.parse_sql("INSERT INTO users VALUES (1, 'Alice')")
