import re
from typing import TypeVar, Type

T = TypeVar('T', int, int)

def strict_stoi(s: str, base: int = 10) -> int:
    match = re.fullmatch(r'[+-]?[0-9a-fA-F]+', s)
    if not match:
        raise ValueError("strict_stoi")
    return int(s, base)

def strict_stoll(s: str, base: int = 10) -> int:
    match = re.fullmatch(r'[+-]?[0-9a-fA-F]+', s)
    if not match:
        raise ValueError("strict_stoll")
    return int(s, base)

def double_to_string(input: float, precision: int = 2) -> str:
    return f"{input:.{precision}f}"

def narrow_cast(target_type: Type[T], source: int) -> T:
    if not isinstance(source, int):
        raise TypeError("Source: integral required")
    target = target_type(source)
    if int(target) != source:
        raise ValueError(f"narrow_cast: {source} != {target}")
    return target