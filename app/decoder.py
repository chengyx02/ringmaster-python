import os
import time
import threading
from typing import Optional, Dict, Deque
from collections import deque
import multiprocessing
from enum import Enum
from ctypes import create_string_buffer

from utils.conversion import double_to_string
from utils.exception_rim import check_call, check_syscall
from utils.timestamp import timestamp_us
from utils.file_descriptor import FileDescriptor
from utils.vpx_wrap import *
from video.sdl import VideoDisplay
from video.image import RawImage
from protocol import FrameType, Datagram


class Frame:
    def __init__(self, frame_id: int, frame_type: FrameType, frag_cnt: int):
        if frag_cnt == 0:
            raise RuntimeError("frame cannot have zero fragments")
            
        self.id_ = frame_id
        self.type_ = frame_type
        self.frags_ = [None] * frag_cnt  # List of Optional[Datagram]
        self.null_frags_ = frag_cnt
        self.frame_size_ = 0

    def has_frag(self, frag_id: int) -> bool:
        return self.frags_[frag_id] is not None

    def get_frag(self, frag_id: int) -> Datagram:
        return self.frags_[frag_id]

    def validate_datagram(self, datagram: Datagram) -> None:
        if (datagram.frame_id != self.id_ or
            datagram.frame_type != self.type_ or
            datagram.frag_id >= len(self.frags_) or
            datagram.frag_cnt != len(self.frags_)):
            raise RuntimeError("unable to insert an incompatible datagram")

    def insert_frag(self, datagram: Datagram) -> None:
        self.validate_datagram(datagram)
        
        if self.frags_[datagram.frag_id] is None:
            self.frame_size_ += len(datagram.payload)
            self.null_frags_ -= 1
            self.frags_[datagram.frag_id] = datagram

    def complete(self) -> bool:
        return self.null_frags_ == 0

    def frame_size(self) -> Optional[int]:
        if not self.complete():
            return None
        return self.frame_size_

    def id(self) -> int:
        return self.id_

    def type(self) -> FrameType:
        return self.type_

class Decoder:
    class LazyLevel(Enum):
        DECODE_DISPLAY = 0    # decode and display
        DECODE_ONLY = 1       # decode only but not display  
        NO_DECODE_DISPLAY = 2 # neither decode nor display

    def __init__(self, display_width: int, display_height: int, 
                 lazy_level: int = 0, output_path: str = ""):
        # Add exit flag for worker
        self.should_exit = False

        self.display_width_ = display_width
        self.display_height_ = display_height
        
        if lazy_level < 0 or lazy_level > 2:
            raise RuntimeError(f"Invalid lazy level: {lazy_level}")
        self.lazy_level_ = self.LazyLevel(lazy_level)

        self.output_fd = None
        if output_path:
            self.output_fd = FileDescriptor(check_syscall(os.open(output_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)))

        self.verbose_ = False
        self.next_frame_ = 0
        self.frame_buf_: Dict[int, Frame] = {}
        
        self.num_decodable_frames_ = 0
        self.total_decodable_frame_size_ = 0
        
        self.decoder_epoch_ = time.monotonic()
        self.last_stats_time_ = self.decoder_epoch_

        # Thread synchronization
        self.mtx_ = threading.Lock()
        self.cv_ = threading.Condition(self.mtx_)
        self.shared_queue_: Deque[Frame] = deque()
        
        self.worker_ = None
        if lazy_level <= self.LazyLevel.DECODE_ONLY.value:
            self.worker_ = threading.Thread(target=self.worker_main)
            self.worker_.start()
            print("Spawned a new thread for decoding and displaying frames")

    def add_datagram_common(self, datagram: Datagram) -> bool:
        frame_id = datagram.frame_id
        
        if frame_id < self.next_frame_:
            return False
            
        if frame_id not in self.frame_buf_:
            self.frame_buf_[frame_id] = Frame(
                frame_id, datagram.frame_type, datagram.frag_cnt)
            
        return True

    def add_datagram(self, datagram: Datagram) -> None:
        if not self.add_datagram_common(datagram):
            return
            
        self.frame_buf_[datagram.frame_id].insert_frag(datagram)

    def next_frame_complete(self) -> bool:
        if self.next_frame_ in self.frame_buf_:
            if self.frame_buf_[self.next_frame_].complete():
                return True
                
        # Look for complete key frame ahead
        for frame_id in sorted(self.frame_buf_.keys(), reverse=True):
            frame = self.frame_buf_[frame_id]
            if (frame.type() == FrameType.KEY and 
                frame.complete() and 
                frame_id > self.next_frame_):
                
                frame_diff = frame_id - self.next_frame_
                self.advance_next_frame(frame_diff)
                print(f"* Recovery: skipped {frame_diff} frames ahead to key frame {frame_id}")
                return True
                
        return False

    def consume_next_frame(self) -> None:
        frame = self.frame_buf_[self.next_frame_]
        if not frame.complete():
            raise RuntimeError("next frame must be complete before consuming it")

        # Update stats
        self.num_decodable_frames_ += 1
        frame_size = frame.frame_size()
        self.total_decodable_frame_size_ += frame_size

        stats_now = time.monotonic()
        while stats_now >= self.last_stats_time_ + 1:
            print(f"Decodable frames in the last ~1s: {self.num_decodable_frames_}")
            
            diff_ms = (stats_now - self.last_stats_time_) * 1000
            if diff_ms > 0:
                bitrate = self.total_decodable_frame_size_ * 8 / diff_ms
                print(f"  - Bitrate (kbps): {double_to_string(bitrate)}")

            # Reset stats
            self.num_decodable_frames_ = 0
            self.total_decodable_frame_size_ = 0
            self.last_stats_time_ += 1

        if self.lazy_level_.value <= self.LazyLevel.DECODE_ONLY.value:
            with self.mtx_:
                self.shared_queue_.append(frame)
                self.cv_.notify()  # Changed from notify_one()
        else:
            if self.output_fd:
                frame_decodable_ts = timestamp_us()
                self.output_fd.write(
                    f"{self.next_frame_},{frame_size},{frame_decodable_ts}\n")

        self.advance_next_frame()

    def advance_next_frame(self, n: int = 1) -> None:
        self.next_frame_ += n
        self.clean_up_to(self.next_frame_)

    def clean_up_to(self, frontier: int) -> None:
        to_remove = []
        for frame_id in self.frame_buf_:
            if frame_id < frontier:
                to_remove.append(frame_id)
        
        for frame_id in to_remove:
            del self.frame_buf_[frame_id]

    # Add constants
    MAX_DECODING_BUF = 1000000  # 1 MB

    def decode_frame(self, context: 'vpx_codec_ctx_t', frame: 'Frame') -> float:
        if not frame.complete():
            raise RuntimeError("frame must be complete before decoding")

        # Allocate static buffer if needed
        if not hasattr(self, '_decode_buf'):
            # self._decode_buf = bytearray(self.MAX_DECODING_BUF)
            self._decode_buf = create_string_buffer(self.MAX_DECODING_BUF)

        # Copy payload data to buffer
        buf_ptr = 0
        for datagram in frame.frags_:
            if datagram:
                payload_size = len(datagram.payload)
                if buf_ptr + payload_size >= self.MAX_DECODING_BUF:
                    raise RuntimeError("frame size exceeds max decoding buffer size")
                
                # Copy payload to buffer
                # self._decode_buf[buf_ptr:buf_ptr + payload_size] = datagram.payload
                memmove(byref(self._decode_buf, buf_ptr), 
                          datagram.payload, 
                          payload_size)
                buf_ptr += payload_size

        frame_size = buf_ptr

        # decode the compressed frame in 'decode_buf'
        decode_start = time.monotonic()
        check_call(vpx_codec_decode(
                byref(context),
                cast(self._decode_buf, POINTER(c_ubyte)),
                frame_size,
                None,
                1
            ),
            0, "failed to decode a frame"
        )
        decode_end = time.monotonic()
        
        return (decode_end - decode_start) * 1000  # Convert to milliseconds

    def display_decoded_frame(self, context: 'vpx_codec_ctx_t', 
                            display: 'VideoDisplay') -> None:
        iter_ptr = c_void_p(None)
        frame_decoded = 0
        
        # display the decoded frame stored in 'context_'
        while True:
            raw_img = vpx_codec_get_frame(byref(context), byref(iter_ptr))
            if not raw_img:
                break
                
            frame_decoded += 1

            # there should be exactly one frame decoded
            if frame_decoded > 1:
                raise RuntimeError("Multiple frames were decoded at once")
            
            # construct a temporary RawImage that does not own the raw_img
            img = RawImage(
                display_width = self.display_width_,
                display_height = self.display_height_,
                vpx_img = raw_img)
            display.show_frame(img)

    def worker_main(self) -> None:
        if self.lazy_level_ == self.LazyLevel.NO_DECODE_DISPLAY:
            return

        # initialize a VP9 decoding context
        max_threads = min(multiprocessing.cpu_count(), 4)
        cfg = vpx_codec_dec_cfg(
            threads=max_threads,
            w=self.display_width_,
            h=self.display_height_
        )

        context = vpx_codec_ctx_t()
        check_call(vpx_codec_dec_init_ver(
            byref(context),
            byref(vpx_codec_vp9_dx_algo),
            byref(cfg),
            0,
            VPX_DECODER_ABI_VERSION
        ), 0, "vpx_codec_dec_init")

        print(f"[worker] Initialized decoder (max threads: {max_threads})")

        # video display
        display = None
        if self.lazy_level_ == self.LazyLevel.DECODE_DISPLAY:
            display = VideoDisplay(self.display_width_, self.display_height_)

        # local queue of frames
        local_queue: Deque[Frame] = deque()
        
        # stats maintained by the worker thread
        num_decoded_frames = 0
        total_decode_time_ms = 0.0
        max_decode_time_ms = 0.0
        last_stats_time = self.decoder_epoch_

        while True:
            # destroy display if it has been signalled to quit
            if display and display.signal_quit():
                display = None

            # worker releases the lock so it doesn't block the main thread anymore
            with self.cv_:
                # wait until the shared queue is not empty
                self.cv_.wait_for(lambda: len(self.shared_queue_) > 0 or self.should_exit)
                if self.should_exit:
                    break

                # worker owns the lock after wait and should copy shared queue quickly
                while self.shared_queue_:
                    local_queue.append(self.shared_queue_.popleft())

            # now worker can take its time to decode and render the frames kept locally
            while local_queue:
                frame = local_queue.popleft()
                decode_time_ms = self.decode_frame(context, frame)

                if self.output_fd:
                    frame_decoded_ts = timestamp_us()
                    self.output_fd.write(
                        f"{frame.id()},{frame.frame_size()},{frame_decoded_ts}\n"
                    )

                if display:
                    self.display_decoded_frame(context, display)

                # update stats
                num_decoded_frames += 1
                total_decode_time_ms += decode_time_ms
                max_decode_time_ms = max(max_decode_time_ms, decode_time_ms)

                # worker thread also outputs stats roughly every second
                stats_now = time.monotonic()
                while stats_now >= last_stats_time + 1:
                    if num_decoded_frames > 0:
                        print(f"[worker] Avg/Max decoding time (ms) of "
                              f"{num_decoded_frames} frames: "
                              f"{double_to_string(total_decode_time_ms / num_decoded_frames)}/"
                              f"{double_to_string(max_decode_time_ms)}")

                    # reset stats
                    num_decoded_frames = 0
                    total_decode_time_ms = 0.0
                    max_decode_time_ms = 0.0
                    last_stats_time += 1

        check_call(vpx_codec_destroy(byref(context)), 0, "vpx_codec_destroy")

    # Add cleanup method
    def __del__(self):
        if hasattr(self, 'worker_') and self.worker_ and self.worker_.is_alive():
            with self.mtx_:
                self.should_exit = True
                self.cv_.notify()
            self.worker_.join(timeout=1.0)
        
        if hasattr(self, 'output_fd') and self.output_fd:
            self.output_fd.close()

    def set_verbose(self, verbose: bool) -> None:
        self.verbose_ = verbose