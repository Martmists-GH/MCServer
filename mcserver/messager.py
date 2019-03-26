import numpy as np
from quarry.net.protocol import Protocol

from mcserver.server_factory import MCServer


if False:
    from mcserver.entities.player_entity import Player
    from mcserver.entities.entity_base import Entity


class Messager:
    buff_type = MCServer.buff_type

    @classmethod
    def send_chat(cls, message: str):
        data = cls.buff_type.pack_chat(message) + cls.buff_type.pack('B', 0)
        for player in MCServer.players:
            player.send_packet("chat_message", data)

    @classmethod
    def send_chat_player(cls, player: Protocol, message: str):
        data = cls.buff_type.pack_chat(message) + cls.buff_type.pack('B', 0)
        player.send_packet("chat_message", data)

    @classmethod
    def send_entity_moved(cls, entity: 'Entity', delta_pos: np.ndarray, on_ground: bool):
        data = cls.buff_type.pack_varint(entity.ent_id) + \
               cls.buff_type.pack("hhhb", *map(int, delta_pos), on_ground)
        for player in MCServer.players:
            player.send_packet("entity_relative_move", data)

    @classmethod
    def send_spawn_player(cls, target: Protocol, player: 'Player'):
        data = (cls.buff_type.pack_varint(player.ent_id) +
                cls.buff_type.pack_uuid(player.uuid) +
                cls.buff_type.pack("dddbb", *player.position, *player.rotation) + b'\xff')
        target.send_packet("spawn_player", data)
