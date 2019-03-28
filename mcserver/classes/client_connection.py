from __future__ import annotations

from typing import TYPE_CHECKING
from traceback import format_exc
from uuid import UUID

from anyio import create_task_group, sleep, create_event
from anyio.exceptions import TLSRequired
from quarry.net.crypto import Cipher, make_server_id, make_verify_token
from quarry.types.buffer import BufferUnderrun

from mcserver.classes.client_message import ClientMessage
from mcserver.classes.player import Player
from mcserver.objects.event_handler import EventHandler
from mcserver.utils.logger import warn, debug, error
from mcserver.objects.packet_handler import PacketHandler
from mcserver.objects.player_registry import PlayerRegistry

if TYPE_CHECKING:
    from typing import List, Dict, Union, Optional
    from anyio import SocketStream, Event
    from mcserver.utils.misc import AnyBuffer


class ClientConnection:
    def __init__(self, client: SocketStream):
        self.client = client
        self.do_loop = True
        self.protocol_state = "init"
        self.messages: List[bytes] = []
        self._locks: List[
            Dict[str,
                 Union[
                     str,
                     Event,
                     Optional[AnyBuffer]
                 ]]
        ] = []
        self.server_id = make_server_id()
        self.verify_token = make_verify_token()
        self.cipher = Cipher()
        self.display_name = ""
        self.uuid: UUID = None

    @property
    def player(self) -> Player:
        return PlayerRegistry.get_player(self.uuid)

    def __repr__(self):
        return (f"ClientConnection(loop={self.do_loop}, "
                f"message_queue={len(self.messages)}, "
                f"lock_queue={len(self._locks)})")

    async def serve(self):
        async with create_task_group() as tg:
            await tg.spawn(self.serve_loop)
            await tg.spawn(self.write_loop)

    async def serve_loop(self):
        data = b""
        async with create_task_group() as tg:
            while self.do_loop:
                try:
                    line = await self.client.receive_some(1)
                except ConnectionError:
                    line = b""

                if line == b"":
                    try:
                        warn(f"Closing connection to {self.client.server_hostname}")
                    except TLSRequired:
                        pass

                    self.do_loop = False
                    break

                data += self.cipher.decrypt(line)

                try:
                    msg = ClientMessage(self, data)
                except BufferUnderrun:
                    continue
                else:
                    data = b""

                for lock in self._locks:
                    if lock["name"] == msg.name:
                        self._locks.remove(lock)
                        lock["result"] = msg.buffer
                        await lock["lock"].set()
                        break

                if msg.name == "handshake":
                    await self.handle_msg(msg)
                else:
                    await tg.spawn(self.handle_msg, msg)

            for lock in self._locks:
                await lock["lock"].set()
            if self.protocol_state == "play":
                # User was logged in
                debug("Player left, removing from game...")
                PlayerRegistry.players.remove(self.player)

    async def handle_msg(self, msg: ClientMessage):
        try:
            coro = PacketHandler.decode(msg)
            if coro:
                args = await coro
                coro2 = EventHandler.handle_event(msg, args)
                if coro2:
                    await coro2
        except Exception:
            error(f"Exception occurred:\n{format_exc()}")

    async def write_loop(self):
        while self.do_loop:
            if self.messages:
                msg = self.messages.pop(0)
                debug(f"Sending to client: {msg}")
                await self.client.send_all(msg)
            else:
                await sleep(0.00001)  # Allow other tasks to run

    async def wait_for_packet(self, packet_name: str) -> AnyBuffer:
        lock = {
            "name": packet_name,
            "lock": create_event(),
            "result": None
        }

        self._locks.append(lock)
        await lock["lock"].wait()

        res: AnyBuffer = lock["result"]
        return res

    def send_packet(self, packet: bytes):
        self.messages.append(self.cipher.encrypt(packet))
