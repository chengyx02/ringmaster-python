import os
from utils.poller import Poller

# Example usage
if __name__ == "__main__":
    def example_callback():
        print("Event triggered")

    poller = Poller()
    fd = os.open("example.txt", os.O_RDWR | os.O_CREAT)
    poller.register_event(fd, Poller.Flag.In, example_callback)
    poller.activate(fd, Poller.Flag.In)
    poller.poll(1000)
    os.close(fd)