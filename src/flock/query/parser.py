"""Query SQL Parser compiling SQL strings to AST stages."""

from __future__ import annotations

import re
from typing import Any, Dict

from flock.query.exceptions import QuerySyntaxError


class QueryParser:
    """Extracts projections, tables, filters, and groups parameters."""

    def __init__(self) -> None:
        pass

    def parse_sql(self, sql: str) -> Dict[str, Any]:
        """Convert SQL query into abstract syntax fields map.

        Raises:
            QuerySyntaxError: If sql syntax matches fail.
        """
        cleaned = sql.strip().replace("\n", " ").replace("\r", " ")
        pattern = re.compile(
            r"^SELECT\s+(.+?)\s+FROM\s+(.+?)(?:\s+WHERE\s+(.+?))?(?:\s+GROUP\s+BY\s+(.+?))?$",
            re.IGNORECASE,
        )
        match = pattern.match(cleaned)
        if not match:
            raise QuerySyntaxError(f"Malformed SELECT query syntax: {sql}")

        proj_str = match.group(1).strip()
        from_str = match.group(2).strip()
        where_str = match.group(3).strip() if match.group(3) else None
        group_str = match.group(4).strip() if match.group(4) else None

        projections = [p.strip() for p in proj_str.split(",")]
        
        return {
            "projections": projections,
            "table": from_str,
            "filter": where_str,
            "group_by": group_by_list(group_str) if group_str else None,
        }


def group_by_list(group_str: str) -> list[str]:
    """Helper converting GROUP BY statement to field elements."""
    return [g.strip() for g in group_str.split(",")]
