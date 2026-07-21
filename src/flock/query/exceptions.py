"""Query Subsystem Exceptions."""

from flock.exceptions import FlockError

class QueryError(FlockError):
    """Base exception for all query operations."""
    pass

class QuerySyntaxError(QueryError):
    """Raised when SQL string syntax is invalid."""
    pass

class QueryExecutionError(QueryError):
    """Raised when plan evaluation pipeline fails."""
    pass

class QueryTimeoutError(QueryError):
    """Raised when execution takes longer than allowed timeout limit."""
    pass

class QueryCancelledError(QueryError):
    """Raised when execution is cancelled by query coordinator."""
    pass

class QueryPlannerError(QueryError):
    """Raised when planner fails to build logical stages."""
    pass

class QueryOptimizerError(QueryError):
    """Raised when optimizer rewrite rules fail."""
    pass

class CatalogNotFoundError(QueryError):
    """Raised when referenced table catalog is missing."""
    pass

class FunctionNotFoundError(QueryError):
    """Raised when function registry lookup fails."""
    pass

class InvalidAggregationError(QueryError):
    """Raised when query has malformed group fields."""
    pass

class JoinPlanningError(QueryError):
    """Raised when join paths cannot be computed."""
    pass
