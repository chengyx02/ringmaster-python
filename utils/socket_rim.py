import socket
import struct
from .file_descriptor import FileDescriptor
from .exception_rim import check_syscall
from .address import Address

class Socket(FileDescriptor):

    def __init__(self, domain: int, type: int):
        try:
            self._sock = socket.socket(domain, type)
            self._fd = self._sock.fileno()
            super().__init__(check_syscall(self._fd))
        except Exception as e:
            print(f"Error initializing socket: {e}")
            raise


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


    def getsockopt(self, level: int, option_name: int):
        option_value = struct.pack('i', 0)
        option_value = check_syscall(socket.getsockopt(self.fd_num(), level, option_name, len(option_value)))
        return struct.unpack('i', option_value)[0]


    def setsockopt(self, level: int, option_name: int, option_value: int):
        packed_value = struct.pack('i', option_value)
        self._sock.setsockopt(level, option_name, packed_value) # return None


    def bind(self, local_addr: Address):
        self._sock.bind(local_addr.sock_addr())  # return None


    def connect(self, peer_addr: Address):
        ret = self._sock.connect(peer_addr.sock_addr())
        check_syscall(ret if ret is not None else 0)


    def local_address(self) -> Address:
        addr = self._sock.getsockname()
        return Address(addr=addr)


    def peer_address(self) -> Address:
        addr = socket.getpeername(self.fd_num())
        return Address(addr=addr)


    def set_reuseaddr(self):
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)