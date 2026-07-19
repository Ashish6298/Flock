"""Internal Event Bus enabling decoupled pub-sub communication across local modules."""

import asyncio
from typing import Dict, List, Callable, Awaitable, Any

class EventBus:
    """Publish-subscribe engine facilitating communication between local framework services."""

    def __init__(self) -> None:
        self._listeners: Dict[str, List[Callable[[Any], Awaitable[None]]]] = {}

    def subscribe(self, event_type: str, callback: Callable[[Any], Awaitable[None]]) -> None:
        """Register local callback for specific local event string notifications."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[Any], Awaitable[None]]) -> None:
        """Remove subscriber from notification list."""
        if event_type in self._listeners:
            try:
                self._listeners[event_type].remove(callback)
            except ValueError:
                pass

    async def publish(self, event_type: str, event_data: Any) -> None:
        """Publish local event, executing all registered subscribers concurrently."""
        callbacks = self._listeners.get(event_type, [])
        if not callbacks:
            return
        
        # Fire all subscribers concurrently
        tasks = [callback(event_data) for callback in callbacks]
        await asyncio.gather(*tasks, return_exceptions=True)
