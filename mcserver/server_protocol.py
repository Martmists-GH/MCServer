from copy import deepcopy

from quarry.net.server import ServerProtocol

from mcserver.event_handler import EventHandler


class MCServerProtocol(ServerProtocol):
    def player_joined(self):
        super().player_joined()
        EventHandler.player_join(self)

    def player_left(self):
        super().player_left()
        EventHandler.player_join(self)

    def packet_unhandled(self, buff, name):
        copy_buff = deepcopy(buff)
        buff.discard()
        EventHandler.handle_event(self, copy_buff, name)
