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
from typing import Optional, Tuple
import struct
from address import Address  
from exception_rim import UnixError, check_syscall
from socket_rim import Socket

class UDPSocket(Socket):
    UDP_MTU = 65536 # 65507  # Maximum transmission unit for UDP

    def __init__(self, domain: int = socket.AF_INET, type: int = socket.SOCK_DGRAM):
        super().__init__(domain, type)

    """
    bool UDPSocket::check_bytes_sent(const ssize_t bytes_sent,
                                 const size_t target) const
    {
        if (bytes_sent <= 0) {
            if (bytes_sent == -1 and errno == EWOULDBLOCK) {
            return false; // return false to indicate EWOULDBLOCK
            }

            throw unix_error("UDPSocket:send()/sendto()");
        }

        if (static_cast<size_t>(bytes_sent) != target) {
            throw runtime_error("UDPSocket failed to deliver target number of bytes");
        }

        return true;
    }
    """
    def check_bytes_sent(self, bytes_sent: int, target: int) -> bool:
        if bytes_sent <= 0:
            if bytes_sent == -1 and os.errno == errno.EWOULDBLOCK:
                return False  # return false to indicate EWOULDBLOCK
            raise UnixError("UDPSocket:send()/sendto()")
        if bytes_sent != target:
            raise RuntimeError("UDPSocket failed to deliver target number of bytes")
        return True

    """
    bool UDPSocket::send(const string_view data)
    {
        if (data.empty()) {
            throw runtime_error("attempted to send empty data");
        }

        const ssize_t bytes_sent = ::send(fd_num(), data.data(), data.size(), 0);
        return check_bytes_sent(bytes_sent, data.size());
    }
    """
    def send(self, data: str) -> bool:
        if not data:
            raise RuntimeError("attempted to send empty data")
        bytes_sent = self._sock.send(data.encode(), 0)
        return self.check_bytes_sent(bytes_sent, len(data))

    """
    bool UDPSocket::sendto(const Address & dst_addr, const string_view data)
    {
        if (data.empty()) {
            throw runtime_error("attempted to send empty data");
        }

        const ssize_t bytes_sent = ::sendto(fd_num(), data.data(), data.size(), 0,
                                            &dst_addr.sock_addr(), dst_addr.size());
        return check_bytes_sent(bytes_sent, data.size());
    }
    """
    def sendto(self, dst_addr: Address, data: str) -> bool:
        if not data:
            raise RuntimeError("attempted to send empty data")
        bytes_sent = self._sock.sendto(data.encode(), dst_addr.sock_addr())
        return self.check_bytes_sent(bytes_sent, len(data))

    """
    bool UDPSocket::check_bytes_received(const ssize_t bytes_received) const
    {
        if (bytes_received < 0) {
            if (bytes_received == -1 and errno == EWOULDBLOCK) {
            return false; // return false to indicate EWOULDBLOCK
            }

            throw unix_error("UDPSocket:recv()/recvfrom()");
        }

        if (static_cast<size_t>(bytes_received) > UDP_MTU) {
            throw runtime_error("UDPSocket::recv()/recvfrom(): datagram truncated");
        }

        return true;
    }
    """
    def check_bytes_received(self, bytes_received: int) -> bool:
        if bytes_received < 0:
            if bytes_received == -1 and os.errno == errno.EWOULDBLOCK:
                return False  # return false to indicate EWOULDBLOCK
            raise UnixError("UDPSocket:recv()/recvfrom()")
        if bytes_received > self.UDP_MTU:
            raise RuntimeError("UDPSocket::recv()/recvfrom(): datagram truncated")
        return True

    """
    optional<string> UDPSocket::recv()
    {
        // data to receive
        vector<char> buf(UDP_MTU);

        const ssize_t bytes_received = ::recv(fd_num(), buf.data(),
                                                UDP_MTU, MSG_TRUNC);
        if (not check_bytes_received(bytes_received)) {
            return nullopt;
        }

        return string{buf.data(), static_cast<size_t>(bytes_received)};
    }
    """
    def recv(self) -> Optional[str]:
        buf = bytearray(self.UDP_MTU)
        bytes_received = os.recv(self.fd_num(), buf, os.MSG_TRUNC)
        if not self.check_bytes_received(bytes_received):
            return None
        return buf[:bytes_received].decode()

    """
    pair<Address, optional<string>> UDPSocket::recvfrom()
    {
        // data to receive and its source address
        vector<char> buf(UDP_MTU);
        sockaddr src_addr;
        socklen_t src_addr_len = sizeof(src_addr);

        const ssize_t bytes_received = ::recvfrom(
            fd_num(), buf.data(), UDP_MTU, MSG_TRUNC, &src_addr, &src_addr_len);
        if (not check_bytes_received(bytes_received)) {
            return { Address{src_addr, src_addr_len}, nullopt };
        }

        return { Address{src_addr, src_addr_len},
                string{buf.data(), static_cast<size_t>(bytes_received)} };
    }
    """
    def recvfrom(self) -> Tuple[Address, Optional[str]]:
        buf = bytearray(self.UDP_MTU)
        src_addr_len = socket.ntohs(struct.calcsize('HHL'))
        # src_addr = bytearray(src_addr_len)
        try:
            bytes_received, addr = self._sock.recvfrom_into(buf, src_addr_len)
        except socket.error as e:
            if e.errno == errno.EWOULDBLOCK:
                return None, None
            raise
        if not self.check_bytes_received(bytes_received):
            return None, None
        return Address(addr=addr), buf[:bytes_received].decode()