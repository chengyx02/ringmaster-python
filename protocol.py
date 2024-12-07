# This Python code mirrors the functionality of the provided C++ code, 
# including serialization and deserialization of datagrams and messages. 
# The Datagram, Msg, AckMsg, and ConfigMsg classes are implemented with methods 
# for parsing from and serializing to binary strings.

import struct
from enum import Enum
from typing import Optional, Union
from utils.serialization import put_number, WireParser

# try:
#     import debugpy; debugpy.connect(5678)
# except:
#     pass

"""
enum class FrameType : uint8_t {
  UNKNOWN = 0, // unknown
  KEY = 1,     // key frame
  NONKEY = 2,  // non-key frame
};

// uses (frame_id, frag_id) as sequence number
using SeqNum = std::pair<uint32_t, uint16_t>;
"""
class FrameType(Enum):
    UNKNOWN = 0
    KEY = 1
    NONKEY = 2

SeqNum = tuple[int, int]

class Datagram:
    """
    // header size after serialization
    static constexpr size_t HEADER_SIZE = sizeof(uint32_t) +
        sizeof(FrameType) + 2 * sizeof(uint16_t) + sizeof(uint64_t);
    """
    HEADER_SIZE = struct.calcsize('!IBHHQ')

    """
    size_t Datagram::max_payload = 1500 - 28 - Datagram::HEADER_SIZE;
    """
    max_payload = 1500 - 28 - HEADER_SIZE

    """
    Datagram::Datagram(const uint32_t _frame_id,
                   const FrameType _frame_type,
                   const uint16_t _frag_id,
                   const uint16_t _frag_cnt,
                   const string_view _payload)
    : frame_id(_frame_id), frame_type(_frame_type),
        frag_id(_frag_id), frag_cnt(_frag_cnt), payload(_payload)
    {}
    """
    def __init__(self, frame_id: int, frame_type: FrameType, frag_id: int, frag_cnt: int, payload: bytes):
        self.frame_id = frame_id
        self.frame_type = frame_type
        self.frag_id = frag_id
        self.frag_cnt = frag_cnt
        self.payload = payload
        self.send_ts = 0  # Placeholder for send timestamp

    """
    void Datagram::set_mtu(const size_t mtu)
    {
        if (mtu > 1500 or mtu < 512) {
            throw runtime_error("reasonable MTU is between 512 and 1500 bytes");
        }

        // MTU - (IP + UDP headers) - Datagram header
        max_payload = mtu - 28 - Datagram::HEADER_SIZE;
    }
    """
    @classmethod
    def set_mtu(cls, mtu: int):
        if mtu > 1500 or mtu < 512:
            raise RuntimeError("reasonable MTU is between 512 and 1500 bytes")
        cls.max_payload = mtu - 28 - cls.HEADER_SIZE

    """
    bool Datagram::parse_from_string(const string & binary)
    {
        if (binary.size() < HEADER_SIZE) {
            return false; // datagram is too small to contain a header
        }

        WireParser parser(binary);
        frame_id = parser.read_uint32();
        frame_type = static_cast<FrameType>(parser.read_uint8());
        frag_id = parser.read_uint16();
        frag_cnt = parser.read_uint16();
        send_ts = parser.read_uint64();
        payload = parser.read_string();

        return true;
    }
    """
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

    """
    string Datagram::serialize_to_string() const
    {
        string binary;
        binary.reserve(HEADER_SIZE + payload.size());

        binary += put_number(frame_id);
        binary += put_number(static_cast<uint8_t>(frame_type));
        binary += put_number(frag_id);
        binary += put_number(frag_cnt);
        binary += put_number(send_ts);
        binary += payload;

        return binary;
    }
    """
    def serialize_to_string(self) -> bytes:
        binary = bytearray()
        binary.extend(put_number(self.frame_id, "!I"))
        binary.extend(put_number(int(self.frame_type.value), "!B"))
        binary.extend(put_number(self.frag_id, "!H"))
        binary.extend(put_number(self.frag_cnt, "!H"))
        binary.extend(put_number(self.send_ts, "!Q"))
        binary.extend(self.payload)
        return bytes(binary)

"""
enum class Type : uint8_t {
    INVALID = 0, // invalid message type
    ACK = 1,     // AckMsg
    CONFIG = 2   // ConfigMsg
};
"""
class MsgType(Enum):
    INVALID = 0 # invalid message type
    ACK = 1     # AckMsg
    CONFIG = 2  # ConfigMsg

"""
struct Msg
{
  enum class Type : uint8_t {
    INVALID = 0, // invalid message type
    ACK = 1,     // AckMsg
    CONFIG = 2   // ConfigMsg
  };

  Type type {Type::INVALID}; // message type

  Msg() {}
  Msg(const Type _type) : type(_type) {}
  virtual ~Msg() {}

  // factory method to make a (derived class of) Msg
  static std::shared_ptr<Msg> parse_from_string(const std::string & binary);

  // virtual functions
  virtual size_t serialized_size() const;
  virtual std::string serialize_to_string() const;
};
"""
class Msg:
    def __init__(self, msg_type: MsgType):
        self.type = msg_type

    """
    size_t Msg::serialized_size() const
    {
        return sizeof(type);
    }
    """
    def serialized_size(self) -> int:
        return struct.calcsize('!B')  # size of type

    """
    string Msg::serialize_to_string() const
    {
        return put_number(static_cast<uint8_t>(type));
    }
    """
    def serialize_to_string(self) -> bytes:
        # return struct.pack('!B', self.type.value)
        return put_number(self.type.value, '!B')

    """
    shared_ptr<Msg> Msg::parse_from_string(const string & binary)
    {
        if (binary.size() < sizeof(type)) {
            return nullptr;
        }

        WireParser parser(binary);
        auto type = static_cast<Type>(parser.read_uint8());

        if (type == Type::ACK) {
            auto ret = make_shared<AckMsg>();
            ret->frame_id = parser.read_uint32();
            ret->frag_id = parser.read_uint16();
            ret->send_ts = parser.read_uint64();
            return ret;
        }
        else if (type == Type::CONFIG) {
            auto ret = make_shared<ConfigMsg>();
            ret->width = parser.read_uint16();
            ret->height = parser.read_uint16();
            ret->frame_rate = parser.read_uint16();
            ret->target_bitrate = parser.read_uint32();
            return ret;
        }
        else {
            return nullptr;
        }
    }
    """
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

"""
struct AckMsg : Msg
{
  // construct an AckMsg
  AckMsg() : Msg(Type::ACK) {}
  AckMsg(const Datagram & datagram);

  uint32_t frame_id {}; // frame ID
  uint16_t frag_id {};  // fragment ID in this frame
  uint64_t send_ts {};  // timestamp (us) on sender when the datagram was sent

  size_t serialized_size() const override;
  std::string serialize_to_string() const override;
};
"""
class AckMsg(Msg):
    """
    AckMsg::AckMsg(const Datagram & datagram)
      : Msg(Type::ACK), frame_id(datagram.frame_id), frag_id(datagram.frag_id),
        send_ts(datagram.send_ts)
    {}
    """
    def __init__(self, frame_id: int, frag_id: int, send_ts: int):
        super().__init__(MsgType.ACK)
        self.frame_id = frame_id
        self.frag_id = frag_id
        self.send_ts = send_ts

    """
    size_t AckMsg::serialized_size() const
    {
        return Msg::serialized_size() + sizeof(uint16_t) + sizeof(uint32_t)
                + sizeof(uint64_t);
    }
    """
    def serialized_size(self) -> int:
        return super().serialized_size() + 4 + 2 + 8

    """
    string AckMsg::serialize_to_string() const
    {
        string binary;
        binary.reserve(serialized_size());

        binary += Msg::serialize_to_string();
        binary += put_number(frame_id);
        binary += put_number(frag_id);
        binary += put_number(send_ts);

        return binary;
    }
    """
    def serialize_to_string(self) -> bytes:
        base = super().serialize_to_string()
        base += put_number(self.frame_id, "!I")
        base += put_number(self.frag_id, "!H")
        base += put_number(self.send_ts, "!Q")

        return bytes(base)

"""
struct ConfigMsg : Msg
{
  // construct a ConfigMsg
  ConfigMsg() : Msg(Type::CONFIG) {}
  ConfigMsg(const uint16_t _width, const uint16_t _height,
            const uint16_t _frame_rate, const uint32_t _target_bitrate);

  uint16_t width {};          // display width
  uint16_t height {};         // display height
  uint16_t frame_rate {};     // FPS
  uint32_t target_bitrate {}; // target bitrate

  size_t serialized_size() const override;
  std::string serialize_to_string() const override;
};
"""
class ConfigMsg(Msg):
    """
    ConfigMsg::ConfigMsg(const uint16_t _width, const uint16_t _height,
                     const uint16_t _frame_rate, const uint32_t _target_bitrate)
    : Msg(Type::CONFIG), width(_width), height(_height),
        frame_rate(_frame_rate), target_bitrate(_target_bitrate)
    {}
    """
    def __init__(self, width: int, height: int, frame_rate: int, target_bitrate: int):
        super().__init__(MsgType.CONFIG)
        self.width = width
        self.height = height
        self.frame_rate = frame_rate
        self.target_bitrate = target_bitrate

    """
    size_t ConfigMsg::serialized_size() const
    {
        return Msg::serialized_size() + 3 * sizeof(uint16_t) + sizeof(uint32_t);
    }
    """
    def serialized_size(self) -> int:
        return super().serialized_size() + 3 * 2 + 4

    """
    string ConfigMsg::serialize_to_string() const
    {
        string binary;
        binary.reserve(serialized_size());

        binary += Msg::serialize_to_string();
        binary += put_number(width);
        binary += put_number(height);
        binary += put_number(frame_rate);
        binary += put_number(target_bitrate);

        return binary;
    }
    """
    def serialize_to_string(self) -> bytes:
        base = super().serialize_to_string()

        base += put_number(self.width, "!H")
        base += put_number(self.height, "!H")
        base += put_number(self.frame_rate, "!H")
        base += put_number(self.target_bitrate, "!I")

        return bytes(base)
    
def example_usage():
    # Create a Datagram instance
    datagram = Datagram(
        frame_id=12345,
        frame_type=FrameType.KEY,
        frag_id=1,
        frag_cnt=1,
        payload=b"Hello, World!"
    )

    # Serialize the Datagram to a binary string
    serialized_datagram = datagram.serialize_to_string()
    print("Serialized Datagram:", serialized_datagram)

    # Parse the binary string back to a Datagram instance
    parsed_datagram = Datagram(0, FrameType.UNKNOWN, 0, 0, b"")
    if parsed_datagram.parse_from_string(serialized_datagram):
        print("Parsed Datagram:")
        print("  frame_id:", parsed_datagram.frame_id)
        print("  frame_type:", parsed_datagram.frame_type)
        print("  frag_id:", parsed_datagram.frag_id)
        print("  frag_cnt:", parsed_datagram.frag_cnt)
        print("  send_ts:", parsed_datagram.send_ts)
        print("  payload:", parsed_datagram.payload)
    else:
        print("Failed to parse Datagram")

    # Create an AckMsg instance from the parsed Datagram
    ack_msg = AckMsg(
        frame_id=parsed_datagram.frame_id,
        frag_id=parsed_datagram.frag_id,
        send_ts=parsed_datagram.send_ts
    )

    # Serialize the AckMsg to a binary string
    serialized_ack_msg = ack_msg.serialize_to_string()
    print("Serialized AckMsg:", serialized_ack_msg)

    # Parse the binary string back to an AckMsg instance
    parsed_msg = Msg.parse_from_string(serialized_ack_msg)
    if isinstance(parsed_msg, AckMsg):
        print("Parsed AckMsg:")
        print("  frame_id:", parsed_msg.frame_id)
        print("  frag_id:", parsed_msg.frag_id)
        print("  send_ts:", parsed_msg.send_ts)
    else:
        print("Failed to parse AckMsg")

    # Create a ConfigMsg instance
    config_msg = ConfigMsg(
        width=1920,
        height=1080,
        frame_rate=30,
        target_bitrate=5000000
    )

    # Serialize the ConfigMsg to a binary string
    serialized_config_msg = config_msg.serialize_to_string()
    print("Serialized ConfigMsg:", serialized_config_msg)

    # Parse the binary string back to a ConfigMsg instance
    parsed_msg = Msg.parse_from_string(serialized_config_msg)
    if isinstance(parsed_msg, ConfigMsg):
        print("Parsed ConfigMsg:")
        print("  width:", parsed_msg.width)
        print("  height:", parsed_msg.height)
        print("  frame_rate:", parsed_msg.frame_rate)
        print("  target_bitrate:", parsed_msg.target_bitrate)
    else:
        print("Failed to parse ConfigMsg")

if __name__ == "__main__":
    example_usage()