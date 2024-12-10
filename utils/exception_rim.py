import errno
import os
import traceback
import inspect
from typing import Any
from termcolor import colored


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

def check_syscall(return_value):
    try:
        if return_value >= 0:
            return return_value
        else:
            raise UnixError()
    except UnixError as e:
        print(f"System call failed with error: {e}")
        raise

def check_syscall_with_tag(return_value, tag):
    try:
        if return_value >= 0:
            return return_value
        else:
            raise UnixError(tag)
    except UnixError as e:
        print(f"System call failed with error: {e}")
        raise

def check_call(actual_return: Any, 
               expected_return: Any, 
               error_msg: str = "check_call",
               stack_depth: int = 5) -> None:
    """Enhanced error checking with colored traceback"""
    if actual_return != expected_return:
        # Get stack trace
        stack = traceback.extract_stack()[:-1]
        stack = stack[-stack_depth:] if len(stack) > stack_depth else stack
        
        # Format colored error info
        error_parts = [
            colored(f"\nError: {error_msg}", "red", attrs=["bold"]),
            colored(f"Expected: {expected_return} ({type(expected_return)})", "yellow"),
            colored(f"Actual: {actual_return} ({type(actual_return)})", "yellow"),
        ]

        # Add system error if available 
        if isinstance(actual_return, int) and actual_return < 0:
            try:
                sys_error = os.strerror(-actual_return)
                error_parts.append(colored(f"System Error: {sys_error}", "red"))
            except:
                pass

        # Format stack trace with colored context
        error_parts.append(colored("\nStack trace:", "blue", attrs=["bold"]))
        for frame in reversed(stack):
            error_parts.extend([
                colored(f"  File '{frame.filename}', line {frame.lineno}, in {frame.name}", "blue"),
                colored(f"    {frame.line.strip()}", "white")
            ])
            # Try to get local variable info
            try:
                locals_dict = inspect.currentframe().f_back.f_locals
                if locals_dict:
                    vars_str = ", ".join(f"{k}={v}" for k,v in locals_dict.items()
                                       if not k.startswith('__'))
                    error_parts.append(colored(f"    locals: {vars_str}", "cyan"))
            except:
                pass

        raise RuntimeError("\n".join(error_parts))
