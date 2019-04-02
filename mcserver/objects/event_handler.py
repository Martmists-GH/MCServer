# Future patches
from __future__ import annotations

# Stdlib
from functools import wraps
from typing import TYPE_CHECKING

# MCServer
from quarry.data import packets

from mcserver.events.event_base import Event
from mcserver.objects.player_registry import PlayerRegistry
from mcserver.objects.server_core import ServerCore
from mcserver.utils.misc import read_favicon

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
            "event_handshake", "event_status", "event_connect_16", "event_ping"
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
    async def event_connect_16(cls, evt: Event):
        pass

    @classmethod
    async def event_status(cls, evt: Event):
        data = {
            "description": {
                "text": ServerCore.options["motd"]
            },
            "players": {
                "online": PlayerRegistry.player_count(),
                "max": ServerCore.options["max-players"]
            },
            "version": {
                "name": packets.minecraft_versions.get(
                    evt._conn.protocol_version,
                    "???"),
                "protocol": evt._conn.protocol_version,
            }
        }
        favicon = read_favicon()
        if favicon:
            data["favicon"] = f"data:image/png;base64,{favicon}"

        evt._conn.send_packet("status", data)

    @classmethod
    async def event_ping(cls, evt: Event):
        evt._conn.send_packet("pong", evt.args[0])
