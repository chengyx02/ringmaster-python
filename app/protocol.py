import struct
from enum import Enum
from typing import Optional, Union
from utils.serialization import put_number, WireParser

class FrameType(Enum):
    UNKNOWN = 0
    KEY = 1
    NONKEY = 2

SeqNum = tuple[int, int]

class Datagram:

    # header size after serialization
    HEADER_SIZE = struct.calcsize('!IBHHQ')


    max_payload = 1500 - 28 - HEADER_SIZE


    def __init__(self, frame_id: int, frame_type: FrameType, frag_id: int, frag_cnt: int, payload: bytes):
        self.frame_id = frame_id
        self.frame_type = frame_type
        self.frag_id = frag_id
        self.frag_cnt = frag_cnt
        self.payload = payload
        self.send_ts = 0  # Placeholder for send timestamp

         # Add retransmission-related members
        self.num_rtx = 0         # Number of retransmissions
        self.last_send_ts = 0    # Last send timestamp


    @classmethod
    def set_mtu(cls, mtu: int):
        if mtu > 1500 or mtu < 512:
            raise RuntimeError("reasonable MTU is between 512 and 1500 bytes")
        
        # MTU - (IP + UDP headers) - Datagram header
        cls.max_payload = mtu - 28 - cls.HEADER_SIZE


    def parse_from_string(self, binary: bytes) -> bool:
        if len(binary) < self.HEADER_SIZE:
            return False  # datagram is too small to contain a header
        
        parse = WireParser(binary)
        self.frame_id = parse.read_uint32()
        frame_type = parse.read_uint8()
        self.frag_id = parse.read_uint16()
        self.frag_cnt = parse.read_uint16()
        self.send_ts = parse.read_uint64()
        self.frame_type = FrameType(frame_type)
        self.payload = parse.read_string()

        return True


    def serialize_to_string(self) -> bytes:
        binary = bytearray()

        binary.extend(put_number(self.frame_id, "!I"))
        binary.extend(put_number(int(self.frame_type.value), "!B"))
        binary.extend(put_number(self.frag_id, "!H"))
        binary.extend(put_number(self.frag_cnt, "!H"))
        binary.extend(put_number(self.send_ts, "!Q"))
        binary.extend(self.payload)

        return bytes(binary)


class MsgType(Enum):
    INVALID = 0 # invalid message type
    ACK = 1     # AckMsg
    CONFIG = 2  # ConfigMsg


class Msg:
    def __init__(self, msg_type: MsgType):
        self.type = msg_type


    def serialized_size(self) -> int:
        return struct.calcsize('!B')  # size of type


    def serialize_to_string(self) -> bytes:
        return put_number(self.type.value, '!B')


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
        base += put_number(self.frame_id, "!I")
        base += put_number(self.frag_id, "!H")
        base += put_number(self.send_ts, "!Q")

        return bytes(base)


class ConfigMsg(Msg):

    def __init__(self, width: int, height: int, frame_rate: int, target_bitrate: int):
        super().__init__(MsgType.CONFIG)
        self.width = width
        self.height = height
        self.frame_rate = frame_rate
        self.target_bitrate = target_bitrate


    def serialized_size(self) -> int:
        return super().serialized_size() + 3 * 2 + 4


    def serialize_to_string(self) -> bytes:
        base = super().serialize_to_string()

        base += put_number(self.width, "!H")
        base += put_number(self.height, "!H")
        base += put_number(self.frame_rate, "!H")
        base += put_number(self.target_bitrate, "!I")

        return bytes(base)
    
