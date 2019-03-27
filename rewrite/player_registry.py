from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rewrite.client_connection import ClientConnection


class PlayerRegistry:
    players = []

    @classmethod
    def player_count(cls) -> int:
        return len(cls.players)

    @classmethod
    def add_player(cls, player: ClientConnection):
        cls.players.append(player)
