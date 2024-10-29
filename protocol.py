# This Python code mirrors the functionality of the provided C++ code, 
# including serialization and deserialization of datagrams and messages. 
# The Datagram, Msg, AckMsg, and ConfigMsg classes are implemented with methods 
# for parsing from and serializing to binary strings.

import struct
from enum import Enum
from typing import Optional, Union

class FrameType(Enum):
    KEY = 0
    DELTA = 1

class Datagram:
    HEADER_SIZE = 16  # Example header size, adjust as needed
    max_payload = 1500 - 28 - HEADER_SIZE

    def __init__(self, frame_id: int, frame_type: FrameType, frag_id: int, frag_cnt: int, payload: bytes):
        self.frame_id = frame_id
        self.frame_type = frame_type
        self.frag_id = frag_id
        self.frag_cnt = frag_cnt
        self.payload = payload
        self.send_ts = 0  # Placeholder for send timestamp

    @classmethod
    def set_mtu(cls, mtu: int):
        if mtu > 1500 or mtu < 512:
            raise RuntimeError("reasonable MTU is between 512 and 1500 bytes")
        cls.max_payload = mtu - 28 - cls.HEADER_SIZE

    def parse_from_string(self, binary: bytes) -> bool:
        if len(binary) < self.HEADER_SIZE:
            return False  # datagram is too small to contain a header

        self.frame_id, frame_type, self.frag_id, self.frag_cnt, self.send_ts = struct.unpack('!IBHHQ', binary[:self.HEADER_SIZE])
        self.frame_type = FrameType(frame_type)
        self.payload = binary[self.HEADER_SIZE:]
        return True

    def serialize_to_string(self) -> bytes:
        header = struct.pack('!IBHHQ', self.frame_id, self.frame_type.value, self.frag_id, self.frag_cnt, self.send_ts)
        return header + self.payload

class MsgType(Enum):
    ACK = 0
    CONFIG = 1

class Msg:
    def __init__(self, msg_type: MsgType):
        self.type = msg_type

    def serialized_size(self) -> int:
        return 1  # size of type

    def serialize_to_string(self) -> bytes:
        return struct.pack('!B', self.type.value)

    @staticmethod
    def parse_from_string(binary: bytes) -> Optional[Union['AckMsg', 'ConfigMsg']]:
        if len(binary) < 1:
            return None

        msg_type = MsgType(struct.unpack('!B', binary[0:1])[0])
        if msg_type == MsgType.ACK:
            frame_id, frag_id, send_ts = struct.unpack('!IHQ', binary[1:15])
            return AckMsg(frame_id, frag_id, send_ts)
        elif msg_type == MsgType.CONFIG:
            width, height, frame_rate, target_bitrate = struct.unpack('!HHHI', binary[1:11])
            return ConfigMsg(width, height, frame_rate, target_bitrate)
        else:
            return None

class AckMsg(Msg):
    def __init__(self, frame_id: int, frag_id: int, send_ts: int):
        super().__init__(MsgType.ACK)
        self.frame_id = frame_id
        self.frag_id = frag_id
        self.send_ts = send_ts

    def serialized_size(self) -> int:
        return super().serialized_size() + 4 + 2 + 8

    def serialize_to_string(self) -> bytes:
        base = super().serialize_to_string()
        return base + struct.pack('!IHQ', self.frame_id, self.frag_id, self.send_ts)

class ConfigMsg(Msg):
    def __init__(self, width: int, height: int, frame_rate: int, target_bitrate: int):
        super().__init__(MsgType.CONFIG)
        self.width = width
        self.height = height
        self.frame_rate = frame_rate
        self.target_bitrate = target_bitrate

    def serialized_size(self) -> int:
        return super().serialized_size() + 2 + 2 + 2 + 4

    def serialize_to_string(self) -> bytes:
        base = super().serialize_to_string()
        return base + struct.pack('!HHHI', self.width, self.height, self.frame_rate, self.target_bitrate)