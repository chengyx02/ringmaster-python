"""
Plan
Import necessary Python modules.
Define the UnixError exception class.
Define the check_syscall function to handle system call errors.
Define the Poller class with methods:
__init__: Initialize the poller.
register_event: Register a single event on a file descriptor with a callback function.
activate: Activate an event on a file descriptor.
deactivate: Deactivate an event on a file descriptor.
deregister: Deregister a file descriptor from the interest list.
do_deregister: Actually deregister file descriptors in the fds_to_deregister_ set.
poll: Execute the callbacks on the ready file descriptors.
Code

This Python code mirrors the functionality of the provided C++ code, 
including event registration, activation, deactivation, and polling. 
The Poller class provides methods for managing file descriptor events 
and executing callbacks when events are triggered. 
The UnixError class and check_syscall function handle system call errors.
"""

import os
import select
from collections import defaultdict
from typing import Callable, Dict, Set, Tuple

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

class Poller:
    class Flag:
        In = select.POLLIN
        Out = select.POLLOUT

    def __init__(self):
        self.roster: Dict[int, Dict[int, Callable[[], None]]] = defaultdict(dict)
        self.active_events: Dict[int, int] = defaultdict(int)
        self.fds_to_deregister: Set[int] = set()

    def register_event(self, fd: int, flag: int, callback: Callable[[], None]):
        if fd not in self.roster:
            self.roster[fd][flag] = callback
            self.active_events[fd] = flag
        else:
            if flag in self.roster[fd]:
                raise RuntimeError("attempted to register the same event")
            self.roster[fd][flag] = callback
            self.active_events[fd] |= flag

    def activate(self, fd: int, flag: int):
        self.active_events[fd] |= flag

    def deactivate(self, fd: int, flag: int):
        self.active_events[fd] &= ~flag

    def deregister(self, fd: int):
        self.fds_to_deregister.add(fd)

    def do_deregister(self):
        for fd in self.fds_to_deregister:
            if fd in self.roster:
                del self.roster[fd]
            if fd in self.active_events:
                del self.active_events[fd]
        self.fds_to_deregister.clear()

    def poll(self, timeout_ms: int = -1):
        self.do_deregister()

        fds_to_poll = []
        for fd, events in self.active_events.items():
            if events != 0:
                fds_to_poll.append((fd, events))

        poller = select.poll()
        for fd, events in fds_to_poll:
            poller.register(fd, events)

        events = poller.poll(timeout_ms)
        check_syscall(len(events))

        for fd, revents in events:
            for flag, callback in self.roster[fd].items():
                if revents & flag:
                    assert self.active_events[fd] & flag
                    callback()

# Example usage
if __name__ == "__main__":
    def example_callback():
        print("Event triggered")

    poller = Poller()
    fd = os.open("example.txt", os.O_RDWR | os.O_CREAT)
    poller.register_event(fd, Poller.Flag.In, example_callback)
    poller.activate(fd, Poller.Flag.In)
    poller.poll(1000)
    os.close(fd)