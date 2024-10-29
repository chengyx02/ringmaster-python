"""
This Python code mirrors the functionality of the provided C++ code, 
including file descriptor management, reading, writing, and error handling. 
The FileDescriptor class provides methods for manipulating file descriptors, 
handling blocking modes, and performing I/O operations. 
The UnixError class and check_syscall function handle system call errors.
"""

import os
import fcntl
from exception_rim import UnixError, check_syscall
import errno


class FileDescriptor:
    """
    static constexpr size_t MAX_BUF_SIZE = 1024 * 1024; // 1 MB
    """
    MAX_BUF_SIZE = 1024 * 1024  # 1 MB

    """
    FileDescriptor::FileDescriptor(const int fd)
        : fd_(fd), eof_(false)
    {
        // set close-on-exec flag by default to prevent fds from leaking
        check_syscall(fcntl(fd_, F_SETFD, FD_CLOEXEC));
    }

    """
    def __init__(self, fd):
        self._fd = fd
        self._eof = False
        # set close-on-exec flag by default to prevent fds from leaking
        check_syscall(fcntl.fcntl(self._fd, fcntl.F_SETFD, fcntl.FD_CLOEXEC))
        

    """
    FileDescriptor::~FileDescriptor()
    {
        // don't throw from destructor
        if (fd_ >= 0 and ::close(fd_) < 0) {
            perror("failed to close file descriptor");
        }
    }
    """
    def __del__(self):
        # don't throw from destructor
        if self._fd >= 0:
            try:
                os.close(self._fd)
            except OSError:
                print("failed to close file descriptor")
    
    """
    FileDescriptor::FileDescriptor(FileDescriptor && other)
        : fd_(other.fd_), eof_(other.eof_)
    {
        other.fd_ = -1; // mark other file descriptor as inactive
    }
    """
    @classmethod
    def move(cls, other):
        if not isinstance(other, cls):
            raise TypeError("Expected an instance of FileDescriptor")
        new_fd = cls(other._fd, other._eof)
        other._fd = -1  # mark other file descriptor as inactive
        return new_fd

    """
    FileDescriptor & FileDescriptor::operator=(FileDescriptor && other)
    {
        fd_ = other.fd_;
        eof_ = other.eof_;
        other.fd_ = -1; // mark other file descriptor as inactive

        return *this;
    }
    """
    # def __repr__(self, other):
    #     if isinstance(other, FileDescriptor):
    #         self._fd = other._fd
    #         self._eof = other._eof
    #         other._fd = -1  
    #         return self
    #     else:
    #         raise TypeError("Expected an instance of FileDescriptor")
    def move_assign(self, other):
        if not isinstance(other, FileDescriptor):
            raise TypeError("Expected an instance of FileDescriptor")
        self._fd = other._fd
        self._eof = other._eof
        other._fd = -1   # mark other file descriptor as inactive
    

    """
    void FileDescriptor::close()
    {
        if (fd_ < 0) { // has already been moved away or closed
            return;
        }

        check_syscall(::close(fd_));

        fd_ = -1;
    }
    """
    def close(self):
        if self._fd < 0:  # has already been moved away or closed
            return
        # check_syscall(os.close(self._fd))
        os.close(self._fd)
        self._fd = -1

    """
    bool FileDescriptor::get_blocking() const
    {
        int flags = check_syscall(fcntl(fd_, F_GETFL));
        return !(flags & O_NONBLOCK);
    }
    """
    def get_blocking(self):
        flags = check_syscall(fcntl.fcntl(self._fd, fcntl.F_GETFL))
        return not (flags & os.O_NONBLOCK)

    """
    void FileDescriptor::set_blocking(const bool blocking)
    {
        int flags = check_syscall(fcntl(fd_, F_GETFL));

        if (blocking) {
            flags &= ~O_NONBLOCK;
        } else {
            flags |= O_NONBLOCK;
        }

        check_syscall(fcntl(fd_, F_SETFL, flags));
    }
    """
    def set_blocking(self, blocking):
        flags = check_syscall(fcntl.fcntl(self._fd, fcntl.F_GETFL))
        if blocking:
            flags &= ~os.O_NONBLOCK
        else:
            flags |= os.O_NONBLOCK
        check_syscall(fcntl.fcntl(self._fd, fcntl.F_SETFL, flags))

    """
    size_t FileDescriptor::write(const string_view data)
    {
        if (data.empty()) {
            throw runtime_error("attempted to write empty data");
        }

        const ssize_t bytes_written = ::write(fd_, data.data(), data.size());

        if (bytes_written <= 0) {
            if (bytes_written == -1 and errno == EWOULDBLOCK) {
            return 0; // return 0 to indicate EWOULDBLOCK
            }

            throw unix_error("FileDescriptor::write()");
        }

        return bytes_written;
    }
    """
    def write(self, data):
        if not data:
            raise ValueError("attempted to write empty data")
        bytes_written = os.write(self._fd, data.encode())
        if bytes_written <= 0:
            if bytes_written == -1 and os.errno == errno.EWOULDBLOCK:
                return 0  # return 0 to indicate EWOULDBLOCK
            raise UnixError("FileDescriptor::write()")
        return bytes_written

    """
    void FileDescriptor::writen(const string_view data, const size_t n)
    {
        if (data.empty() or n == 0) {
            throw runtime_error("attempted to write empty data");
        }

        if (data.size() < n) {
            throw runtime_error("data size is smaller than n");
        }

        const char * it = data.data();
        const char * end = it + n;

        while (it != end) {
            const ssize_t bytes_written = ::write(fd_, it, end - it);

            if (bytes_written <= 0) {
            throw unix_error("FileDescriptor::writen()");
            }

            it += bytes_written;
        }
    }
    """
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

    """
    void FileDescriptor::write_all(const string_view data)
    {
        writen(data, data.size());
    }
    """
    def write_all(self, data):
        self.writen(data, len(data))

    """
    string FileDescriptor::read(const size_t limit)
    {
        vector<char> buf(min(MAX_BUF_SIZE, limit));

        const size_t bytes_read = check_syscall(::read(fd_, buf.data(), buf.size()));

        if (bytes_read == 0) {
            eof_ = true;
        }

        return {buf.data(), bytes_read};
    }
    """
    def read(self, limit):
        buf = bytearray(min(self.MAX_BUF_SIZE, limit))
        bytes_read = os.read(self._fd, len(buf))
        if not bytes_read:
            self._eof = True
            return ''
        return bytes_read.decode()

    """
    string FileDescriptor::readn(const size_t n, const bool allow_partial_read)
    {
        if (n == 0) {
            throw runtime_error("attempted to read 0 bytes");
        }

        vector<char> buf(n);
        size_t total_read = 0;

        while (total_read != n) {
            const size_t bytes_read = check_syscall(
            ::read(fd_, buf.data() + total_read, n - total_read));

            if (bytes_read == 0) {
            eof_ = true;

            if (allow_partial_read) {
                return {buf.data(), total_read};
            } else {
                throw runtime_error("FileDescriptor::readn(): unexpected EOF");
            }
            }

            total_read += bytes_read;
        }

        return {buf.data(), total_read};
    }
    """
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
                    return buf[:total_read].decode()
                else:
                    raise RuntimeError("FileDescriptor::readn(): unexpected EOF")
            total_read += len(bytes_read)
        return bytes_read[:total_read].decode()

    """
    string FileDescriptor::getline()
    {
        string ret;

        while (true) {
            const string char_read = read(1);

            if (eof_ or char_read == "\n") {
            break;
            }

            ret += char_read;
        }

        return ret;
    }
    """
    def getline(self):
        ret = ""
        while True:
            char_read = self.read(1)
            if self._eof or char_read == "\n":
                break
            ret += char_read
        return ret

    """
    uint64_t FileDescriptor::seek(const int64_t offset, const int whence)
    {
        return check_syscall(lseek(fd_, offset, whence));
    }
    """
    def seek(self, offset, whence):
        return check_syscall(os.lseek(self._fd, offset, whence))

    """
    void FileDescriptor::reset_offset()
    {
        seek(0, SEEK_SET);
        eof_ = false;
    }
    """
    def reset_offset(self):
        self.seek(0, os.SEEK_SET)
        self._eof = False

    """
    uint64_t FileDescriptor::file_size()
    {
        // save the current offset
        const uint64_t saved_offset = seek(0, SEEK_CUR);

        // seek to the end of file to get file size
        const uint64_t ret = seek(0, SEEK_END);

        // seek back to the original offset
        seek(saved_offset, SEEK_SET);

        return ret;
    }
    """
    def file_size(self):
        # save the current offset
        saved_offset = self.seek(0, os.SEEK_CUR)
        # seek to the end of file to get file size
        ret = self.seek(0, os.SEEK_END)
        # seek back to the original offset
        self.seek(saved_offset, os.SEEK_SET)
        return ret
    
    """
    // accessors
    int fd_num() const { return fd_; }
    bool eof() const { return eof_; }
    """
    @property
    def fd_num(self):
        return self._fd

    @property
    def eof(self):
        return self._eof

# # Example usage
# try:
#     fd = os.open("example.txt", os.O_RDWR | os.O_CREAT)
#     file_desc = FileDescriptor(fd)
#     file_desc.write_all("Hello, World!"*200)
#     file_desc.reset_offset()
#     print(file_desc.readn(100, allow_partial_read=False))
#     file_desc.close()
# except Exception as e:
#     print(f"Error: {e}")