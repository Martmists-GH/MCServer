from __future__ import annotations

from typing import TYPE_CHECKING

from mcserver.game.entities.player import EntityPlayer

if TYPE_CHECKING:
    from typing import Type
    from mcserver.classes.client_connection import ClientConnection
    from mcserver.utils.misc import AnyBuffer


class Player:
    def __init__(self, conn: ClientConnection):
        self.conn = conn
        self.entity = EntityPlayer()
        self.uuid = self.entity.uuid = conn.uuid
        self.name = self.entity.name = conn.display_name
        self.entity.display_name = conn.display_name

        self.ping = 0
        self.properties = {}

    async def load(self):
        # TODO:
        # Load from file
        # Load from API
        pass

    def pack_properties(self, buffer_type: Type[AnyBuffer]) -> bytes:
        return b""

    @property
    def display_name(self):
        return self.entity.display_name

    @property
    def gamemode(self):
        return self.entity.gamemode
