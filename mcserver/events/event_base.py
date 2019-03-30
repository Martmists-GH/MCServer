# Stdlib
from abc import ABC
from typing import Any


class Event(ABC):
    def __init__(self, event_name: str, args: Any):
        self.event = event_name
        if not isinstance(args, tuple):
            args = (args, )
        self.args = args
