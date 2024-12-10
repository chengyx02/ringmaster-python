import os
import struct
import ctypes
from .file_descriptor import FileDescriptor
from .exception_rim import check_syscall
from .conversion import narrow_cast


# timerfd_create with ctypes
libc = ctypes.CDLL('libc.so.6')

# Constants
CLOCK_REALTIME = 0
CLOCK_MONOTONIC = 1
TFD_NONBLOCK = 0o4000
TFD_CLOEXEC = 0o2000000

class timespec(ctypes.Structure):
    _fields_ = [
        ("tv_sec", ctypes.c_long), 
        ("tv_nsec", ctypes.c_long)
    ]

class itimerspec(ctypes.Structure):
    _fields_ = [
        ("it_interval", timespec),
        ("it_value", timespec)
    ]

timerfd_create = libc.timerfd_create
timerfd_create.argtypes = [ctypes.c_int, ctypes.c_int]
timerfd_create.restype = ctypes.c_int

timerfd_settime = libc.timerfd_settime
timerfd_settime.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(itimerspec), ctypes.POINTER(itimerspec)]
timerfd_settime.restype = ctypes.c_int

class Timerfd(FileDescriptor):

    def __init__(self, clockid: int = CLOCK_MONOTONIC, flags: int = 0):
        fd = check_syscall(timerfd_create(clockid, flags))
        super().__init__(fd)


    def set_time(self, initial_expiration, interval):
        its = itimerspec()
        its.it_value.tv_sec = initial_expiration[0]
        its.it_value.tv_nsec = initial_expiration[1]
        its.it_interval.tv_sec = interval[0]
        its.it_interval.tv_nsec = interval[1]

        check_syscall(timerfd_settime(self.fd_num(), 0, ctypes.byref(its), None))


    def read_expirations(self) -> int:
        buf = ctypes.c_uint64()
        size = ctypes.sizeof(buf)
        result = os.read(self._fd, size)
        
        if len(result) != size: # 8
            raise RuntimeError("read error in timerfd")
            
        num_exp = struct.unpack('Q', result)[0]  # Q = uint64
        # return int.from_bytes(result, byteorder='little')
        return narrow_cast(int, num_exp)
    
    def fileno(self) -> int:
        return self._fd