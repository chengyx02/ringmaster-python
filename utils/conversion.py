import re
from typing import TypeVar, Type

T = TypeVar('T', int, int)

"""
int strict_stoi(const string & str, const int base)
{
  size_t pos;
  int ret = stoi(str, &pos, base);

  if (pos != str.size()) {
    throw runtime_error("strict_stoi");
  }

  return ret;
}
"""
def strict_stoi(s: str, base: int = 10) -> int:
    match = re.fullmatch(r'[+-]?[0-9a-fA-F]+', s)
    if not match:
        raise ValueError("strict_stoi")
    return int(s, base)

"""
long long strict_stoll(const string & str, const int base)
{
  size_t pos;
  int ret = stoll(str, &pos, base);

  if (pos != str.size()) {
    throw runtime_error("strict_stoll");
  }

  return ret;
}
"""
def strict_stoll(s: str, base: int = 10) -> int:
    match = re.fullmatch(r'[+-]?[0-9a-fA-F]+', s)
    if not match:
        raise ValueError("strict_stoll")
    return int(s, base)

"""
string double_to_string(const double input, const int precision)
{
  stringstream stream;
  stream << fixed << setprecision(precision) << input;
  return stream.str();
}
"""
def double_to_string(input: float, precision: int = 2) -> str:
    return f"{input:.{precision}f}"

"""
// cast two integral types: Source to Target, and assert no precision is lost
template<typename Target, typename Source>
Target narrow_cast(const Source & s)
{
  static_assert(std::is_integral<Source>::value, "Source: integral required");
  static_assert(std::is_integral<Target>::value, "Target: integral required");

  Target t = static_cast<Target>(s);

  if (static_cast<Source>(t) != s) {
    throw std::runtime_error("narrow_cast: " + std::to_string(s)
                             + " != " + std::to_string(t));
  }

  return t;
}
"""
def narrow_cast(target_type: Type[T], source: int) -> T:
    if not isinstance(source, int):
        raise TypeError("Source: integral required")
    target = target_type(source)
    if int(target) != source:
        raise ValueError(f"narrow_cast: {source} != {target}")
    return target