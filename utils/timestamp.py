import time

def timestamp_ns() -> int:
    return int(time.time() * 1e9)

def timestamp_us() -> int:
    return int(time.time() * 1e6)

def timestamp_ms() -> int:
    return int(time.time() * 1e3)

# Example usage
if __name__ == "__main__":
    print(f"Timestamp in nanoseconds: {timestamp_ns()}")
    print(f"Timestamp in microseconds: {timestamp_us()}")
    print(f"Timestamp in milliseconds: {timestamp_ms()}")