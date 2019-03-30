# Future patches
from __future__ import annotations

# Stdlib
from typing import TYPE_CHECKING
from uuid import UUID

# MCServer
from mcserver.classes.player import Player

if TYPE_CHECKING:
    from typing import List, Union
    from mcserver.classes.client_connection import ClientConnection


class PlayerRegistry:
    players: List[Player] = []

    @classmethod
    def player_count(cls) -> int:
        return len(cls.players)

    @classmethod
    def get_player(cls, uuid: UUID) -> Player:
        return [p for p in cls.players if p.uuid == uuid][0]

    @classmethod
    def add_player(cls, player: ClientConnection) -> Player:
        player_obj = Player(player)
        cls.players.append(player_obj)
        return player_obj

    @classmethod
    def remove_player(cls, player: Union[Player, UUID]):
        if isinstance(player, UUID):
            player = cls.get_player(player)

        cls.players.remove(player)
