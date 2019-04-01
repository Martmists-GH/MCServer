# Stdlib
from abc import ABC
from typing import Any


class Event(ABC):
    def __init__(self, event_name: str, args: Any):
        self.event = event_name
        if not isinstance(args, tuple):
            args = tuple(args) if isinstance(args, list) else (args, )
        self.args = args
        self._conn = None

    def __repr__(self):
        return f"Event(name={self.event}, args={self.args}"
