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
from exception_rim import UnixError, check_syscall

class Poller:
    """
    // type definitions
    enum Flag : short {
        In = POLLIN,
        Out = POLLOUT
    };
    """
    class Flag:
        In = select.POLLIN
        Out = select.POLLOUT

    def __init__(self):
        self.roster: Dict[int, Dict[int, Callable[[], None]]] = defaultdict(dict)
        self.active_events: Dict[int, int] = defaultdict(int)
        self.fds_to_deregister: Set[int] = set()

    """
    void Poller::register_event(const int fd,
                                const Flag flag,
                                const Callback callback)
    {
        if (not roster_.count(fd)) { // fd is not registered yet
            roster_[fd][flag] = callback;
            active_events_[fd] = flag;
        }
        else { // fd is registered but flag should not be registered yet
            if (roster_[fd].count(flag)) {
            throw runtime_error("attempted to register the same event");
            }

            roster_[fd][flag] = callback;
            active_events_[fd] |= flag;
        }
    }

    void Poller::register_event(const FileDescriptor & fd,
                                const Flag flag,
                                const Callback callback)
    {
        register_event(fd.fd_num(), flag, callback);
    }
    """
    def register_event(self, fd: int, flag: int, callback: Callable[[], None]):
        if fd not in self.roster:
            self.roster[fd][flag] = callback
            self.active_events[fd] = flag
        else:
            if flag in self.roster[fd]:
                raise RuntimeError("attempted to register the same event")
            self.roster[fd][flag] = callback
            self.active_events[fd] |= flag

    """
    void Poller::activate(const int fd, const Flag flag)
    {
        active_events_.at(fd) |= flag;
    }

    void Poller::activate(const FileDescriptor & fd, const Flag flag)
    {
        activate(fd.fd_num(), flag);
    }
    """
    def activate(self, fd: int, flag: int):
        self.active_events[fd] |= flag

    """
    void Poller::deactivate(const int fd, const Flag flag)
    {
        active_events_.at(fd) &= ~flag;
    }

    void Poller::deactivate(const FileDescriptor & fd, const Flag flag)
    {
        deactivate(fd.fd_num(), flag);
    }
    """
    def deactivate(self, fd: int, flag: int):
        self.active_events[fd] &= ~flag

    """
    void Poller::deregister(const int fd)
    {
        fds_to_deregister_.emplace(fd);
    }

    void Poller::deregister(const FileDescriptor & fd)
    {
        deregister(fd.fd_num());
    }
    """
    def deregister(self, fd: int):
        self.fds_to_deregister.add(fd)

    """
    void Poller::do_deregister()
    {
        for (const int fd : fds_to_deregister_) {
            roster_.erase(fd);
            active_events_.erase(fd);
        }

        fds_to_deregister_.clear();
    }
    """
    def do_deregister(self):
        for fd in self.fds_to_deregister:
            if fd in self.roster:
                del self.roster[fd]
            if fd in self.active_events:
                del self.active_events[fd]
        self.fds_to_deregister.clear()

    """
    void Poller::poll(const int timeout_ms)
    {
        // first, deregister the fds that have been scheduled to deregister
        do_deregister();

        // construct a list of fds to poll
        vector<pollfd> fds_to_poll;
        for (const auto [fd, events] : active_events_) {
            if (events != 0) {
            fds_to_poll.push_back({fd, events, 0});
            }
        }

        check_syscall(::poll(fds_to_poll.data(), fds_to_poll.size(), timeout_ms));

        for (const auto & it : fds_to_poll) {
            for (const auto & [flag, callback] : roster_.at(it.fd)) {
            if (it.revents & flag) {
                assert(it.events & flag); // returned event must have been requested
                callback(); // execute the callback function
            }
            }
        }
    }
    """
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