"""
This Python code mirrors the functionality of the provided C++ code, 
including splitting a string based on a separator and handling the case 
where the separator is empty by raising an exception. 
The split function returns a list of substrings.
"""

"""
vector<string> split(const string & str, const string & separator)
{
  if (separator.empty()) {
    throw runtime_error("empty separator");
  }

  vector<string> ret;

  size_t curr_pos = 0;
  while (curr_pos < str.size()) {
    size_t next_pos = str.find(separator, curr_pos);

    if (next_pos == string::npos) {
      ret.emplace_back(str.substr(curr_pos));
      break;
    } else {
      ret.emplace_back(str.substr(curr_pos, next_pos - curr_pos));
      curr_pos = next_pos + separator.size();
    }
  }

  return ret;
}
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