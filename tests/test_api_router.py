"""Unit tests for ApiRouter."""

import pytest
from flock.api.exceptions import RouteNotFoundError
from flock.api.models import ApiRoute
from flock.api.router import ApiRouter


def test_router_registrations() -> None:
    router = ApiRouter()
    route = ApiRoute(path="/tasks", method="GET", handler_name="get_tasks")

    def mock_handler() -> str:
        return "tasks"

    router.register_route(route, mock_handler)
    matched = router.match_and_dispatch("GET", "/tasks")
    assert matched() == "tasks"

    # Route mismatch raises RouteNotFoundError
    with pytest.raises(RouteNotFoundError):
        router.match_and_dispatch("POST", "/tasks")
