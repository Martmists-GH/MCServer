from copy import deepcopy

import numpy as np
from quarry.net.protocol import Protocol

from mcserver.messager import Messager
from mcserver.player_handler import PlayerHandler
from mcserver.plugin_manager import PluginManager


class EventHandler:
    player_handler = PlayerHandler()

    @classmethod
    def handle_event(cls, player: Protocol, buffer, name):
        copy_buff = deepcopy(buffer)
        PluginManager.handle_event(player, buffer, name)
        func = getattr(cls, f"packet_{name}",
                       lambda *_: print(f"Unhandled packet_{name} with data {copy_buff.read()}"))
        func(player, copy_buff)

    # Player join/leave

    @classmethod
    def player_join(cls, player: Protocol):
        Messager.send_chat(f"\u00a7e{player.display_name} has joined.")
        player_obj = cls.player_handler.get_player(player)
        player_obj.join()

    @classmethod
    def player_left(cls, player: Protocol):
        Messager.send_chat(f"\u00a7e{player.display_name} has left.")
        cls.player_handler.remove_player(player)

    # Packet events
    @classmethod
    def packet_keep_alive(cls, player: Protocol, buff):
        # 1.7.x
        if player.protocol_version <= 338:
            num = buff.unpack_varint()
        # 1.12.2
        else:
            num = buff.unpack('Q')

        exp_num = cls.player_handler.get_player(player).last_ka_packet

        if num != exp_num:
            player.close(f"Invalid Keep-Alive value: Got {num}, expected {exp_num}")

    @classmethod
    def packet_client_settings(cls, player: Protocol, buff):
        pass

    @classmethod
    def packet_player_position_and_look(cls, player: Protocol, buff):
        x, y, z, yaw, pitch, on_ground = buff.unpack("dddffb")
        player_obj = cls.player_handler.get_player(player)
        player_obj.moved(np.array([x, y, z]), on_ground)
        # player_obj.position = (x, y, z)
        # player_obj.rotation = (yaw, pitch)
        # player_obj.on_ground = on_ground
