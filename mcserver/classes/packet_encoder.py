import io
import json
import struct
from uuid import UUID

from mcserver.objects.server_core import ServerCore
from mcserver.game.abc.entity_base import Look


class PacketEncoder:
    def __init__(self, protocol: int):
        self.protocol = protocol
        self.buffer: io.BytesIO = None

    def write(self, fmt: str, *args):
        self.buffer.write(struct.pack(">" + fmt, *args))

    def write_varint(self, number: int):
        if number < 0:
            number += 1 << 32

        for i in range(10):
            b = number & 0x7F
            number >>= 7
            self.write("B", b | (0x80 if number > 0 else 0))
            if number == 0:
                break

    def write_position(self, x, y, z):
        self.write("Q", ((x & 0x3FFFFFF) << 38) | ((y & 0xFFF) << 26) | (z & 0x3FFFFFF))
        # def pack_twos_comp(bits, number):
        #     if number < 0:
        #         number = number + (1 << bits)
        #     return number
        #
        # self.write('Q', sum((
        #     pack_twos_comp(26, x) << 38,
        #     pack_twos_comp(12, y) << 26,
        #     pack_twos_comp(26, z))))

    def write_bytes(self, data: bytes):
        self.write_varint(len(data))
        self.buffer.write(data)

    def write_string(self, text: str, encoding="utf-8"):
        self.write_bytes(text.encode(encoding))

    def write_json(self, data: dict):
        self.write_string(json.dumps(data))

    def encode(self, packet_id: str, args) -> bytes:
        self.buffer = io.BytesIO()

        if packet_id == "status":
            self.encode_status(*args)
        elif packet_id == "pong":
            self.encode_pong(*args)
        elif packet_id == "encryption_start":
            self.encode_encryption_start(*args)
        elif packet_id == "login_success":
            self.encode_login_success(*args)
        elif packet_id == "join_game":
            self.encode_join_game(*args)
        elif packet_id == "spawn_position":
            self.encode_spawn_position(*args)
        elif packet_id == "player_abilities":
            self.encode_player_abilities(*args)
        elif packet_id == "player_pos_and_look":
            self.encode_player_pos_and_look(*args)
        else:
            raise

        self.buffer.seek(0)
        data = self.buffer.read()

        self.buffer = io.BytesIO()
        self.write_varint(len(data))
        self.buffer.seek(0)

        return self.buffer.read() + data

    def encode_status(self, data: dict):
        self.write_varint(0)  # `status` code
        self.write_json(data)

    def encode_pong(self, arg: int):
        self.write_varint(1)  # `pong` code
        self.write("q", arg)

    def encode_encryption_start(self, server_id: str, verify_token: bytes):
        self.write_varint(1)  # `encryption_start` code
        self.write_string(server_id)
        self.write_bytes(ServerCore.pubkey)
        self.write_bytes(verify_token)

    def encode_login_success(self, uuid: UUID, username: str):
        self.write_varint(2)
        self.write_string(str(uuid))
        self.write_string(username)

    def encode_join_game(self, eid: int, gamemode: int, dimension: int, difficulty: int, max_players: int,
                         level_type: str, debug_info: bool):
        self.write_varint(25)
        self.write("iBiBB", eid, gamemode, dimension, difficulty, max_players)
        self.write_string(level_type)
        self.write("?", debug_info)

    def encode_spawn_position(self, location: list):
        self.write_varint(73)
        # Note this is the server's home spawn chunks and not the position the player will spawn at
        self.write_position(12, 12, 12)

    def encode_player_abilities(self, abilities: dict, flying_speed: float, fov_modifier: float):
        self.write_varint(46)
        # Takes the abilities dict and turns it into a bitfield based on the packet specification
        self.write("B", sum(1 << i if x else 0 for i, x in enumerate(abilities.values())))
        self.write("ff", flying_speed, fov_modifier)

    def encode_player_pos_and_look(self, look: Look, tp_id: int):
        self.write_varint(50)
        self.write("ddd", *look.xyz)
        self.write("ff", *look.pitchyaw)
        self.write("B", look.relative)  # Not properly implemented yet
        self.write_varint(tp_id)
