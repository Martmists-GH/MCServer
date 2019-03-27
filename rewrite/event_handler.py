from __future__ import annotations

from typing import TYPE_CHECKING

from rewrite.logger import error

if TYPE_CHECKING:
    from typing import Tuple, Any
    from rewrite.client_message import ClientMessage


def remap_name(name: str) -> str:
    if name in ("handshake", "status_request", "status_ping", "login_start"):
        # Don't pass these to events
        return ""
    if name == "login_encryption_response":
        return "player_join"
    return name


class EventHandler:
    @classmethod
    def handle_event(cls, msg: ClientMessage, args: Tuple[Any]):
        event = remap_name(msg.name)
        if event:
            func = getattr(cls, "event_"+event, lambda *_: error(f"Unhandled event: {event}"))
            if args:
                return func(*[msg, *args])
            else:
                return func(msg)
