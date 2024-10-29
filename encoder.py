import os
import time
import struct
import threading
from collections import deque
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple, Union

class Encoder:
    def __init__(self, display_width: int, display_height: int, frame_rate: int, output_path: str):
        self.display_width_ = display_width
        self.display_height_ = display_height
        self.frame_rate_ = frame_rate
        self.output_fd_ = None
        self.frame_id_ = 0
        self.target_bitrate_ = 1000  # Default bitrate, can be changed later
        self.send_buf_ = deque()
        self.unacked_ = {}
        self.num_encoded_frames_ = 0
        self.total_encode_time_ms_ = 0.0
        self.max_encode_time_ms_ = 0.0
        self.min_rtt_us_ = None
        self.ewma_rtt_us_ = None
        self.verbose_ = False

        if output_path:
            self.output_fd_ = open(output_path, 'w')

        # Initialize VP9 encoder configuration
        self.cfg_ = self.default_vp9_config()
        self.context_ = self.init_vp9_encoder(self.cfg_)

        print(f"Initialized VP9 encoder (CPU used: {self.cfg_['cpu_used']})")

    def __del__(self):
        self.destroy_vp9_encoder(self.context_)

    def default_vp9_config(self):
        cfg = {
            'g_w': self.display_width_,
            'g_h': self.display_height_,
            'g_timebase': (1, self.frame_rate_),
            'g_pass': 'VPX_RC_ONE_PASS',
            'g_lag_in_frames': 0,
            'g_error_resilient': 'VPX_ERROR_RESILIENT_DEFAULT',
            'g_threads': 4,
            'rc_resize_allowed': 0,
            'rc_dropframe_thresh': 0,
            'rc_buf_initial_sz': 500,
            'rc_buf_optimal_sz': 600,
            'rc_buf_sz': 1000,
            'rc_min_quantizer': 2,
            'rc_max_quantizer': 52,
            'rc_undershoot_pct': 50,
            'rc_overshoot_pct': 50,
            'kf_mode': 'VPX_KF_DISABLED',
            'kf_max_dist': float('inf'),
            'kf_min_dist': 0,
            'rc_end_usage': 'VPX_CBR',
            'rc_target_bitrate': self.target_bitrate_,
            'cpu_used': min(os.cpu_count(), 16)
        }
        return cfg

    def init_vp9_encoder(self, cfg):
        # Placeholder for actual VP9 encoder initialization
        context = {}
        return context

    def destroy_vp9_encoder(self, context):
        # Placeholder for actual VP9 encoder destruction
        pass

    def compress_frame(self, raw_img):
        frame_generation_ts = time.time()

        self.encode_frame(raw_img)
        frame_size = self.packetize_encoded_frame()

        if self.output_fd_:
            frame_encoded_ts = time.time()
            self.output_fd_.write(f"{self.frame_id_},{self.target_bitrate_},{frame_size},{frame_generation_ts},{frame_encoded_ts}\n")

        self.frame_id_ += 1

    def encode_frame(self, raw_img):
        if raw_img.display_width != self.display_width_ or raw_img.display_height != self.display_height_:
            raise RuntimeError("Encoder: image dimensions don't match")

        encode_flags = 0
        if self.unacked_:
            first_unacked = next(iter(self.unacked_.values()))
            us_since_first_send = time.time() - first_unacked['send_ts']

            if us_since_first_send > 1:  # MAX_UNACKED_US placeholder
                encode_flags = 1  # VPX_EFLAG_FORCE_KF placeholder
                print(f"* Recovery: gave up retransmissions and forced a key frame {self.frame_id_}")

                if self.verbose_:
                    print(f"Giving up on lost datagram: frame_id={first_unacked['frame_id']} frag_id={first_unacked['frag_id']} rtx={first_unacked['num_rtx']} us_since_first_send={us_since_first_send}")

                self.send_buf_.clear()
                self.unacked_.clear()

        encode_start = time.time()
        # Placeholder for actual VP9 encoding call
        encode_end = time.time()
        encode_time_ms = (encode_end - encode_start) * 1000

        self.num_encoded_frames_ += 1
        self.total_encode_time_ms_ += encode_time_ms
        self.max_encode_time_ms_ = max(self.max_encode_time_ms_, encode_time_ms)

    def packetize_encoded_frame(self):
        # Placeholder for actual packetization logic
        frame_size = 1000  # Example frame size
        return frame_size

    def add_unacked(self, datagram):
        seq_num = (datagram['frame_id'], datagram['frag_id'])
        if seq_num in self.unacked_:
            raise RuntimeError("datagram already exists in unacked")
        self.unacked_[seq_num] = datagram
        self.unacked_[seq_num]['last_send_ts'] = self.unacked_[seq_num]['send_ts']

    def handle_ack(self, ack):
        curr_ts = time.time()
        self.add_rtt_sample(curr_ts - ack['send_ts'])

        acked_seq_num = (ack['frame_id'], ack['frag_id'])
        if acked_seq_num not in self.unacked_:
            return

        for seq_num, datagram in reversed(list(self.unacked_.items())):
            if datagram['num_rtx'] >= 5:  # MAX_NUM_RTX placeholder
                continue

            if datagram['num_rtx'] == 0 or curr_ts - datagram['last_send_ts'] > self.ewma_rtt_us_:
                datagram['num_rtx'] += 1
                datagram['last_send_ts'] = curr_ts
                self.send_buf_.appendleft(datagram)

        del self.unacked_[acked_seq_num]

    def add_rtt_sample(self, rtt_us):
        if self.min_rtt_us_ is None or rtt_us < self.min_rtt_us_:
            self.min_rtt_us_ = rtt_us

        if self.ewma_rtt_us_ is None:
            self.ewma_rtt_us_ = rtt_us
        else:
            alpha = 0.125  # ALPHA placeholder
            self.ewma_rtt_us_ = alpha * rtt_us + (1 - alpha) * self.ewma_rtt_us_

    def output_periodic_stats(self):
        print(f"Frames encoded in the last ~1s: {self.num_encoded_frames_}")

        if self.num_encoded_frames_ > 0:
            avg_encode_time = self.total_encode_time_ms_ / self.num_encoded_frames_
            print(f"  - Avg/Max encoding time (ms): {avg_encode_time}/{self.max_encode_time_ms_}")

        if self.min_rtt_us_ and self.ewma_rtt_us_:
            print(f"  - Min/EWMA RTT (ms): {self.min_rtt_us_ / 1000.0}/{self.ewma_rtt_us_ / 1000.0}")

        self.num_encoded_frames_ = 0
        self.total_encode_time_ms_ = 0.0
        self.max_encode_time_ms_ = 0.0

    def set_target_bitrate(self, bitrate_kbps):
        self.target_bitrate_ = bitrate_kbps
        self.cfg_['rc_target_bitrate'] = bitrate_kbps
        # Placeholder for actual VP9 configuration update call