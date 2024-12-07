import socket
from utils.socket_rim import Socket
from utils.address import Address

# Example usage
try:
    sock = Socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.set_reuseaddr()
    addr = Address(ip="127.0.0.1", port=18080)
    sock.bind(addr)
    print(f"Local address: {sock.local_address()}")
    sock.close()
except Exception as e:
    print(f"Error: {e}")