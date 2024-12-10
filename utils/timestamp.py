import time

"""
uint64_t timestamp_ns()
{
  return system_clock::now().time_since_epoch() / 1ns;
}
"""
def timestamp_ns() -> int:
    return int(time.time() * 1e9)

"""
uint64_t timestamp_us()
{
  return system_clock::now().time_since_epoch() / 1us;
}
"""
def timestamp_us() -> int:
    return int(time.time() * 1e6)

"""
uint64_t timestamp_ms()
{
  return system_clock::now().time_since_epoch() / 1ms;
}
"""
def timestamp_ms() -> int:
    return int(time.time() * 1e3)