
import struct
from typing import TypeVar

T = TypeVar('T', int, int)

# Convert values from network to host byte order
"""
inline uint8_t ntoh(uint8_t net) { return net; }
"""
def ntoh8(net: int) -> int:
    return net

"""
inline uint16_t ntoh(uint16_t net) { return be16toh(net); }
"""
def ntoh16(net: int) -> int:
    return struct.unpack('!H', struct.pack('H', net))[0]

"""
inline uint32_t ntoh(uint32_t net) { return be32toh(net); }
"""
def ntoh32(net: int) -> int:
    return struct.unpack('!I', struct.pack('I', net))[0]

"""
inline uint64_t ntoh(uint64_t net) { return be64toh(net); }
"""
def ntoh64(net: int) -> int:
    return struct.unpack('!Q', struct.pack('Q', net))[0]

# Convert values from host to network byte order
"""
inline uint8_t hton(uint8_t host) { return host; }
"""
def hton8(host: int) -> int:
    return host

"""
inline uint16_t hton(uint16_t host) { return htobe16(host); }
"""
def hton16(host: int) -> int:
    return struct.unpack('H', struct.pack('!H', host))[0]

"""
inline uint32_t hton(uint32_t host) { return htobe32(host); }
"""
def hton32(host: int) -> int:
    return struct.unpack('I', struct.pack('!I', host))[0]

"""
inline uint64_t hton(uint64_t host) { return htobe64(host); }
"""
def hton64(host: int) -> int:
    return struct.unpack('Q', struct.pack('!Q', host))[0]

# Serialize a number in host byte order to binary data on wire
"""
template<typename T>
std::string put_number(const T host)
{
  const T net = hton(host);
  return {reinterpret_cast<const char *>(&net), sizeof(net)};
}
"""
def put_number(host: int, fmt: str) -> bytes:
    net = struct.pack(fmt, host)
    return net

# Deserialize binary data received on wire to a number in host byte order
def get_number(net: bytes, fmt: str) -> int:
    if len(net) < struct.calcsize(fmt):
        raise ValueError("get_number(): read past end")
    return struct.unpack(fmt, net)[0]

# Similar to get_number except with *no* bounds check
"""
uint8_t get_uint8(const char * net);
"""
def get_uint8(data: bytes) -> int:
    return data[0]

"""
uint16_t get_uint16(const char * net);
"""
def get_uint16(data: bytes) -> int:
    return struct.unpack('!H', data[:2])[0]

"""
uint32_t get_uint32(const char * net);
"""
def get_uint32(data: bytes) -> int:
    return struct.unpack('!I', data[:4])[0]

"""
uint64_t get_uint64(const char * net);
"""
def get_uint64(data: bytes) -> int:
    return struct.unpack('!Q', data[:8])[0]

# Get the value of a bit range in the number
"""
// bit numbering is *MSB 0*, e.g., 0x01 is represented as:
// binary: 0 0 0 0 0 0 0 1
// index:  0 1 2 3 4 5 6 7
"""
def get_bits(number: int, bit_offset: int, bit_len: int) -> int:
    total_bits = number.bit_length()
    if bit_offset + bit_len > total_bits:
        raise ValueError("get_bits(): read past end")
    ret = number >> (total_bits - bit_offset - bit_len)
    ret &= (1 << bit_len) - 1
    return ret

class WireParser:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0


    def read_uint8(self) -> int:
        return self.read('!B')


    def read_uint16(self) -> int:
        return self.read('!H')


    def read_uint32(self) -> int:
        return self.read('!I')


    def read_uint64(self) -> int:
        return self.read('!Q')


    def read_string(self, length: int=None) -> bytes:
        if length is None:
            length = len(self.data) - self.offset
            
        if self.offset + length > len(self.data):
            raise ValueError("WireParser::read_string(): attempted to read past end")
            
        # Get raw bytes without decoding
        value = self.data[self.offset:self.offset + length]
        self.offset += length
        return value


    def skip(self, length: int):
        if self.offset + length > len(self.data):
            raise ValueError("WireParser::skip(): skip past end")
        self.offset += length


    def read(self, fmt: str) -> int:
        size = struct.calcsize(fmt)
        if self.offset + size > len(self.data):
            raise ValueError("WireParser::read(): read past end")
        result = struct.unpack_from(fmt, self.data, self.offset)[0]
        self.offset += size
        return result