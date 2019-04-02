from mcserver.events.event_base import Event


class HandshakeEvent(Event):
    def __init__(self, event: str, *args):
        super().__init__(event, *args)
        self.hostname: str = args[0]
        self.port: int = args[1]
