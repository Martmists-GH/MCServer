# Future patches
from __future__ import annotations

# Stdlib
from functools import wraps
from typing import TYPE_CHECKING

# MCServer
from uuid import UUID

import asks
from anyio import fail_after
from asks import Session
from quarry.data import packets

from mcserver.events.event_base import Event
from mcserver.events.init import HandshakeEvent
from mcserver.events.login import LoginStartEvent, ConfirmEncryptionEvent
from mcserver.events.status import Connect16Event, StatusEvent, PingEvent
from mcserver.events.play import PlayerLeaveEvent
from mcserver.objects.player_registry import PlayerRegistry
from mcserver.objects.server_core import ServerCore
from mcserver.utils.cryptography import make_digest
from mcserver.utils.logger import info
from mcserver.utils.misc import read_favicon
from mcserver.game.abc.entity_base import Look

if TYPE_CHECKING:
    from typing import List, Callable, Dict, Optional


def event(event_name: Optional[str] = None):
    def decorator(func: Callable):
        _event = event_name or func.__name__

        @wraps
        def inner(*args, **kwargs):
            return func(*args, **kwargs)

        if _event not in EventHandler.listeners:
            raise ValueError(f"Invalid event name: {_event}!"
                             " If this is a non-standard event, make sure your dependencies loaded!")

        EventHandler.listeners[_event].append(_event)

        return inner

    return decorator


def register_event(event_name: str):
    EventHandler.listeners[event_name] = []


class EventHandler:
    listeners: Dict[str, List[Callable]] = {
        key: []
        for key in (
            "event_handshake", "event_status", "event_connect_16", "event_ping", "event_login_start",
            "event_login_encryption", "event_player_leave"
        )
    }

    @classmethod
    async def handle_event(cls, evt: Event):
        _event = f"event_{evt.event}"
        func = getattr(cls, _event)
        await func(evt)
        for listener in cls.listeners[_event]:
            await listener(evt)

    # TODO:
    # Implement all events
    @classmethod
    async def event_handshake(cls, evt: HandshakeEvent):
        pass

    @classmethod
    async def event_connect_16(cls, evt: Connect16Event):
        pass

    @classmethod
    async def event_status(cls, evt: StatusEvent):
        data = {
            "description": {
                "text": ServerCore.options["motd"]
            },
            "players": {
                "online": PlayerRegistry.player_count(),
                "max": ServerCore.options["max-players"]
            },
            "version": {
                "name": packets.minecraft_versions.get(
                    evt._conn.protocol_version,
                    "???"),
                "protocol": evt._conn.protocol_version,
            }
        }
        favicon = read_favicon()
        if favicon:
            data["favicon"] = f"data:image/png;base64,{favicon}"

        evt._conn.send_packet("status", data)

    @classmethod
    async def event_ping(cls, evt: PingEvent):
        evt._conn.send_packet("pong", evt.value)

    @classmethod
    async def event_login_start(cls, evt: LoginStartEvent):
        evt._conn.name = evt.username

        if ServerCore.options["online-mode"]:
            evt._conn.send_packet(
                "encryption_start",
                evt._conn.server_id,
                evt._conn.verify_token
            )
        else:
            # TODO: Offline mode
            pass

    @classmethod
    async def event_login_encryption(cls, evt: ConfirmEncryptionEvent):
        if evt.verify != evt._conn.verify_token:
            raise Exception("Invalid verification token!")

        evt._conn.cipher.enable(evt.secret)
        digest = make_digest(
            evt._conn.server_id.encode(),
            evt.secret,
            ServerCore.pubkey
        )

        url = "https://sessionserver.mojang.com/session/minecraft/hasJoined"
        params = {
            "username": evt._conn.name,
            "serverId": digest
        }
        if ServerCore.options["prevent-proxy-connections"]:
            params["ip"] = evt._conn.client.server_hostname

        async with fail_after(ServerCore.auth_timeout):  # FIXME: Fails on curio
            resp = await asks.get(url, params=params)
            data = resp.json()
            info(data)
            evt._conn.uuid = UUID(data["id"])

        evt._conn.packet_decoder.status = 3

        await cls.login_success(evt._conn, evt._conn.uuid, evt._conn.name)  # Init complete. TODO: Switch to play mode

        return PlayerRegistry.add_player(evt._conn)

    @classmethod
    async def login_success(cls, conn, *args):
        # This is not an event. This might get moved or something
        conn.packet_decoder.status = 3  # Set the connection to the play state
        conn.send_packet("login_success", *args)

        # A lot of these are placeholder content

        conn.send_packet("join_game", 0, 0, 0, 0, 20, "default", False)
        conn.send_packet("spawn_position", [0, 63, 0])
        d = {"Invulnerable": False, "Flying": False, "Allow Flying": True, "Instant Break": True}
        conn.send_packet("player_abilities", d, 0.05, 0.1)
        conn.send_packet("player_pos_and_look", Look(), 0)

    @classmethod
    async def event_player_leave(cls, evt: PlayerLeaveEvent):
        PlayerRegistry.players.remove(evt.player)
