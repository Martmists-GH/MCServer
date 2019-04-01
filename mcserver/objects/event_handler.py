# Future patches
from __future__ import annotations

# Stdlib
from functools import wraps
from typing import TYPE_CHECKING

# MCServer
from mcserver.events.event_base import Event

if TYPE_CHECKING:
    from typing import List, Callable, Dict, Optional


def event(event_name: Optional[str] = None):
    def decorator(func: Callable):

        _event = event_name or func.__name__

        @wraps
        def inner(*args, **kwargs):
            return func(*args, **kwargs)

        if _event not in EventHandler.listeners:
            raise ValueError(f"Invalid event name: {_event}!"
                             " If this is a non-standard event, make sure your dependencies loaded!")

        EventHandler.listeners[_event].append(_event)

        return inner
    return decorator


def register_event(event_name: str):
    EventHandler.listeners[event_name] = []


class EventHandler:
    listeners: Dict[str, List[Callable]] = {
        key: []
        for key in (
            "player_join", "player_leave", ...
        )
    }

    @classmethod
    async def handle_event(cls, evt: Event):
        _event = f"event_{evt.event}"
        func = getattr(cls, _event)
        await func(evt)
        for listener in cls.listeners[_event]:
            await listener(evt)

    # TODO:
    # Implement all events
    @classmethod
    async def event_handshake(cls, evt: Event):
        pass

    @classmethod
    async def event_status(cls, evt: Event):
        # evt._conn.send_packet("status", {...})
        pass
