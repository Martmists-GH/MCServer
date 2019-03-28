from __future__ import annotations

import random
import numpy as np
from typing import TYPE_CHECKING
from uuid import UUID

from aiohttp import ClientSession
from quarry.data import packets
from quarry.net.crypto import decrypt_secret, make_digest
from quarry.net.protocol import protocol_modes

from mcserver.classes.player import Player
from mcserver.utils.logger import error, debug
from mcserver.objects.player_registry import PlayerRegistry
from mcserver.objects.server_core import ServerCore

if TYPE_CHECKING:
    from mcserver.classes.client_message import ClientMessage
    from typing import Awaitable, Optional


class PacketHandler:
    @classmethod
    def update_protocol(cls, msg: ClientMessage, mode: str):
        if mode == "play":
            if msg.compression_threshold:
                # Send set compression
                msg.send_packet(
                    "login_set_compression",
                    msg.buffer_type.pack_varint(msg.compression_threshold))

            # Send login success
            msg.send_packet(
                "login_success",
                msg.buffer_type.pack_string(str(msg.conn.uuid)) +
                msg.buffer_type.pack_string(msg.conn.display_name))

        elif mode == "login":
            if PlayerRegistry.player_count() >= ServerCore.options["max-players"]:
                msg.close_connection("Server is full!")

        msg.conn.protocol_state = mode

    # === DECODE ===

    @classmethod
    def decode(cls, msg: ClientMessage) -> Optional[Awaitable]:
        debug(f"Handling packet: {msg}")
        func = getattr(cls,
                       "decode_" + msg.name,
                       lambda _, err=f"Unhandled packet type: {msg.name}": error(err) or msg.close_connection(err))
        return func(msg)

    @classmethod
    def decode_keep_alive(cls, msg: ClientMessage):
        pass

    @classmethod
    def decode_teleport_confirm(cls, msg: ClientMessage):
        pass

    @classmethod
    def decode_animation(cls, msg: ClientMessage):
        animation = msg.buffer.unpack_varint()

    @classmethod
    def decode_client_settings(cls, msg: ClientMessage):
        buf = msg.buffer
        locale = buf.unpack_string()
        view_distance = buf.unpack("b")
        chat_mode = buf.unpack_varint()
        chat_colors, displayed_skin = buf.unpack("?b")
        main_hand = buf.unpack_varint()

    @classmethod
    def decode_plugin_message(cls, msg: ClientMessage):
        buf = msg.buffer
        channel = buf.unpack_string()
        pass

    @classmethod
    async def decode_handshake(cls, msg: ClientMessage):
        buffer = msg.buffer
        msg.set_protocol_version(buffer.unpack_varint())
        hostname = buffer.unpack_string()
        port = buffer.unpack("H")
        next_state = buffer.unpack_varint()

        mode = protocol_modes.get(next_state, next_state)
        msg.conn.protocol_state = mode

        cls.update_protocol(msg, mode)

    @classmethod
    async def decode_player_position_and_look(cls, msg: ClientMessage):
        player = msg.conn.player
        buf = msg.buffer
        player.entity.position = np.array(buf.unpack("ddd"))
        player.entity.rotation = np.array(buf.unpack("ff"))
        player.entity.on_ground = buf.unpack("?")

    @classmethod
    async def decode_status_request(cls, msg: ClientMessage):
        d = {
            "description": {
                "text": ServerCore.options["motd"]
            },
            "players": {
                "online": PlayerRegistry.player_count(),
                "max": ServerCore.options["max-players"]
            },
            "version": {
                "name": packets.minecraft_versions.get(
                    msg.protocol_version,
                    "???"),
                "protocol": msg.protocol_version
            }
        }
        # TODO: Server icon

        msg.send_packet(
            "status_response",
            msg.buffer_type.pack_json(d)
        )

    @classmethod
    async def decode_chat_message(cls, msg: ClientMessage) -> str:
        return msg.buffer.unpack_string()

    @classmethod
    async def decode_status_ping(cls, msg: ClientMessage):
        time = msg.buffer.unpack("Q")
        msg.send_packet("status_pong", msg.buffer_type.pack("Q", time))

    @classmethod
    async def decode_login_start(cls, msg: ClientMessage):
        msg.conn.display_name = msg.buffer.unpack_string()

        if ServerCore.options["online-mode"]:
            # 1.7.x
            if msg.protocol_version <= 5:
                pack_array = lambda a: msg.buffer_type.pack('h', len(a)) + a
            else:
                pack_array = lambda a: msg.buffer_type.pack_varint(len(a), max_bits=16) + a

            msg.send_packet("login_encryption_request",
                            msg.buffer_type.pack_string(msg.conn.server_id) +
                            pack_array(ServerCore.pubkey) +
                            pack_array(msg.conn.verify_token))
        else:
            # TODO
            pass

    @classmethod
    async def decode_login_encryption_response(cls, msg: ClientMessage) -> ...:
        # 1.7.x
        if msg.protocol_version <= 5:
            unpack_array = lambda b: b.read(b.unpack('h'))
        else:
            unpack_array = lambda b: b.read(b.unpack_varint(max_bits=16))

        buffer = msg.buffer
        p_shared_secret = unpack_array(buffer)
        p_shared_verify = unpack_array(buffer)
        shared_secret = decrypt_secret(ServerCore.keypair, p_shared_secret)
        shared_verify = decrypt_secret(ServerCore.keypair, p_shared_verify)

        if shared_verify != msg.conn.verify_token:
            msg.close_connection("Invalid verify token!")

        msg.conn.cipher.enable(shared_secret)

        digest = make_digest(msg.conn.server_id.encode("ascii"),
                             shared_secret,
                             ServerCore.pubkey)

        url = ("https://sessionserver.mojang.com/session/minecraft/hasJoined" +
               f"?username={msg.conn.display_name}&serverId={digest}")
        if ServerCore.options["prevent-proxy-connections"]:
            url += f"&ip={msg.conn.client.server_hostname}"

        async with ClientSession() as session:
            async with session.get(url, timeout=ServerCore.auth_timeout) as resp:
                data = await resp.json()
                msg.conn.uuid = UUID(data["id"])

        cls.update_protocol(msg, "play")
        return PlayerRegistry.add_player(msg.conn)

    @classmethod
    async def packet_teleport_confirm(cls, msg: ClientMessage):
        if msg.conn.player._cache["TID"] != msg.buffer.unpack_varint():
            msg.close_connection("Player couldn't confirm Teleport ID")

    @classmethod
    async def packet_chat_message(cls, msg: ClientMessage):
        message = msg.buffer.unpack_string()
        packet = msg.build_packet("chat_message", msg.buffer_type.pack_chat(message))
        for player in PlayerRegistry.players:
            player.conn.send_packet(packet)

    # === ENCODE ===

    @classmethod
    async def encode_player_info(cls, msg: ClientMessage, target_player: Player, player_updated: Player, action: int):
        player_packet = player_updated.uuid.bytes

        display_name = None if player_updated.display_name == player_updated.name else player_updated.display_name

        if action == 0:
            player_packet += (
                msg.buffer_type.pack_string(player_updated.name) +
                msg.buffer_type.pack_varint(len(player_updated.properties)) +
                player_updated.pack_properties(msg.buffer_type) +
                msg.buffer_type.pack_varint(player_updated.gamemode) +
                msg.buffer_type.pack_varint(player_updated.ping) +
                msg.buffer_type.pack("?", player_updated.display_name != player_updated.name) +
                msg.buffer_type.pack_optional(msg.buffer_type.pack_chat, display_name)
            )
        elif action == 1:
            player_packet += msg.buffer_type.pack_varint(player_updated.gamemode)
        elif action == 2:
            player_packet += msg.buffer_type.pack_varint(player_updated.ping)
        elif action == 3:
            player_packet += (
                msg.buffer_type.pack("?", player_updated.display_name != player_updated.name) +
                msg.buffer_type.pack_optional(msg.buffer_type.pack_chat, display_name)
            )
        elif action == 4:
            pass
        else:
            raise Exception

        target_player.conn.send_packet(
            msg.build_packet(
                "player_list_item",
                msg.buffer_type.pack_varint(action) +
                msg.buffer_type.pack_varint(1) +
                msg.buffer.pack_array("", player_packet)
            )
        )

    @classmethod
    async def encode_player_join(cls, msg: ClientMessage, player: Player):
        msg.send_packet(
            "join_game",
            msg.buffer_type.pack(
                "iBiBB",
                player.entity.id, player.gamemode, player.entity.dimension,
                ServerCore.options["difficulty"], ServerCore.options["max-players"]
            ) +
            msg.buffer.pack_string("default") +
            msg.buffer_type.pack("?", False)
        )

    @classmethod
    async def encode_player_spawn(cls, msg: ClientMessage, target_player: Player, player: Player):
        target_player.conn.send_packet(
            msg.build_packet(
                "spawn_player",
                msg.buffer_type.pack_varint(player.entity.id) +
                player.uuid.bytes +
                msg.buffer_type.pack("ddd", *player.entity.position) +
                msg.buffer_type.pack("ff", *player.entity.rotation) +
                player.entity.pack_metadata(msg.buffer_type)
            )
        )

    @classmethod
    async def encode_player_position_look(cls, msg: ClientMessage, player: Player):
        teleport_id = random.randint(0, 2**20)

        msg.send_packet(
            "player_position_and_look",
            msg.buffer_type.pack("ddd", *player.entity.position) +
            msg.buffer_type.pack("ff", *player.entity.rotation) +
            msg.buffer_type.pack("b", player.entity.flags) +
            msg.buffer_type.pack_varint(teleport_id)
        )

        teleport_packet = await msg.conn.wait_for_packet("teleport_confirm")
        verify = teleport_packet.unpack_varint()
        if teleport_id != verify:
            msg.close_connection("Invalid Teleport ID packet")

    @classmethod
    async def encode_player_spawn_pos(cls, msg: ClientMessage, player: Player):
        msg.send_packet(
            "spawn_position",
            msg.buffer_type.pack_position(*player.entity.position)
        )

    @classmethod
    async def encode_player_abilities(cls, msg: ClientMessage, player: Player):
        player.conn.send_packet(
            msg.build_packet(
                "player_abilities",
                msg.buffer_type.pack("bff", player.entity.abilities, player.entity.fly_speed, player.entity.walk_speed)
            )
        )

    @classmethod
    async def encode_chat_message(cls, msg: ClientMessage, target_player: Player, message: str):
        buf = msg.buffer_type.pack_chat(message) + msg.buffer_type.pack("b", 0)
        target_player.conn.send_packet(
            msg.build_packet("chat_message", buf)
        )
