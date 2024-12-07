from utils.udp_socket import UDPSocket
from utils.address import Address

# Example usage
try:
    # Start a UDP server to receive the message
    def udp_server():
        server_sock = UDPSocket()
        server_sock._sock.bind(("127.0.0.1", 8080))
        print("UDP server up and listening")
        addr, data = server_sock.recvfrom()
        print(f"Received message: {data} from {addr}")
        server_sock.close()

    import threading
    server_thread = threading.Thread(target=udp_server)
    server_thread.start()

    # Send a message using UDPSocket
    udp_socket = UDPSocket()
    udp_socket.sendto(Address(ip="127.0.0.1", port=8080), "Hello, World!")
    print("Message sent")
    udp_socket.close()

    # Wait for the server thread to finish
    server_thread.join()
except Exception as e:
    print(f"Error: {e}")