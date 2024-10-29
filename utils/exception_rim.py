import errno
import os

"""
#include <system_error>
#include <stdexcept>

class unix_error : public std::system_error
{
public:
  unix_error()
    : system_error(errno, std::system_category()) {}

  unix_error(const std::string & tag)
    : system_error(errno, std::system_category(), tag) {}
};
"""
class UnixError(OSError):
    def __init__(self, tag=None):
        current_errno = errno.EINVAL
        self.errno = current_errno
        self.strerror = os.strerror(current_errno)
        self.tag = tag
        if tag:
            super().__init__(current_errno, self.strerror, tag)
        else:
            super().__init__(current_errno, self.strerror)

    def __str__(self):
        if self.tag:
            return f"{self.strerror}: {self.tag}"
        return self.strerror

"""
inline int check_syscall(const int return_value)
{
  if (return_value >= 0) {
    return return_value;
  }
  throw unix_error();
}
"""
def check_syscall(return_value):
    try:
        if return_value >= 0:
            return return_value
        else:
            raise UnixError()
    except UnixError as e:
        print(f"System call failed with error: {e}")
        raise

"""
inline int check_syscall(const int return_value, const std::string & tag)
{
  if (return_value >= 0) {
    return return_value;
  }
  throw unix_error(tag);
}
"""
def check_syscall_with_tag(return_value, tag):
    if return_value >= 0:
        return return_value
    else:
        raise UnixError(tag)

"""
template<typename T>
inline void check_call(const T & actual_return, const T & expected_return,
                       const std::string & error_msg = "check_call")
{
  if (actual_return != expected_return) {
    throw std::runtime_error(error_msg);
  }
}
"""
def check_call(actual_return, expected_return, error_msg="check_call"):
    if actual_return!= expected_return:
        raise RuntimeError(error_msg)
    
if __name__ == "__main__":

    try:
        check_syscall(-1)
    except UnixError as e:
        print(e)

    try:
        check_syscall_with_tag(-1, "Custom tag")
    except UnixError as e:
        print(e)

    try:
        check_call(1, 2, "Values do not match")
    except RuntimeError as e:
        print(e)


    raise UnixError("FileDescriptor::write()")
    print("123")
