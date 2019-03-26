from typing import Set

from quarry.net.protocol import Protocol

from mcserver.entities.player_entity import Player


class PlayerHandler:
    players: Set[Player] = set()

    @classmethod
    def get_player(cls, prot: Protocol) -> Player:
        target = [player for player in cls.players if prot.uuid == player.uuid]
        if not target:
            print("Creating new player")
            player = Player(prot)
            cls.players.add(player)
        else:
            player = target[0]
            player.load()
        return player

    @classmethod
    def remove_player(cls, prot: Protocol):
        target = [player for player in cls.players if prot.uuid == player.uuid][0]
        cls.players.remove(target)
        target.save()
