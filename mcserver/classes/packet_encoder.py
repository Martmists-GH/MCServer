import io
import json
import struct

from mcserver.objects.server_core import ServerCore


class PacketEncoder:
    def __init__(self, protocol: int):
        self.protocol = protocol
        self.buffer: io.BytesIO = None

    def write(self, fmt: str, args):
        self.buffer.write(struct.pack(">"+fmt, args))

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
        def pack_twos_comp(bits, number):
            if number < 0:
                number = number + (1 << bits)
            return number

        self.write('Q', sum((
            pack_twos_comp(26, x) << 38,
            pack_twos_comp(12, y) << 26,
            pack_twos_comp(26, z))))

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
