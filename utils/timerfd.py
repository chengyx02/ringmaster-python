"""
This Python code mirrors the functionality of the provided C++ code, 
including timer file descriptor management, setting timer intervals, and reading the 
number of expirations. The Timerfd class inherits from FileDescriptor and provides methods 
for setting and reading timer values. The UnixError class and check_syscall function 
handle system call errors. 
The narrow_cast function ensures no precision is lost during type casting
"""

import os
import struct
import time
import ctypes
from file_descriptor import FileDescriptor
from exception_rim import check_syscall
from conversion import narrow_cast

class timespec(ctypes.Structure):
    _fields_ = [("tv_sec", ctypes.c_long), ("tv_nsec", ctypes.c_long)]

class itimerspec(ctypes.Structure):
    _fields_ = [("it_interval", timespec), ("it_value", timespec)]

# timerfd_create with ctypes
libc = ctypes.CDLL('libc.so.6')
TIMERFD_CREATE = libc.timerfd_create
TIMERFD_CREATE.argtypes = [ctypes.c_int, ctypes.c_int]
TIMERFD_CREATE.restype = ctypes.c_int

TIMERFD_SETTIME = libc.timerfd_settime
TIMERFD_SETTIME.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(itimerspec), ctypes.POINTER(itimerspec)]
TIMERFD_SETTIME.restype = ctypes.c_int

class Timerfd(FileDescriptor):
    """
    Timerfd::Timerfd(int clockid, int flags)
        : FileDescriptor(check_syscall(timerfd_create(clockid, flags)))
    {}
    """
    def __init__(self, clockid: int = time.CLOCK_MONOTONIC, flags: int = os.O_NONBLOCK):
        fd = check_syscall(TIMERFD_CREATE(clockid, flags))
        super().__init__(fd)

    """
    void Timerfd::set_time(const timespec & initial_expiration,
                        const timespec & interval)
    {
        itimerspec its;
        its.it_value = initial_expiration;
        its.it_interval = interval;

        check_syscall(timerfd_settime(fd_num(), 0, &its, nullptr));
    }
    """
    def set_time(self, initial_expiration, interval):
        its = itimerspec()
        its.it_value = initial_expiration
        its.it_interval = interval
        check_syscall(TIMERFD_SETTIME(self.fd_num(), 0, ctypes.byref(its), None))

    """
    unsigned int Timerfd::read_expirations()
    {
        uint64_t num_exp = 0;

        if (check_syscall(::read(fd_num(), &num_exp, sizeof(num_exp)))
            != sizeof(num_exp)) {
            throw runtime_error("read error in timerfd");
        }

        return narrow_cast<unsigned int>(num_exp);
    }
    """
    def read_expirations(self) -> int:
        num_exp = struct.unpack('Q', os.read(self.fd_num(), 8))[0]
        return narrow_cast(int, num_exp)