# Future patches
from __future__ import annotations

# Stdlib
from typing import TYPE_CHECKING

# MCServer
from mcserver.game.abc.entity_base import EntityBase

if TYPE_CHECKING:
    from uuid import UUID


class EntityPlayer(EntityBase):
    def __init__(self):
        super().__init__()
        self.uuid: UUID = None
        self.name = ""
        self.display_name = ""
        self.gamemode = 1
        self.flying = False
        self.walk_speed = 1.0
        self.fly_speed = 1.0

    @property
    def abilities(self):
        flags = 0
        if self.flying:
            flags |= 0x02
        if self.gamemode in (1, 3):
            flags |= 0x04
        if self.gamemode in (1, 3):
            flags |= 0x08
        if self.gamemode == 1:
            flags |= 0x01
        return flags
