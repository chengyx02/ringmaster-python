"""
This Python code mirrors the functionality of the provided C++ code, 
including sending and receiving data over a UDP socket, checking the 
number of bytes sent and received, and handling errors. 
The UDPSocket class inherits from FileDescriptor and provides methods 
for sending and receiving data, both to a connected peer and to a specific address. 
The UnixError class and check_syscall function handle system call errors. 
The Address class handles socket addresses and is assumed to be defined in address.py.

"""

import os
import socket
import errno
import fcntl
from typing import Optional, Tuple
from address import Address  # Assuming Address class is defined in address.py

class UnixError(Exception):
    def __init__(self, tag=None):
        self.errno = os.errno
        self.strerror = os.strerror(self.errno)
        self.tag = tag
        super().__init__(self.__str__())

    def __str__(self):
        if self.tag:
            return f"{self.tag}: {self.strerror} (errno {self.errno})"
        else:
            return f"{self.strerror} (errno {self.errno})"

def check_syscall(return_value, tag=None):
    if return_value >= 0:
        return return_value
    raise UnixError(tag)

class FileDescriptor:
    def __init__(self, fd):
        self.fd_ = fd
        self.eof_ = False
        check_syscall(fcntl.fcntl(self.fd_, fcntl.F_SETFD, fcntl.FD_CLOEXEC))

    def __del__(self):
        if self.fd_ >= 0:
            try:
                os.close(self.fd_)
            except OSError:
                print("failed to close file descriptor")

    def close(self):
        if self.fd_ < 0:
            return
        check_syscall(os.close(self.fd_))
        self.fd_ = -1

    def fd_num(self):
        return self.fd_

class UDPSocket(FileDescriptor):
    UDP_MTU = 65507  # Maximum transmission unit for UDP

    def __init__(self, domain: int = socket.AF_INET, type: int = socket.SOCK_DGRAM):
        super().__init__(check_syscall(socket.socket(domain, type).fileno()))

    def check_bytes_sent(self, bytes_sent: int, target: int) -> bool:
        if bytes_sent <= 0:
            if bytes_sent == -1 and os.errno == errno.EWOULDBLOCK:
                return False  # return false to indicate EWOULDBLOCK
            raise UnixError("UDPSocket:send()/sendto()")
        if bytes_sent != target:
            raise RuntimeError("UDPSocket failed to deliver target number of bytes")
        return True

    def send(self, data: str) -> bool:
        if not data:
            raise RuntimeError("attempted to send empty data")
        bytes_sent = os.send(self.fd_num(), data.encode(), 0)
        return self.check_bytes_sent(bytes_sent, len(data))

    def sendto(self, dst_addr: Address, data: str) -> bool:
        if not data:
            raise RuntimeError("attempted to send empty data")
        bytes_sent = os.sendto(self.fd_num(), data.encode(), 0, dst_addr.sock_addr())
        return self.check_bytes_sent(bytes_sent, len(data))

    def check_bytes_received(self, bytes_received: int) -> bool:
        if bytes_received < 0:
            if bytes_received == -1 and os.errno == errno.EWOULDBLOCK:
                return False  # return false to indicate EWOULDBLOCK
            raise UnixError("UDPSocket:recv()/recvfrom()")
        if bytes_received > self.UDP_MTU:
            raise RuntimeError("UDPSocket::recv()/recvfrom(): datagram truncated")
        return True

    def recv(self) -> Optional[str]:
        buf = bytearray(self.UDP_MTU)
        bytes_received = os.recv(self.fd_num(), buf, os.MSG_TRUNC)
        if not self.check_bytes_received(bytes_received):
            return None
        return buf[:bytes_received].decode()

    def recvfrom(self) -> Tuple[Address, Optional[str]]:
        buf = bytearray(self.UDP_MTU)
        src_addr = bytearray(socket.sizeof(socket.sockaddr))
        src_addr_len = socket.sizeof(socket.sockaddr)
        bytes_received = os.recvfrom(self.fd_num(), buf, os.MSG_TRUNC, src_addr, src_addr_len)
        if not self.check_bytes_received(bytes_received):
            return Address(addr=src_addr), None
        return Address(addr=src_addr), buf[:bytes_received].decode()

# Example usage
try:
    udp_socket = UDPSocket()
    udp_socket.sendto(Address(ip="127.0.0.1", port=8080), "Hello, World!")
    print("Message sent")
    udp_socket.close()
except Exception as e:
    print(f"Error: {e}")