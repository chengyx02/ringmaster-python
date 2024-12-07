from utils.address import Address

# Example usage
try:
    addr1 = Address(ip="127.0.0.1", port=8080)
    print(addr1)  # Output: 127.0.0.1:8080

    addr2 = Address(addr=addr1._addr)
    print(addr2)  # Output: 127.0.0.1:8080

    print(addr1 == addr2)  # Output: True
except Exception as e:
    print(f"Error: {e}")