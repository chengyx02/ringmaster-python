"""
Plan
Import necessary Python modules.
Define functions to convert values between network and host byte order.
Define functions to serialize and deserialize numbers.
Define functions to get the value of a bit range in a number.
Define the WireParser class with methods:
__init__: Initialize the parser with a string view.
read_uint8, read_uint16, read_uint32, read_uint64: Read unsigned integers from the string view.
read_string: Read a string of a specified length from the string view.
skip: Skip a specified number of bytes in the string view.
read: Template method to read a value of a specified type from the string view.
Code

This Python code mirrors the functionality of the provided C++ code, 
including serialization and deserialization of numbers, bit manipulation, 
and parsing binary data. The WireParser class provides methods for reading 
unsigned integers and strings from a byte sequence, as well as skipping bytes. 
The conversion functions handle network-to-host and host-to-network byte order conversions.
"""

import struct
from typing import TypeVar, Type

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
# def put_number(host: int) -> bytes:
#     if isinstance(host, int):
#         if host <= 0xFF:
#             return struct.pack('!B', host)
#         elif host <= 0xFFFF:
#             return struct.pack('!H', host)
#         elif host <= 0xFFFFFFFF:
#             return struct.pack('!I', host)
#         elif host <= 0xFFFFFFFFFFFFFFFF:
#             return struct.pack('!Q', host)
#     raise ValueError("Unsupported number size")


# Deserialize binary data received on wire to a number in host byte order
"""
template<typename T>
T get_number(const std::string_view net)
{
  if (sizeof(T) > net.size()) {
    throw std::out_of_range("get_number(): read past end");
  }

  T ret;
  memcpy(&ret, net.data(), sizeof(T));

  return ntoh(ret);
}
"""
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

template<typename T>
T get_bits(const T number, const size_t bit_offset, const size_t bit_len)
{
  const size_t total_bits = sizeof(T) * 8;

   if (bit_offset + bit_len > total_bits) {
    throw std::out_of_range("get_bits(): read past end");
  }

  T ret = number >> (total_bits - bit_offset - bit_len);
  ret &= (1 << bit_len) - 1;

  return ret;
}
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

    """
    uint8_t get_uint8(const char * data)
    {
        return *reinterpret_cast<const uint8_t *>(data);
    }
    """
    def read_uint8(self) -> int:
        return self.read('!B')

    """
    uint16_t get_uint16(const char * data)
    {
        return be16toh(*reinterpret_cast<const uint16_t *>(data));
    }
    """
    def read_uint16(self) -> int:
        return self.read('!H')

    """
    uint32_t get_uint32(const char * data)
    {
        return be32toh(*reinterpret_cast<const uint32_t *>(data));
    }
    """
    def read_uint32(self) -> int:
        return self.read('!I')

    """
    uint64_t get_uint64(const char * data)
    {
        return be64toh(*reinterpret_cast<const uint64_t *>(data));
    }
    """
    def read_uint64(self) -> int:
        return self.read('!Q')

    """
    string WireParser::read_string(const size_t len)
    {
        if (len > str_.size()) {
            throw out_of_range("WireParser::read_string(): attempted to read past end");
        }

        string ret { str_.data(), len };

        // move the start of string view forward
        str_.remove_prefix(len);

        return ret;
    }
    std::string read_string() { return read_string(str_.size()); }
    """
    def read_string(self, length: int=None) -> str:
        if length is None:
            length = len(self.data) - self.offset
        if self.offset + length > len(self.data):
            raise ValueError("WireParser::read_string(): attempted to read past end")
        value = self.data[self.offset:self.offset + length].decode('utf-8')
        self.offset += length
        return value

    """
    void WireParser::skip(const size_t len)
    {
        if (len > str_.size()) {
            throw out_of_range("WireParser::skip(): attempted to skip past end");
        }

        str_.remove_prefix(len);
    }
    """
    def skip(self, length: int):
        if self.offset + length > len(self.data):
            raise ValueError("WireParser::skip(): skip past end")
        self.offset += length

    """
    template<typename T>
    T read()
    {
        if (sizeof(T) > str_.size()) {
        throw std::out_of_range("WireParser::read(): read past end");
        }

        T ret;
        memcpy(&ret, str_.data(), sizeof(T));

        // move the start of string view forward
        str_.remove_prefix(sizeof(T));

        return ntoh(ret);
    }
    """
    def read(self, fmt: str) -> int:
        size = struct.calcsize(fmt)
        if self.offset + size > len(self.data):
            raise ValueError("WireParser::read(): read past end")
        result = struct.unpack_from(fmt, self.data, self.offset)[0]
        self.offset += size
        return result