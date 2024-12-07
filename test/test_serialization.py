from utils.serialization import WireParser

# Example usage
if __name__ == "__main__":
    parser = WireParser(b'\x01\x02\x03\x04\x05\x06\x07\x08')
    print(parser.read_uint8())  # Output: 1
    print(parser.read_uint16())  # Output: 515
    print(parser.read_uint32())  # Output: 84281096
    # print(parser.read_uint64())  # Output: 72623859790382856
    parser = WireParser(b'Hello, World!')
    print(parser.read_string(5))  # Output: Hello
    parser.skip(2)
    print(parser.read_string(5))  # Output: World