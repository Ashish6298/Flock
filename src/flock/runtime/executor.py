"""Abstract and concrete executor backend implementations."""

import abc
import asyncio
import concurrent.futures
from typing import Any, Callable, TypeVar, Coroutine
from flock.runtime.context import ExecutionContext

T = TypeVar("T")

class Executor(abc.ABC):
    """Abstract interface defining the execution submit operations."""

    @abc.abstractmethod
    async def submit(self, func: Callable[..., T], *args: Any, context: ExecutionContext) -> T:
        """Submit a callable for execution."""
        pass


class ThreadPoolExecutorBackend(Executor):
    """Executes callables inside a local thread pool."""

    def __init__(self, max_workers: int = 4) -> None:
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    async def submit(self, func: Callable[..., T], *args: Any, context: ExecutionContext) -> T:
        loop = asyncio.get_running_loop()
        
        # Define wrapper executing checks
        def wrapper() -> T:
            context.check_cancellation()
            res = func(*args)
            context.check_cancellation()
            return res

        future = self.pool.submit(wrapper)
        
        # Async wait wrapper supporting cancel tokens
        while not future.done():
            if context.is_cancelled():
                future.cancel()
                raise asyncio.CancelledError()
            await asyncio.sleep(0.05)
            
        return future.result()

    def shutdown(self) -> None:
        """Close executor pool."""
        self.pool.shutdown(wait=True)


class ProcessPoolExecutorBackend(Executor):
    """Executes callables inside isolated processes."""

    def __init__(self, max_workers: int = 2) -> None:
        self.pool = concurrent.futures.ProcessPoolExecutor(max_workers=max_workers)

    async def submit(self, func: Callable[..., T], *args: Any, context: ExecutionContext) -> T:
        loop = asyncio.get_running_loop()
        
        def wrapper() -> T:
            # Note: Context cancellation checks require process communication.
            # In Phase 9, we run basic wrapper evaluations.
            return func(*args)

        future = self.pool.submit(wrapper)
        
        while not future.done():
            if context.is_cancelled():
                future.cancel()
                raise asyncio.CancelledError()
            await asyncio.sleep(0.05)
            
        return future.result()

    def shutdown(self) -> None:
        """Close process executor pool."""
        self.pool.shutdown(wait=True)


class AsyncExecutorBackend(Executor):
    """Executes coroutines directly on the active event loop."""

    async def submit(self, func: Callable[..., Any], *args: Any, context: ExecutionContext) -> Any:
        context.check_cancellation()
        # Expecting func to be coroutine function
        coro = func(*args)
        if not asyncio.iscoroutine(coro):
            # Fallback if standard function provided
            return func(*args)
            
        task = asyncio.create_task(coro)
        
        try:
            while not task.done():
                if context.is_cancelled():
                    task.cancel()
                    raise asyncio.CancelledError()
                await asyncio.sleep(0.05)
            return await task
        except asyncio.CancelledError:
            task.cancel()
            raise
