"""Performance Timer Engine capturing high-resolution execution durations."""

from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, cast

T = TypeVar("T", bound=Callable[..., Any])


class PerformanceTimer:
    """Scoped execution context timer utilizing perf_counter."""

    def __init__(self, name: str, callback: Optional[Callable[[float], None]] = None) -> None:
        self.name = name
        self.callback = callback
        self.start_time: float = 0.0
        self.duration: float = 0.0

    def __enter__(self) -> PerformanceTimer:
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.duration = (time.perf_counter() - self.start_time) * 1000.0  # ms
        if self.callback:
            self.callback(self.duration)


def time_execution(
    name: str, callback: Optional[Callable[[float], None]] = None
) -> Callable[[T], T]:
    """Decorator to time method executions."""

    def decorator(func: T) -> T:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = (time.perf_counter() - start) * 1000.0
                if callback:
                    callback(duration)

        return cast(T, wrapper)

    return decorator
