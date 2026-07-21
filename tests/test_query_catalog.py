"""Unit tests for QueryCatalog."""

import pytest
from flock.query.catalog import QueryCatalog
from flock.query.exceptions import CatalogNotFoundError
from flock.query.models import CatalogEntry, TableSchema


def test_catalog_table_registration() -> None:
    catalog = QueryCatalog()
    schema = TableSchema(columns_map={"id": "int", "name": "str"})
    entry = CatalogEntry(name="users", schema=schema)

    catalog.register_table(entry)
    assert catalog.get_table("users") == entry
    assert len(catalog.list_tables()) == 1

    with pytest.raises(CatalogNotFoundError):
        catalog.get_table("missing-table")
