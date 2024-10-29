import time
from utils.timerfd import Timerfd, timespec

# Example usage
try:
    timer = Timerfd()
    initial_expiration = timespec(tv_sec=1, tv_nsec=0)
    interval = timespec(tv_sec=1, tv_nsec=0)
    timer.set_time(initial_expiration, interval)
    time.sleep(2)
    expirations = timer.read_expirations()
    print(f"Timer expired {expirations} times")
    timer.close()
except Exception as e:
    print(f"Error: {e}")