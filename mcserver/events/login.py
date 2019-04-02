from mcserver.events.event_base import Event


class LoginStartEvent(Event):
    def __init__(self, event: str, *args):
        super().__init__(event, *args)
        self.username: str = args[0]


class ConfirmEncryptionEvent(Event):
    def __init__(self, event: str, *args):
        super().__init__(event, *args)
        self.secret: bytes = args[0]
        self.verify: bytes = args[1]
