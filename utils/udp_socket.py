import os
import socket
import errno
import sys
from typing import Optional, Tuple

from termcolor import colored
from .address import Address  
from .exception_rim import UnixError
from .socket_rim import Socket

class UDPSocket(Socket):
    UDP_MTU = 65536  # Maximum transmission unit for UDP

    def __init__(self, domain: int = socket.AF_INET, type: int = socket.SOCK_DGRAM):
        super().__init__(domain, type)


    def check_bytes_sent(self, bytes_sent: int, target: int) -> bool:
        if bytes_sent <= 0:
            if bytes_sent == -1 and os.errno == errno.EWOULDBLOCK:
                return False  # return false to indicate EWOULDBLOCK
            raise UnixError("UDPSocket:send()/sendto()")
        
        if bytes_sent != target:
            raise RuntimeError("UDPSocket failed to deliver target number of bytes")
        
        return True


    def send(self, data: str) -> bool:
        """Send data over UDP socket.
            
        Args:
            data: String or bytes to send
        Returns:
            bool: True if all data was sent successfully
        """
        if not data:
            raise RuntimeError("attempted to send empty data")
            
        try:
            # Convert to bytes if string
            data_bytes = data.encode() if isinstance(data, str) else data
            bytes_sent = self._sock.send(data_bytes, 0)
            return self.check_bytes_sent(bytes_sent, len(data_bytes))
            
        except ConnectionRefusedError:
            # print(colored("Connection refused - peer not ready", "yellow"), 
                # file=sys.stderr)
            return False
            
        except ConnectionResetError:
            print(colored("Connection reset by peer", "yellow"), 
                file=sys.stderr)
            return False
            
        except OSError as e:
            if e.errno in (errno.ECONNREFUSED, errno.ECONNRESET):
                return False
            print(colored(f"Socket error: {e}", "red"), file=sys.stderr)
            raise


    def sendto(self, dst_addr: Address, data: str) -> bool:
        if not data:
            raise RuntimeError("attempted to send empty data")
        
        bytes_sent = self._sock.sendto(data.encode(), dst_addr.sock_addr())

        return self.check_bytes_sent(bytes_sent, len(data))


    def check_bytes_received(self, bytes_received: int) -> bool:
        if bytes_received < 0:
            if bytes_received == -1 and os.errno == errno.EWOULDBLOCK:
                return False  # return false to indicate EWOULDBLOCK
            
            raise UnixError("UDPSocket:recv()/recvfrom()")
        
        if bytes_received > self.UDP_MTU:
            raise RuntimeError("UDPSocket::recv()/recvfrom(): datagram truncated")
        
        return True


    def recv(self) -> Optional[bytes]:
        """Receive data from UDP socket.
        
        Returns:
            Optional[bytes]: Received data or None if error/no data
        """
        try:
            # data to receive
            buf = bytearray(self.UDP_MTU)
            bytes_received = self._sock.recv_into(buf, self.UDP_MTU)
            if not self.check_bytes_received(bytes_received):
                return None
            return bytes(buf[:bytes_received])
            
        except BlockingIOError:
            return None  # No data available (non-blocking socket)
            
        except ConnectionRefusedError:
            # print(colored("Connection refused - peer not ready", "yellow"), 
                # file=sys.stderr)
            return None
            
        except ConnectionResetError:
            # print(colored("Connection reset by peer", "yellow"), 
            #     file=sys.stderr)
            return None
            
        except OSError as e:
            if e.errno in (errno.ECONNREFUSED, errno.ECONNRESET):
                return None
            print(colored(f"Socket error: {e}", "red"), file=sys.stderr)
            raise


    def recvfrom(self) -> Tuple[Address, Optional[bytes]]:
        """Receive data and sender address from UDP socket.
        
        Returns:
            Tuple[Address, Optional[bytes]]: Sender address and received data or None
        """
        buf = bytearray(self.UDP_MTU)
        try:
            bytes_received, addr = self._sock.recvfrom_into(buf, self.UDP_MTU)
            if not self.check_bytes_received(bytes_received):
                return None, None
            return Address(addr=addr), bytes(buf[:bytes_received])
        except BlockingIOError:
            return None, None
        except socket.error as e:
            raise RuntimeError(f"recvfrom failed: {e}")