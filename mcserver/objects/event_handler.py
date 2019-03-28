from __future__ import annotations

import random
from typing import TYPE_CHECKING

import anyio

from mcserver.classes.player import Player
from mcserver.objects.packet_handler import PacketHandler
from mcserver.objects.player_registry import PlayerRegistry
from mcserver.utils.logger import error

if TYPE_CHECKING:
    from typing import Tuple, Any
    from mcserver.classes.client_message import ClientMessage


def _remap_name(name: str) -> str:
    if name in ("handshake", "status_request", "status_ping", "login_start", "keep_alive"):
        # Don't pass these to events
        return ""
    if name == "login_encryption_response":
        return "player_join"
    return name


class EventHandler:
    @classmethod
    def handle_event(cls, msg: ClientMessage, args: Tuple[Any]):
        event = _remap_name(msg.name)
        if event:
            func = getattr(cls, "event_"+event, lambda *_: error(f"Unhandled event: {event}"))
            if args:
                if not isinstance(args, tuple):
                    args = (args, )
                return func(msg, *args)
            else:
                return func(msg)

    @classmethod
    async def event_chat_message(cls, msg: ClientMessage, message: str):
        for player in PlayerRegistry.players:
            await PacketHandler.encode_chat_message(msg, player, f"<{msg.conn.player.display_name}> {message}")

    @classmethod
    async def event_player_join(cls, msg: ClientMessage, player: Player):
        for _player in PlayerRegistry.players:
            # PacketHandler.encode_player_info(msg, player, _player, 0)
            await PacketHandler.encode_chat_message(msg, _player, f"\u00a7e{player.display_name} has joined.")

        await PacketHandler.encode_player_join(msg, player)
        await PacketHandler.encode_player_spawn_pos(msg, player)
        await PacketHandler.encode_player_position_look(msg, player)
        await PacketHandler.encode_player_spawn(msg, player, player)
        while msg.conn.do_loop:
            val = random.randint(0, 2**20)
            msg.send_packet(
                "keep_alive",
                msg.buffer_type.pack_varint(val) if msg.protocol_version <= 338 else msg.buffer_type.pack("Q", val)
            )
            keep_alive_packet = await msg.conn.wait_for_packet("keep_alive")

            # 1.7.x
            if msg.protocol_version <= 338:
                verify = keep_alive_packet.unpack_varint()
            else:
                verify = keep_alive_packet.unpack("Q")

            if val != verify:
                msg.close_connection("Invalid KeepAlive packet!")
                return

            await anyio.sleep(1)
