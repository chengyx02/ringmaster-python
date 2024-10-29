"""
This Python code mirrors the functionality of the provided C++ code, 
including socket creation, option manipulation, binding, connecting, 
and address retrieval. 
The Socket class inherits from FileDescriptor and provides methods 
for managing socket options and connections. 
The UnixError class and check_syscall function handle system call errors. 
The Address class handles socket addresses.
"""

import os
import socket
import struct
from file_descriptor import FileDescriptor
from exception_rim import check_syscall
from conversion import narrow_cast
from address import Address

class Socket(FileDescriptor):
    """
    Socket::Socket(const int domain, const int type)
        : FileDescriptor(check_syscall(socket(domain, type, 0)))
    {}
    """
    def __init__(self, domain: int, type: int):
        try:
            self._sock = socket.socket(domain, type)
            self._fd = self._sock.fileno()
            super().__init__(check_syscall(self._fd))
        except Exception as e:
            print(f"Error initializing socket: {e}")
            raise

    """
    Socket::Socket(FileDescriptor && fd, const int domain, const int type)
        ileDescriptor(move(fd))
    {
        int actual_value;
        socklen_t len;

        // verify domain and type
        len = getsockopt(SOL_SOCKET, SO_DOMAIN, actual_value);
        if (len != sizeof(actual_value) or actual_value != domain) {
            throw runtime_error("socket domain mismatch");
        }

        len = getsockopt(SOL_SOCKET, SO_TYPE, actual_value);
        if (len != sizeof(actual_value) or actual_value != type) {
            throw runtime_error("socket type mismatch");
        }
    }
    """
    @classmethod
    def from_fd(cls, fd: FileDescriptor, domain: int, type: int):
        instance = cls.__new__(cls)
        super(Socket, instance).__init__(fd.fd_num())
        actual_value = instance.getsockopt(socket.SOL_SOCKET, socket.SO_DOMAIN)
        if actual_value != domain:
            raise RuntimeError("socket domain mismatch")
        actual_value = instance.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE)
        if actual_value != type:
            raise RuntimeError("socket type mismatch")
        return instance

    """
    template<typename OptionType>
    socklen_t Socket::getsockopt(const int level, const int option_name,
                                OptionType & option_value) const
    {
        socklen_t option_len = sizeof(option_value);
        check_syscall(::getsockopt(fd_num(), level, option_name,
                                    &option_value, &option_len));
        return option_len;
    }
    """
    def getsockopt(self, level: int, option_name: int):
        option_value = struct.pack('i', 0)
        option_value = check_syscall(socket.getsockopt(self.fd_num(), level, option_name, len(option_value)))
        return struct.unpack('i', option_value)[0]

    """
    template<typename OptionType>
    void Socket::setsockopt(const int level, const int option_name,
                            const OptionType & option_value)
    {
        check_syscall(::setsockopt(fd_num(), level, option_name,
                                    &option_value, sizeof(option_value)));
    }
    """
    def setsockopt(self, level: int, option_name: int, option_value: int):
        packed_value = struct.pack('i', option_value)
        self._sock.setsockopt(level, option_name, packed_value) # return None

    """
    void Socket::bind(const Address & local_addr)
    {
        check_syscall(::bind(fd_num(), &local_addr.sock_addr(), local_addr.size()));
    }
    """
    def bind(self, local_addr: Address):
        self._sock.bind(local_addr.sock_addr())  # return None

    """
    void Socket::connect(const Address & peer_addr)
    {
        check_syscall(::connect(fd_num(), &peer_addr.sock_addr(), peer_addr.size()));
    }
    """
    def connect(self, peer_addr: Address):
        check_syscall(socket.connect(self.fd_num(), peer_addr.sock_addr()))

    """
    Address Socket::local_address() const
    {
        sockaddr addr;
        socklen_t size = sizeof(addr);

        check_syscall(getsockname(fd_num(), &addr, &size));
        return {addr, size};
    }
    """
    def local_address(self) -> Address:
        addr = self._sock.getsockname()
        return Address(addr=addr)

    """
    Address Socket::peer_address() const
    {
        sockaddr addr;
        socklen_t size = sizeof(addr);

        check_syscall(getpeername(fd_num(), &addr, &size));
        return {addr, size};
    }
    """
    def peer_address(self) -> Address:
        addr = socket.getpeername(self.fd_num())
        return Address(addr=addr)

    """
    void Socket::set_reuseaddr()
    {
        setsockopt(SOL_SOCKET, SO_REUSEADDR, int(true));
    }
    """
    def set_reuseaddr(self):
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)