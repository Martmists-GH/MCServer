import numpy as np

from mcserver.entities.entity_base import Entity
from mcserver.entities.mob_entity import MobEntity
from mcserver.entities.painting_entity import PaintingEntity
from mcserver.entities.player_entity import Player
from mcserver.server_factory import MCServer
from mcserver.utils import get_free_id


class PacketTransformer:
    bt = MCServer.buff_type

    @classmethod
    def spawn_object(cls, ent: Entity) -> bytes:
        return (cls.bt.pack_varint(ent.ent_id) +
                cls.bt.pack_uuid(ent.uuid) +
                cls.bt.pack(
                    "bdddffihhh",
                    ent.type_,
                    *ent.position,
                    *ent.rotation,
                    ent.data,
                    *ent.velocity
                ))

    @classmethod
    def spawn_exp_orb(cls, position: np.ndarray, exp_amount: int) -> bytes:
        ent_id = next(get_free_id())
        return (cls.bt.pack_varint(ent_id) +
                cls.bt.pack(
                    "dddh",
                    *position,
                    exp_amount
                ))

    @classmethod
    def spawn_global_entity(cls, position: np.ndarray) -> bytes:
        ent_id = next(get_free_id())
        return (cls.bt.pack_varint(ent_id) +
                cls.bt.pack(
                    "bddd",
                    1,
                    *position
                ))

    @classmethod
    def spawn_mob(cls, ent: MobEntity) -> bytes:
        return (cls.bt.pack_varint(ent.ent_id) +
                cls.bt.pack_uuid(ent.uuid) +
                cls.bt.pack_varint(ent.type_) +
                cls.bt.pack(
                    "dddfffhhh",
                    *ent.position,
                    *ent.rotation,
                    ent.head_pitch,
                    *ent.velocity
                ) +
                ent.pack_metadata(cls.bt))

    @classmethod
    def spawn_painting(cls, ent: PaintingEntity) -> bytes:
        return (cls.bt.pack_varint(ent.ent_id) +
                cls.bt.pack_uuid(ent.uuid) +
                cls.bt.pack_varint(ent.motive) +
                cls.bt.pack_position(*ent.position) +
                cls.bt.pack("b", ent.direction))

    @classmethod
    def spawn_player(cls, player_data: Player) -> bytes:
        return (cls.bt.pack_varint(player_data.ent_id) +
                cls.bt.pack_uuid(player_data.uuid) +
                cls.bt.pack("dddbb", *player_data.position, *player_data.rotation) + player_data.pack_metadata(cls.bt))

    @classmethod
    def animation(cls, ent_id: int, animation_state: int) -> bytes:
        return (cls.bt.pack_varint(ent_id) +
                cls.bt.pack("b", animation_state))

    @classmethod
    def statistics(cls) -> bytes:
        # TODO
        return b""

    @classmethod
    def block_break_animation(cls, ent_id: int, block_pos: np.ndarray, stage: int) -> bytes:
        return (cls.bt.pack_varint(ent_id) +
                cls.bt.pack_position(*block_pos) +
                cls.bt.pack("b", stage))

    @classmethod
    def update_block_entity(cls, pos: np.ndarray, action: int, nbt):
        return (cls.bt.pack_position(*pos) +
                cls.bt.pack("b", action) +
                cls.bt.pack_nbt(nbt))

    # TODO: Finish all this shit
