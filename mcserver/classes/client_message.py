from __future__ import annotations

from typing import TYPE_CHECKING

from quarry.data import packets
from quarry.types.buffer import buff_types

from mcserver.utils.logger import debug
from mcserver.utils.misc import copy_buffer

if TYPE_CHECKING:
    from typing import Type
    from mcserver.utils.misc import AnyBuffer
    from mcserver.classes.client_connection import ClientConnection


class ClientMessage:
    """
    protocol version:
    4 -> 1.7.5
    47 -> 1.8.8
    107 -> 1.9
    108 -> 1.9.1
    109 -> 1.9.2
    110 -> 1.9.4
    210 -> 1.10
    315 -> 1.11
    316 -> 1.11.2
    335 -> 1.12
    338 -> 1.12.1
    340 -> 1.12.2
    393 -> 1.13
    401 -> 1.13.1
    404 -> 1.13.2
    """
    protocol_version = packets.default_protocol_version
    recv_direction = "upstream"
    send_direction = "downstream"
    compression_threshold = -1

    def __init__(self, connection: ClientConnection, data: bytes):
        self.conn = connection
        decrypted = self._new_buffer(data)
        self._buffer: AnyBuffer = decrypted.unpack_packet(self.buffer_type, self.compression_threshold)
        self.old_len = len(decrypted.read())
        self.name = self.get_packet_name(self._buffer.unpack_varint())

    def __repr__(self):
        return f"ClientMessage(event={self.name}, data={self.buffer.read()})"

    def set_protocol_version(self, version: int):
        if self.protocol_version == packets.default_protocol_version:
            ClientMessage.protocol_version = version

    @property
    def buffer(self) -> AnyBuffer:
        return copy_buffer(self._buffer)

    def get_packet_name(self, ident: int) -> str:
        key = (self.protocol_version, self.conn.protocol_state, self.recv_direction, ident)
        return packets.packet_names[key]

    def get_packet_ident(self, name: str) -> int:
        key = (self.protocol_version, self.conn.protocol_state, self.send_direction, name)
        return packets.packet_idents[key]

    @property
    def buffer_type(self) -> Type[AnyBuffer]:
        for ver, cls in reversed(buff_types):
            if self.protocol_version >= ver:
                return cls

    def _new_buffer(self, data: bytes = None) -> AnyBuffer:
        return self.buffer_type(data)

    def close_connection(self, reason: str = None):
        debug(f"Closing connection with reason: {reason}")
        if self.conn.do_loop and reason is not None:
            # Kick the player if possible.
            if self.conn.protocol_state == "play":
                self.send_packet("disconnect",
                                 self.buffer_type.pack_chat(reason))
            elif self.conn.protocol_state == "login":
                self.send_packet(
                    "login_disconnect",
                    self.buffer_type.pack_chat(reason))

    def build_packet(self, name: str, data: bytes) -> bytes:
        combined = self.buffer_type.pack_varint(self.get_packet_ident(name)) + data
        return self.buffer_type.pack_packet(combined, self.compression_threshold)

    def send_packet(self, name: str, data: bytes):
        self.conn.send_packet(
            self.build_packet(name, data)
        )
