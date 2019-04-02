from __future__ import annotations

# Stdlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcserver.classes.client_connection import ClientConnection


class Event:
    def __init__(self, event: str, *args):
        self.event = event
        self.args = args
        self._conn: ClientConnection = None

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(map(repr, self.args))})"
