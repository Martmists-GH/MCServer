import random

from quarry.net.protocol import Protocol

from mcserver.entities.entity_base import Entity
from mcserver.messager import Messager


class Player(Entity):
    def __init__(self, prot: Protocol):
        super().__init__()
        self.uuid = prot.uuid
        self.prot = prot
        self.gamemode = 0
        self.dimension = 0
        self.health = 20
        self.max_health = 20
        self.last_ka_packet = 0

    def join(self):
        self.prot.send_packet(
            "join_game",
            self.prot.buff_type.pack(
                "iBiBB", self.ent_id, self.gamemode, self.dimension, 25, 0),
            self.prot.buff_type.pack_string("flat"),
            self.prot.buff_type.pack("?", False)
        )
        self.prot.send_packet(
            "player_position_and_look",
            self.prot.buff_type.pack("dddffb", *self.position, *self.rotation, self.on_ground),
            self.prot.buff_type.pack_varint(0)
        )
        Messager.send_spawn_player(self.prot, self)
        self.__tick_player()

    def __tick_player(self):
        def keep_alive():
            num = random.randint(0, 99999999)
            self.last_ka_packet = num

            # 1.7.x
            if self.prot.protocol_version <= 338:
                payload = self.prot.buff_type.pack_varint(num)
            # 1.12.2
            else:
                payload = self.prot.buff_type.pack('Q', num)
            self.prot.send_packet("keep_alive", payload)

        self.prot.ticker.add_loop(50, keep_alive)

    def pack_metadata(self, bt) -> bytes:
        # TODO
        return b"\xff"

    # TODO: Save/Load player data

    def load(self):
        pass

    def save(self):
        pass
