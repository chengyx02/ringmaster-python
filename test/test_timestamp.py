from utils.timestamp import timestamp_ns, timestamp_us, timestamp_ms

# Example usage
if __name__ == "__main__":
    print(f"Timestamp in nanoseconds: {timestamp_ns()}")
    print(f"Timestamp in microseconds: {timestamp_us()}")
    print(f"Timestamp in milliseconds: {timestamp_ms()}")