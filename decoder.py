# Note: The Datagram class and its attributes are assumed to be implemented 
# elsewhere in your Python project. The decode_frame and display_decoded_frame 
# methods contain placeholders for actual decoding and displaying logic.
import os
import sys
import time
import threading
import struct
from collections import deque
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple, Union

class Datagram:
    def __init__(self, frame_id, frame_type, frag_id, frag_cnt, payload):
        self.frame_id = frame_id
        self.frame_type = frame_type
        self.frag_id = frag_id
        self.frag_cnt = frag_cnt
        self.payload = payload

class Frame:
    def __init__(self, frame_id: int, frame_type: str, frag_cnt: int):
        if frag_cnt == 0:
            raise RuntimeError("frame cannot have zero fragments")
        self.id_ = frame_id
        self.type_ = frame_type
        self.frags_ = [None] * frag_cnt
        self.null_frags_ = frag_cnt
        self.frame_size_ = 0

    def has_frag(self, frag_id: int) -> bool:
        return self.frags_[frag_id] is not None

    def get_frag(self, frag_id: int) -> Datagram:
        return self.frags_[frag_id]

    def frame_size(self) -> Optional[int]:
        if not self.complete():
            return None
        return self.frame_size_

    def validate_datagram(self, datagram: Datagram):
        if (datagram.frame_id != self.id_ or
            datagram.frame_type != self.type_ or
            datagram.frag_id >= len(self.frags_) or
            datagram.frag_cnt != len(self.frags_)):
            raise RuntimeError("unable to insert an incompatible datagram")

    def insert_frag(self, datagram: Datagram):
        self.validate_datagram(datagram)
        if self.frags_[datagram.frag_id] is None:
            self.frame_size_ += len(datagram.payload)
            self.null_frags_ -= 1
            self.frags_[datagram.frag_id] = datagram

    def complete(self) -> bool:
        return self.null_frags_ == 0

class Decoder:
    DECODE_DISPLAY = 0
    DECODE_ONLY = 1
    NO_DECODE_DISPLAY = 2

    def __init__(self, display_width: int, display_height: int, lazy_level: int, output_path: str):
        if lazy_level < self.DECODE_DISPLAY or lazy_level > self.NO_DECODE_DISPLAY:
            raise RuntimeError(f"Invalid lazy level: {lazy_level}")
        self.display_width_ = display_width
        self.display_height_ = display_height
        self.lazy_level_ = lazy_level
        self.output_fd_ = None
        self.decoder_epoch_ = datetime.now()
        self.last_stats_time_ = self.decoder_epoch_
        self.next_frame_ = 0
        self.frame_buf_: Dict[int, Frame] = {}
        self.shared_queue_ = deque()
        self.mtx_ = threading.Lock()
        self.cv_ = threading.Condition(self.mtx_)
        self.num_decodable_frames_ = 0
        self.total_decodable_frame_size_ = 0

        if output_path:
            self.output_fd_ = open(output_path, 'w')

        if lazy_level <= self.DECODE_ONLY:
            self.worker_ = threading.Thread(target=self.worker_main)
            self.worker_.start()
            print("Spawned a new thread for decoding and displaying frames")

    def add_datagram_common(self, datagram: Datagram) -> bool:
        frame_id = datagram.frame_id
        frame_type = datagram.frame_type
        frag_cnt = datagram.frag_cnt

        if frame_id < self.next_frame_:
            return False

        if frame_id not in self.frame_buf_:
            self.frame_buf_[frame_id] = Frame(frame_id, frame_type, frag_cnt)

        return True

    def add_datagram(self, datagram: Datagram):
        if not self.add_datagram_common(datagram):
            return
        self.frame_buf_[datagram.frame_id].insert_frag(datagram)

    def add_datagram_move(self, datagram: Datagram):
        if not self.add_datagram_common(datagram):
            return
        self.frame_buf_[datagram.frame_id].insert_frag(datagram)

    def next_frame_complete(self) -> bool:
        if self.next_frame_ in self.frame_buf_ and self.frame_buf_[self.next_frame_].complete():
            return True

        for frame_id, frame in reversed(self.frame_buf_.items()):
            if frame.type_ == "KEY" and frame.complete():
                if frame_id > self.next_frame_:
                    self.advance_next_frame(frame_id - self.next_frame_)
                    print(f"* Recovery: skipped {frame_id - self.next_frame_} frames ahead to key frame {frame_id}")
                    return True
        return False

    def consume_next_frame(self):
        frame = self.frame_buf_[self.next_frame_]
        if not frame.complete():
            raise RuntimeError("next frame must be complete before consuming it")

        self.num_decodable_frames_ += 1
        frame_size = frame.frame_size()
        self.total_decodable_frame_size_ += frame_size

        stats_now = datetime.now()
        while stats_now >= self.last_stats_time_ + timedelta(seconds=1):
            print(f"Decodable frames in the last ~1s: {self.num_decodable_frames_}")
            diff_ms = (stats_now - self.last_stats_time_).total_seconds() * 1000
            if diff_ms > 0:
                print(f"  - Bitrate (kbps): {self.total_decodable_frame_size_ * 8 / diff_ms}")
            self.num_decodable_frames_ = 0
            self.total_decodable_frame_size_ = 0
            self.last_stats_time_ += timedelta(seconds=1)

        if self.lazy_level_ <= self.DECODE_ONLY:
            with self.mtx_:
                self.shared_queue_.append(frame)
            self.cv_.notify_one()
        else:
            if self.output_fd_:
                frame_decodable_ts = int(time.time() * 1e6)
                self.output_fd_.write(f"{self.next_frame_},{frame_size},{frame_decodable_ts}\n")

        self.advance_next_frame()

    def advance_next_frame(self, n: int = 1):
        self.next_frame_ += n
        self.clean_up_to(self.next_frame_)

    def clean_up_to(self, frontier: int):
        self.frame_buf_ = {k: v for k, v in self.frame_buf_.items() if k >= frontier}

    def decode_frame(self, context, frame: Frame) -> float:
        if not frame.complete():
            raise RuntimeError("frame must be complete before decoding")

        MAX_DECODING_BUF = 1000000
        decode_buf = bytearray(MAX_DECODING_BUF)
        buf_ptr = 0

        for datagram in frame.frags_:
            payload = datagram.payload
            if buf_ptr + len(payload) >= MAX_DECODING_BUF:
                raise RuntimeError("frame size exceeds max decoding buffer size")
            decode_buf[buf_ptr:buf_ptr+len(payload)] = payload
            buf_ptr += len(payload)

        frame_size = buf_ptr
        decode_start = datetime.now()
        # Simulate decoding process
        time.sleep(0.01)  # Replace with actual decoding call
        decode_end = datetime.now()

        return (decode_end - decode_start).total_seconds() * 1000

    def display_decoded_frame(self, context, display):
        # Simulate displaying process
        print("Displaying frame")

    def set_verbose(self, verbose):
        self.verbose = verbose

    def worker_main(self):
        if self.lazy_level_ == self.NO_DECODE_DISPLAY:
            return

        max_threads = min(os.cpu_count(), 4)
        context = {}  # Placeholder for actual decoding context

        print(f"[worker] Initialized decoder (max threads: {max_threads})")

        display = None
        if self.lazy_level_ == self.DECODE_DISPLAY:
            display = "VideoDisplay"  # Placeholder for actual display object

        local_queue = deque()
        num_decoded_frames = 0
        total_decode_time_ms = 0.0
        max_decode_time_ms = 0.0
        last_stats_time = self.decoder_epoch_

        while True:
            if display and display == "quit":
                display = None

            with self.cv_:
                self.cv_.wait_for(lambda: len(self.shared_queue_) > 0)
                while self.shared_queue_:
                    local_queue.append(self.shared_queue_.popleft())

            while local_queue:
                frame = local_queue.popleft()
                decode_time_ms = self.decode_frame(context, frame)

                if self.output_fd_:
                    frame_decoded_ts = int(time.time() * 1e6)
                    self.output_fd_.write(f"{frame.id_},{frame.frame_size()},{frame_decoded_ts}\n")

                if display:
                    self.display_decoded_frame(context, display)

                num_decoded_frames += 1
                total_decode_time_ms += decode_time_ms
                max_decode_time_ms = max(max_decode_time_ms, decode_time_ms)

                stats_now = datetime.now()
                while stats_now >= last_stats_time + timedelta(seconds=1):
                    if num_decoded_frames > 0:
                        print(f"[worker] Avg/Max decoding time (ms) of {num_decoded_frames} frames: "
                              f"{total_decode_time_ms / num_decoded_frames}/{max_decode_time_ms}")
                    num_decoded_frames = 0
                    total_decode_time_ms = 0.0
                    max_decode_time_ms = 0.0
                    last_stats_time += timedelta(seconds=1)

        # Simulate destroying context
        print("Destroying context")

# Example usage
if __name__ == "__main__":
    decoder = Decoder(1920, 1080, Decoder.DECODE_DISPLAY, "output.txt")
    datagram = Datagram(1, "KEY", 0, 1, b"payload")
    decoder.add_datagram(datagram)
    if decoder.next_frame_complete():
        decoder.consume_next_frame()