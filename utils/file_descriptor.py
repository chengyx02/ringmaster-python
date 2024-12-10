import os
import fcntl
from .exception_rim import UnixError, check_syscall
import errno


class FileDescriptor:

    MAX_BUF_SIZE = 1024 * 1024  # 1 MB

    def __init__(self, fd):
        self._fd = fd
        self._eof = False
        # set close-on-exec flag by default to prevent fds from leaking
        check_syscall(fcntl.fcntl(self._fd, fcntl.F_SETFD, fcntl.FD_CLOEXEC))
        
    def __del__(self):
        # don't throw from destructor
        if self._fd >= 0:
            try:
                os.close(self._fd)
            except OSError:
                print("failed to close file descriptor")
    
    @classmethod
    def move(cls, other):
        if not isinstance(other, cls):
            raise TypeError("Expected an instance of FileDescriptor")
        new_fd = cls(other._fd, other._eof)
        other._fd = -1  # mark other file descriptor as inactive
        return new_fd

    def move_assign(self, other):
        if not isinstance(other, FileDescriptor):
            raise TypeError("Expected an instance of FileDescriptor")
        self._fd = other._fd
        self._eof = other._eof
        other._fd = -1   # mark other file descriptor as inactive
    
    def close(self):
        if self._fd < 0:  # has already been moved away or closed
            return
        os.close(self._fd)
        self._fd = -1

    def get_blocking(self):
        flags = check_syscall(fcntl.fcntl(self._fd, fcntl.F_GETFL))
        return not (flags & os.O_NONBLOCK)


    def set_blocking(self, blocking):
        flags = check_syscall(fcntl.fcntl(self._fd, fcntl.F_GETFL))

        if blocking:
            flags &= ~os.O_NONBLOCK
        else:
            flags |= os.O_NONBLOCK

        check_syscall(fcntl.fcntl(self._fd, fcntl.F_SETFL, flags))

    def write(self, data):
        if not data:
            raise ValueError("attempted to write empty data")
        bytes_written = os.write(self._fd, data.encode())

        if bytes_written <= 0:
            if bytes_written == -1 and os.errno == errno.EWOULDBLOCK:
                return 0  # return 0 to indicate EWOULDBLOCK
            raise UnixError("FileDescriptor::write()")
        
        return bytes_written


    def writen(self, data, n):
        if not data or n == 0:
            raise ValueError("attempted to write empty data")
        
        if len(data) < n:
            raise ValueError("data size is smaller than n")
        
        it = 0
        end = n

        while it != end:
            bytes_written = os.write(self._fd, data[it:end].encode())
            if bytes_written <= 0:
                raise UnixError("FileDescriptor::writen()")
            it += bytes_written

    def write_all(self, data):
        self.writen(data, len(data))

    def read(self, limit):
        buf = bytearray(min(self.MAX_BUF_SIZE, limit))
        bytes_read = os.read(self._fd, len(buf))
        if not bytes_read:
            self._eof = True
            return ''
        return bytes_read

    def readn(self, n, allow_partial_read=False):
        if n == 0:
            raise ValueError("attempted to read 0 bytes")
        
        buf = bytearray(n)
        total_read = 0

        while total_read != n:
            bytes_read = os.read(self._fd, n-total_read)

            if not bytes_read:
                self._eof = True

                if allow_partial_read:
                    return buf[:total_read]
                else:
                    raise RuntimeError("FileDescriptor::readn(): unexpected EOF")
                
            total_read += len(bytes_read)

        return bytes_read[:total_read]

    def getline(self):
        ret = b''
        while True:
            char_read = self.read(1)
            if self._eof or char_read == b'\n' or char_read == b'':
                break
            ret += char_read
        return ret.decode('utf-8')

    def seek(self, offset, whence):
        return check_syscall(os.lseek(self._fd, offset, whence))

    def reset_offset(self):
        self.seek(0, os.SEEK_SET)
        self._eof = False


    def file_size(self):
        # save the current offset
        saved_offset = self.seek(0, os.SEEK_CUR)

        # seek to the end of file to get file size
        ret = self.seek(0, os.SEEK_END)

        # seek back to the original offset
        self.seek(saved_offset, os.SEEK_SET)

        return ret
    
    """
    accessors
    """
    def fd_num(self):
        return self._fd

    def eof(self):
        return self._eof