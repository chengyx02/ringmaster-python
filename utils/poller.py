import select
from collections import defaultdict
from typing import Callable, Dict, Set, Union

from utils.file_descriptor import FileDescriptor
from .exception_rim import check_syscall
from enum import IntEnum


class Flag(IntEnum):
    """Poll event flags"""
    In = select.POLLIN    # Data ready to be read
    Out = select.POLLOUT  # Ready for output 

class Poller:

    In = Flag.In
    Out = Flag.Out

    def __init__(self):
        self.roster_: Dict[int, Dict[int, Callable[[], None]]] = defaultdict(dict)
        self.active_events_: Dict[int, int] = defaultdict(int)
        self.fds_to_deregister_: Set[int] = set()


    def register_event(self, fd: Union[int, FileDescriptor], flag: int, 
                      callback: Callable[[], None]) -> None:

        # Convert FileDescriptor to int if needed
        fd_num = fd.fd_num() if isinstance(fd, FileDescriptor) else fd

        def _register_event_internal(fd_num: int, flag: int, callback: Callable[[], None]) -> None:
            # fd is not registered yet
            if fd_num not in self.roster_:
                self.roster_[fd_num] = {}  # Initialize dict first
                self.roster_[fd_num][flag] = callback
                self.active_events_[fd_num] = flag
                
            # fd is registered but flag should not be registered yet
            else:
                if flag in self.roster_[fd_num]:
                    raise RuntimeError("attempted to register the same event")
                
                self.roster_[fd_num][flag] = callback
                self.active_events_[fd_num] |= flag

        _register_event_internal(fd_num, flag, callback)


    def activate(self, fd: Union[int, FileDescriptor], flag: int):
        fd_num = fd.fd_num() if isinstance(fd, FileDescriptor) else fd
        self.active_events_[fd_num] |= flag


    def deactivate(self, fd: Union[int, FileDescriptor], flag: int):
        fd_num = fd.fd_num() if isinstance(fd, FileDescriptor) else fd
        self.active_events_[fd_num] &= ~flag


    def deregister(self, fd: Union[int, FileDescriptor]):
        fd_num = fd.fd_num() if isinstance(fd, FileDescriptor) else fd
        self.fds_to_deregister_.add(fd_num)


    def do_deregister(self):
        for fd in self.fds_to_deregister_:
            if fd in self.roster_:
                del self.roster_[fd]
            if fd in self.active_events_:
                del self.active_events_[fd]
        self.fds_to_deregister_.clear()


    def poll(self, timeout_ms: int) -> None:
        # first, deregister the fds that have been scheduled to deregister
        self.do_deregister()

        # construct a list of fds to poll
        poller = select.poll()
        fds_to_poll = []
        
        for fd, events in self.active_events_.items():
            if events != 0:
                # Convert FileDescriptor to int if needed
                fd_num = fd.fd_num() if isinstance(fd, FileDescriptor) else fd
                poller.register(fd_num, events)
                fds_to_poll.append((fd_num, events))

        events = poller.poll(timeout_ms)
        check_syscall(len(events))  # Check if poll succeeded

        for fd, revents in events:
            for flag, callback in self.roster_[fd].items():
                if revents & flag:
                    # Verify event was requested (matches C++ assert)
                    assert self.active_events_[fd] & flag, "Returned event must have been requested"
                    callback()  # execute the callback function
