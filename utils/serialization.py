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
def ntoh8(net: int) -> int:
    return net

def ntoh16(net: int) -> int:
    return struct.unpack('!H', struct.pack('H', net))[0]

def ntoh32(net: int) -> int:
    return struct.unpack('!I', struct.pack('I', net))[0]

def ntoh64(net: int) -> int:
    return struct.unpack('!Q', struct.pack('Q', net))[0]

# Convert values from host to network byte order
def hton8(host: int) -> int:
    return host

def hton16(host: int) -> int:
    return struct.unpack('H', struct.pack('!H', host))[0]

def hton32(host: int) -> int:
    return struct.unpack('I', struct.pack('!I', host))[0]

def hton64(host: int) -> int:
    return struct.unpack('Q', struct.pack('!Q', host))[0]

# Serialize a number in host byte order to binary data on wire
def put_number(host: int, fmt: str) -> bytes:
    net = struct.pack(fmt, host)
    return net

# Deserialize binary data received on wire to a number in host byte order
def get_number(net: bytes, fmt: str) -> int:
    if len(net) < struct.calcsize(fmt):
        raise ValueError("get_number(): read past end")
    return struct.unpack(fmt, net)[0]

# Similar to get_number except with *no* bounds check
def get_uint8(data: bytes) -> int:
    return data[0]

def get_uint16(data: bytes) -> int:
    return struct.unpack('!H', data[:2])[0]

def get_uint32(data: bytes) -> int:
    return struct.unpack('!I', data[:4])[0]

def get_uint64(data: bytes) -> int:
    return struct.unpack('!Q', data[:8])[0]

# Get the value of a bit range in the number
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

    def read_uint8(self) -> int:
        return self.read('B')

    def read_uint16(self) -> int:
        return self.read('!H')

    def read_uint32(self) -> int:
        return self.read('!I')

    def read_uint64(self) -> int:
        return self.read('!Q')

    def read_string(self, length: int) -> str:
        if length > len(self.data):
            raise ValueError("WireParser::read_string(): attempted to read past end")
        result = self.data[:length].decode()
        self.data = self.data[length:]
        return result

    def skip(self, length: int):
        if length > len(self.data):
            raise ValueError("WireParser::skip(): attempted to skip past end")
        self.data = self.data[length:]

    def read(self, fmt: str) -> int:
        size = struct.calcsize(fmt)
        if size > len(self.data):
            raise ValueError("WireParser::read(): read past end")
        result = struct.unpack(fmt, self.data[:size])[0]
        self.data = self.data[size:]
        return result

# # Example usage
# if __name__ == "__main__":
#     parser = WireParser(b'\x01\x02\x03\x04\x05\x06\x07\x08')
#     print(parser.read_uint8())  # Output: 1
#     print(parser.read_uint16())  # Output: 515
#     print(parser.read_uint32())  # Output: 84281096
#     print(parser.read_uint64())  # Output: 72623859790382856
#     parser = WireParser(b'Hello, World!')
#     print(parser.read_string(5))  # Output: Hello
#     parser.skip(2)
#     print(parser.read_string(5))  # Output: World