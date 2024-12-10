import socket

class Address:
    def __init__(self, ip: str = None, port: int = None, addr: tuple = None):
        if addr:
            self._addr = addr
            self._size = len(addr)
        elif ip and port:
            self._addr = socket.getaddrinfo(ip, port, socket.AF_INET, socket.SOCK_STREAM)[0][4]
            self._size = len(self._addr)
        else:
            raise ValueError("Either ip and port or addr must be provided")

    def sock_addr(self) -> tuple:
        return self._addr
    

    def size(self) -> int:
        return self._size

    def ip_port(self) -> tuple:
        ip, port = socket.getnameinfo(self._addr, socket.NI_NUMERICHOST | socket.NI_NUMERICSERV)
        return ip, int(port)

    def ip(self) -> str:
        return self.ip_port()[0]

    def port(self) -> int:
        return self.ip_port()[1]
    
    def __str__(self) -> str:
        ip, port = self.ip_port()
        return f"{ip}:{port}"

    def __eq__(self, other) -> bool:
        return self._size == other._size and self._addr == other._addr