"""
This Python code mirrors the functionality of the provided C++ code, 
including splitting a string based on a separator and handling the case 
where the separator is empty by raising an exception. 
The split function returns a list of substrings.
"""

def split(s: str, separator: str) -> list:
    if not separator:
        raise ValueError("empty separator")

    ret = []
    curr_pos = 0

    while curr_pos < len(s):
        next_pos = s.find(separator, curr_pos)

        if next_pos == -1:
            ret.append(s[curr_pos:])
            break
        else:
            ret.append(s[curr_pos:next_pos])
            curr_pos = next_pos + len(separator)

    return ret

# # Example usage
# try:
#     result = split("hello world this is a test", " ")
#     print(result)  # Output: ['hello', 'world', 'this', 'is', 'a', 'test']
# except ValueError as e:
#     print(f"Error: {e}")