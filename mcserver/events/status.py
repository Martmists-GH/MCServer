from mcserver.events.event_base import Event


class PingEvent(Event):
    def __init__(self, event: str, *args):
        super().__init__(event, *args)
        self.value: int = args[0]


class StatusEvent(Event):
    pass


class Connect16Event(Event):
    def __init__(self, event: str, *args):
        super().__init__(event, *args)
        self.protocol: int = args[0]
        self.hostname: str = args[1]
        self.port: int = args[2]
