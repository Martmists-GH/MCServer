import io
import struct

from mcserver.events.event_base import Event


class PacketDecoder:
    def __init__(self, protocol: int, status: int):
        self.protocol = protocol
        self.status = status
        self.buffer: io.BytesIO = None

    def read(self, fmt: str):
        fmt = ">" + fmt
        size = struct.calcsize(fmt)
        vals = struct.unpack(fmt, self.buffer.read(size))
        return vals if len(vals) != 1 else vals[0]

    def read_varint(self) -> int:
        number = 0
        for i in range(10):
            b = self.read("B")
            number |= (b & 0x7F) << 7*i
            if not b & 0x80:
                break

        if number & (1 << 31):
            number -= 1 << 32

        return number

    def read_string(self) -> str:
        size = self.read_varint()
        return self.buffer.read(size).decode()

    def decode(self, packet: bytes):
        print(packet)
        self.buffer = io.BytesIO(packet)

        packet_length = self.read("b")
        pos = self.buffer.tell()
        assert len(self.buffer.read()) >= packet_length
        self.buffer.seek(pos)

        packet_id = self.read("b")
        if packet_id == 0:
            if self.status == 0:
                data = self.decode_handshake()
            elif self.status == 1:
                data = self.decode_status()
        else:
            raise Exception(f"Unhandled packet ID {packet_id} with data {self.buffer.read()}")
        return self.buffer.read(), data  # read the buffer to return remaining bytes

    def decode_handshake(self):
        self.protocol = self.read_varint()
        hostname = self.read_string()
        port = self.read("H")
        self.status = self.read_varint()
        return Event("handshake", [hostname, port])

    def decode_status(self):
        return Event("status", None)
