from mcserver.events.event_base import Event


class PlayerJoinEvent(Event):
    def __init__(self, event: str, *args):
        super().__init__(event, *args)
        self.player = args[0]


class PlayerLeaveEvent(Event):
    def __init__(self, event: str, *args):
        super().__init__(event, *args)
        self.player = args[0]
