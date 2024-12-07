import socket
import struct

class Address:
    """
    Address::Address(const std::string & ip, const uint16_t port)
    {
        addrinfo hints;
        memset(&hints, 0, sizeof(hints));
        hints.ai_family = AF_INET;

        // resolved address
        addrinfo * result;

        const int ret_code = getaddrinfo(ip.c_str(), to_string(port).c_str(),
                                        &hints, &result);
        if (ret_code != 0) {
            throw runtime_error(gai_strerror(ret_code));
        }

        size_ = result->ai_addrlen;
        memcpy(&addr_, result->ai_addr, size_);
    }

    Address::Address(const sockaddr & addr, const socklen_t size)
    {
        if (size > sizeof(addr_)) {
            throw runtime_error("invalid sockaddr size");
        }

        size_ = size;
        memcpy(&addr_, &addr, size_);
    }
    """
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

    """
    pair<string, uint16_t> Address::ip_port() const
    {
        char ip[NI_MAXHOST], port[NI_MAXSERV];

        const int ret_code = getnameinfo(&addr_, size_,
                                        ip, sizeof(ip), port, sizeof(port),
                                        NI_NUMERICHOST | NI_NUMERICSERV);
        if (ret_code != 0) {
            throw runtime_error(gai_strerror(ret_code));
        }

        return {ip, stoi(port)};
    }    
    """
    def ip_port(self) -> tuple:
        ip, port = socket.getnameinfo(self._addr, socket.NI_NUMERICHOST | socket.NI_NUMERICSERV)
        return ip, int(port)

    """
    std::string ip() const { return ip_port().first; }   
    """
    def ip(self) -> str:
        return self.ip_port()[0]

    """
    uint16_t port() const { return ip_port().second; }
    """
    def port(self) -> int:
        return self.ip_port()[1]
    
    """
    string Address::str() const
    {
        const auto & [ip, port] = ip_port();
        return ip + ":" + to_string(port);
    }
    """
    def __str__(self) -> str:
        ip, port = self.ip_port()
        return f"{ip}:{port}"

    """
    bool Address::operator==(const Address & other) const
    {
        return size_ == other.size_ and memcmp(&addr_, &other.addr_, size_) == 0;
    }
    """
    def __eq__(self, other) -> bool:
        return self._size == other._size and self._addr == other._addr