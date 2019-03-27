from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from aiohttp import ClientSession
from quarry.data import packets
from quarry.net.crypto import decrypt_secret, make_digest
from quarry.net.protocol import protocol_modes
from rewrite.logger import error, debug
from rewrite.player_registry import PlayerRegistry
from rewrite.server_core import ServerCore

if TYPE_CHECKING:
    from rewrite.client_message import ClientMessage
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

    @classmethod
    def decode(cls, msg: ClientMessage) -> Optional[Awaitable]:
        debug(f"Handling packet: {msg}")
        func = getattr(cls,
                       "decode_" + msg.name,
                       lambda _, err=f"Unhandled packet type: {msg.name}": error(err) or msg.close_connection(err))
        return func(msg)

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
    async def decode_login_encryption_response(cls, msg: ClientMessage):
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
