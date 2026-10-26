import asyncio
from collections import defaultdict
from typing import Callable, Any
from loguru import logger


class EventBus:
    """
    A simple pub/sub system to decouple the RCON core from the GUI.
    """
    def __init__(self):
        self._subs: dict[str, list[Callable]] = defaultdict(list)

    def on(self, event: str, handler: Callable):
        """Subscribe a handler to an event."""
        self._subs[event].append(handler)

    async def emit(self, event: str, payload: Any = None):
        """Emit an event to all subscribers."""
        for handler in self._subs.get(event, []):
            try:
                result = handler(payload)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"EventBus handler error on '{event}': {e}")


# Global event bus instance
bus = EventBus()