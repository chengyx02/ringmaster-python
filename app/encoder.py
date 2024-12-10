import os
import time
from ctypes import c_void_p, byref, cast
from typing import Optional, Deque, Dict, Tuple
from collections import deque

from utils.file_descriptor import FileDescriptor
from utils.exception_rim import check_syscall, check_call
from utils.timestamp import timestamp_us
from utils.conversion import narrow_cast
from utils.vpx_wrap import *
from video.image import RawImage
from protocol import Datagram, AckMsg, FrameType


class Encoder:
    ALPHA = 0.2
    MAX_NUM_RTX = 3
    MAX_UNACKED_US = 1000 * 1000  # 1s

    def __init__(self, display_width, display_height, frame_rate, output_path=""):
        self.display_width_ = display_width
        self.display_height_ = display_height
        self.frame_rate_ = frame_rate
        self.output_path = output_path
        self.output_fd: Optional[FileDescriptor] = None
        # print debugging info
        self.verbose_ = False
        # current target bitrate
        self.target_bitrate_ = 0
        # VPX encoding configuration and context
        self.context_ = vpx_codec_ctx()
        self.cfg_ = vpx_codec_enc_cfg()
        # frame ID to encode
        self.frame_id_ = 0
        # queue of datagrams (packetized video frames) to send
        self.send_buf: Deque = deque()
        # unacked datagrams
        self.unacked: Dict[Tuple[int, int], Datagram] = {}
        # RTT-related
        self.min_rtt_us: Optional[int] = None
        self.ewma_rtt_us: Optional[float] = None
        # performance stats
        self.num_encoded_frames = 0
        self.total_encode_time_ms = 0.0
        self.max_encode_time_ms = 0.0

        # open the output file
        if output_path:
            self.output_fd = FileDescriptor(check_syscall(os.open(output_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)))

        # populate VP9 configuration with default values
        check_call(vpx_codec_enc_config_default(
                    byref(vpx_codec_vp9_cx_algo), 
                    byref(self.cfg_), 
                    0
                ),
                VPX_CODEC_OK, "vpx_codec_enc_config_default") 

        # copy the configuration below mostly from WebRTC (libvpx_vp9_encoder.cc)
        self.cfg_.g_w = self.display_width_
        self.cfg_.g_h = self.display_height_
        self.cfg_.g_timebase_num = 1
        self.cfg_.g_timebase_den = self.frame_rate_  # WebRTC uses a 90 kHz clock
        self.cfg_.g_pass = VPX_RC_ONE_PASS
        self.cfg_.g_lag_in_frames = 0        # disable lagged encoding

        # WebRTC disables error resilient mode unless for SVC
        self.cfg_.g_error_resilient = VPX_ERROR_RESILIENT_DEFAULT
        self.cfg_.g_threads = 4              # encoder threads; should equal to column tiles below
        self.cfg_.rc_resize_allowed = 0      # WebRTC enables spatial sampling
        self.cfg_.rc_dropframe_thresh = 0    # WebRTC sets to 30 (% of target data buffer)
        self.cfg_.rc_buf_initial_sz = 500
        self.cfg_.rc_buf_optimal_sz = 600
        self.cfg_.rc_buf_sz = 1000
        self.cfg_.rc_min_quantizer = 2
        self.cfg_.rc_max_quantizer = 52
        self.cfg_.rc_undershoot_pct = 50
        self.cfg_.rc_overshoot_pct = 50

        # prevent libvpx encoder from automatically placing key frames
        self.cfg_.kf_mode = VPX_KF_DISABLED
        # WebRTC sets the two values below to 3000 frames (fixed keyframe interval)
        self.cfg_.kf_max_dist = c_uint32(-1).value
        self.cfg_.kf_min_dist = 0

        self.cfg_.rc_end_usage = VPX_CBR
        self.cfg_.rc_target_bitrate = self.target_bitrate_

        # use no more than 16 or the number of avaialble CPUs
        cpu_used = min(os.cpu_count(), 16)

        # more encoder settings
        check_call(vpx_codec_enc_init(
            byref(self.context_), 
            byref(vpx_codec_vp9_cx_algo), 
            byref(self.cfg_), 
            0,
            ),
            VPX_CODEC_OK, "vpx_codec_enc_init") 

        # this value affects motion estimation and *dominates* the encoding speed        
        self.codec_control(byref(self.context_), VP8E_SET_CPUUSED, cpu_used)
        
        # enable encoder to skip static/low content blocks
        self.codec_control(byref(self.context_), VP8E_SET_STATIC_THRESHOLD, 1)
        
        # clamp the max bitrate of a keyframe to 900% of average per-frame bitrate
        self.codec_control(byref(self.context_), VP8E_SET_MAX_INTRA_BITRATE_PCT, 900)
        
        # enable encoder to adaptively change QP for each segment within a frame
        self.codec_control(byref(self.context_), VP9E_SET_AQ_MODE, 3)
        
        # set the number of column tiles in encoding a frame to 2 ** 2 = 4
        self.codec_control(byref(self.context_), VP9E_SET_TILE_COLUMNS, 2)
        
        # enable row-based multi-threading
        self.codec_control(byref(self.context_), VP9E_SET_ROW_MT, 1)
        
        # disable frame parallel decoding
        self.codec_control(byref(self.context_), VP9E_SET_FRAME_PARALLEL_DECODING, 0)
        
        # enable denoiser (but not on ARM since optimization is pending)
        self.codec_control(byref(self.context_), VP9E_SET_NOISE_SENSITIVITY, 1)

        print(f"Initialized VP9 encoder (CPU used: {cpu_used})")

    def __del__(self):
        if vpx_codec_destroy(byref(self.context_)) != VPX_CODEC_OK:
            print("~Encoder(): failed to destroy VPX encoder context")

    def compress_frame(self, raw_img: RawImage):
        frame_generation_ts = timestamp_us()

        # encode raw_img into frame 'frame_id_'
        self.encode_frame(raw_img)

        # packetize frame 'frame_id_' into datagrams
        frame_size = self.packetize_encoded_frame()

        # output frame information
        if self.output_fd:
            frame_encoded_ts = timestamp_us()

            self.output_fd.write(f"{self.frame_id_},{self.target_bitrate_},{frame_size},\
                                 {frame_generation_ts},{frame_encoded_ts}\n")

        # move onto the next frame
        self.frame_id_ += 1

    def encode_frame(self, raw_img: RawImage):
        if raw_img.display_width() != self.display_width_ or \
            raw_img.display_height() != self.display_height_:
            raise RuntimeError("Encoder: image dimensions don't match")

        # check if a key frame needs to be encoded
        encode_flags = 0    # normal frame

        if self.unacked:
            first_unacked = next(iter(self.unacked.values()))

            # give up if first unacked datagram was initially sent MAX_UNACKED_US ago
            us_since_first_send = timestamp_us() - first_unacked.send_ts

            if us_since_first_send > self.MAX_UNACKED_US:
                VPX_EFLAG_FORCE_KF = 1 << 0 
                encode_flags = VPX_EFLAG_FORCE_KF #  force next frame to be key frame

                print(f"* Recovery: gave up retransmissions and forced a key frame {self.frame_id_}")

                if self.verbose_:
                    print(f"Giving up on lost datagram: frame_id={first_unacked.frame_id} "
                        f"frag_id={first_unacked.frag_id} rtx={first_unacked.num_rtx} "
                        f"us_since_first_send={us_since_first_send}")

                # clean up
                self.send_buf.clear()
                self.unacked.clear()

        # encode a frame and calculate encoding time
        encode_start = time.time()
        check_call(vpx_codec_encode(
                    byref(self.context_), 
                    raw_img.get_vpx_image(), 
                    self.frame_id_, 
                    1, 
                    encode_flags, 
                    VPX_DL_REALTIME
                ),
                VPX_CODEC_OK, "failed to encode a frame")  # 
        
        encode_end = time.time()
        encode_time_ms = (encode_end - encode_start) * 1000

        # track stats in the current period
        self.num_encoded_frames += 1
        self.total_encode_time_ms += encode_time_ms
        self.max_encode_time_ms = max(self.max_encode_time_ms, encode_time_ms)

    def packetize_encoded_frame(self):
        # read the encoded frame's "encoder packets" from 'context_'
        iter = c_void_p()
        frames_encoded = 0
        frame_size = 0

        while True:
            encoder_pkt = vpx_codec_get_cx_data(byref(self.context_), byref(iter))
            if not encoder_pkt:
                break
                
            if encoder_pkt.contents.kind == 0: # VPX_CODEC_CX_FRAME_PKT:  
                frames_encoded += 1

                # there should be exactly one frame encoded
                if frames_encoded > 1:
                    raise RuntimeError("Multiple frames were encoded at once")
                    
                frame_size = encoder_pkt.contents.data.frame.sz
                assert frame_size > 0

                # read the returned frame type
                frame_type = FrameType.NONKEY
                if (encoder_pkt.contents.data.frame.flags & VPX_FRAME_IS_KEY):
                    frame_type = FrameType.KEY
                
                    if self.verbose_:
                        print(f"Encoded a {frame_type} frame: frame_id={self.frame_id_}")

                # total fragments to divide this frame into
                frag_cnt = narrow_cast(int, (frame_size // (Datagram.max_payload + 1)) + 1)
                
                # next address to copy compressed frame data from
                buf_ptr = cast(
                    encoder_pkt.contents.data.frame.buf,
                    POINTER(c_uint8 * frame_size)
                )
                
                # Create a memoryview for efficient slicing
                buffer = memoryview(buf_ptr.contents)
                
                # Split into fragments
                for frag_id in range(frag_cnt):
                    # calculate payload size and construct the payload
                    start = frag_id * Datagram.max_payload
                    end = min(start + Datagram.max_payload, frame_size)
                    payload = bytes(buffer[start:end])
                    
                    # enqueue a datagram
                    dgram = Datagram(
                        frame_id=self.frame_id_,
                        frame_type=frame_type,
                        frag_id=frag_id,
                        frag_cnt=frag_cnt,
                        payload=payload
                    )
                    self.send_buf.append(dgram)

        return frame_size
    

    def add_unacked(self, datagram: Datagram):
        seq_num = (datagram.frame_id, datagram.frag_id)
        if seq_num in self.unacked:
            raise RuntimeError("datagram already exists in unacked")

        self.unacked[seq_num] = datagram
        self.unacked[seq_num].last_send_ts = datagram.send_ts

    
    def handle_ack(self, ack: 'AckMsg'):
        curr_ts = timestamp_us()

        # observed an RTT sample
        self.add_rtt_sample(curr_ts - ack.send_ts)

        # find the acked datagram in 'unacked'
        acked_seq_num = (ack.frame_id, ack.frag_id)
        acked_it = self.unacked.get(acked_seq_num)

        if acked_it is None:
            # do nothing else if ACK is not for an unacked datagram
            return

        # retransmit all unacked datagrams before the acked one (backward)
        for seq_num, datagram in reversed(list(self.unacked.items())):
            if seq_num == acked_seq_num:
                break

            # skip if a datagram has been retransmitted MAX_NUM_RTX times
            if datagram.num_rtx >= self.MAX_NUM_RTX:
                continue

            # retransmit if it's the first RTX or the last RTX was about one RTT ago
            if datagram.num_rtx == 0 or curr_ts - datagram.last_send_ts > self.ewma_rtt_us:
                datagram.num_rtx += 1
                datagram.last_send_ts = curr_ts

                # retransmissions are more urgent
                self.send_buf.appendleft(datagram)

        # finally, erase the acked datagram from 'unacked'
        del self.unacked[acked_seq_num]

    
    def add_rtt_sample(self, rtt_us: int):
        # min RTT
        if self.min_rtt_us is None or rtt_us < self.min_rtt_us:
            self.min_rtt_us = rtt_us

        # EWMA RTT
        if self.ewma_rtt_us is None:
            self.ewma_rtt_us = rtt_us
        else:
            self.ewma_rtt_us = self.ALPHA * rtt_us + (1 - self.ALPHA) * self.ewma_rtt_us


    def output_periodic_stats(self):
        print(f"Frames encoded in the last ~1s: {self.num_encoded_frames}")

        if self.num_encoded_frames > 0:
            avg_encode_time = self.total_encode_time_ms / self.num_encoded_frames
            print(f" - Avg/Max encoding time (ms): {avg_encode_time:.2f}/{self.max_encode_time_ms:.2f}")
        
        if self.min_rtt_us and self.ewma_rtt_us:
            print(f" - Min/EWMA RTT (ms): {(self.min_rtt_us / 1000.0):.2f}/{(self.ewma_rtt_us / 1000.0):.2f}")

        # reset all but RTT-related stats
        self.num_encoded_frames = 0
        self.total_encode_time_ms = 0.0
        self.max_encode_time_ms = 0.0


    def set_target_bitrate(self, bitrate_kbps: int):
        self.target_bitrate_ = bitrate_kbps
        
        self.cfg_.rc_target_bitrate = bitrate_kbps
        check_call(vpx_codec_enc_config_set(
                        byref(self.context_), 
                        byref(self.cfg_)),
                   VPX_CODEC_OK, "set_target_bitrate") 
        

    def set_verbose(self, verbose: bool) -> None:
        """Set verbose flag for decoder."""
        self.verbose_ = verbose


    def codec_control(self, *args):
        """Control codec settings with variable arguments.
    
        Args:
            *args: Variable number of arguments to forward to vpx_codec_control_
        """
        check_call(vpx_codec_control_(*args), VPX_CODEC_OK, "vpx_codec_control_")
