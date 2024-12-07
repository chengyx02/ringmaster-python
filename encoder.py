import ctypes
import os
import time
from ctypes import Union, c_char, c_double, c_int64, c_uint, c_int, c_uint32, c_size_t, c_char_p, c_uint64, c_uint8, c_ulong, c_void_p, Structure, byref, POINTER, sizeof
from typing import Optional, Deque, Dict, Tuple
from collections import deque
from enum import IntEnum

from video.image import RawImage
from video.vpx_img import VpxImage, VpxImgFmt
from protocol import Datagram, AckMsg
from utils.file_descriptor import FileDescriptor
from utils.exception_rim import check_syscall, check_call
from utils.timestamp import timestamp_us
from utils.conversion import narrow_cast

# try:
#     import debugpy; debugpy.connect(5678)
# except:
#     pass

# Load the libvpx library
libvpx = ctypes.CDLL('libvpx.so')

# Define vpx_codec_iface_t struct and functions
class vpx_codec_iface(Structure):
    _fields_ = [("name", c_char_p)]

# Set function signatures
vpx_codec_vp9_cx = libvpx.vpx_codec_vp9_cx
vpx_codec_vp9_cx.restype = ctypes.POINTER(vpx_codec_iface)
vpx_codec_vp9_cx.argtypes = []

# Constants for array sizes
VPX_SS_MAX_LAYERS = 5
VPX_TS_MAX_LAYERS = 5 
VPX_TS_MAX_PERIODICITY = 16
VPX_MAX_LAYERS = 12 # 3 temporal + 4 spatial layers are allowed.

# Define vpx_bit_depth_t enum
# class vpx_bit_depth(IntEnum):
#     VPX_BITS_8 = 8   # 8 bits
#     VPX_BITS_10 = 10 # 10 bits 
#     VPX_BITS_12 = 12 # 12 bits
vpx_bit_depth = c_int   # enum

# Define vpx_rational_t struct
class vpx_rational(Structure):
    _fields_ = [
        ("num", c_int),  # fraction numerator
        ("den", c_int)   # fraction denominator
    ]
vpx_rational_t = vpx_rational

# Define vpx_codec_er_flags_t
vpx_codec_er_flags_t = c_uint32

# Define VpxEncPass
# class VpxEncPass(IntEnum):
#     VPX_RC_ONE_PASS = 0    # Single pass mode
#     VPX_RC_FIRST_PASS = 1  # First pass of multi-pass mode  
#     VPX_RC_LAST_PASS = 2   # Final pass of multi-pass mode
vpx_enc_pass = c_int    # enum

# Define VpxRcMode
# class VpxRcMode(IntEnum):
#     VPX_VBR = 0  # Variable Bit Rate mode
#     VPX_CBR = 1  # Constant Bit Rate mode  
#     VPX_CQ = 2   # Constrained Quality mode
#     VPX_Q = 3    # Constant Quality mode
vpx_rc_mode = c_int # enum

# Define VpxFixedBufT struct
class vpx_fixed_buf(Structure):
    _fields_ = [
        ("buf", c_void_p),     # Pointer to the data
        ("sz", c_size_t)       # Length of the buffer, in chars
    ]

# Define necessary structures and constants (vpx_encoder.h)
class vpx_codec_enc_cfg(Structure):
    _fields_ = [
        # generic settings
        ("g_usage", c_uint),         # Must be zero
        ("g_threads", c_uint),       # Max number of threads
        ("g_profile", c_uint),       # Bitstream profile
        ("g_w", c_uint),            # Frame width
        ("g_h", c_uint),            # Frame height
        ("g_bit_depth", c_uint),     # Codec bit-depth, type: VpxBitDeepth
        ("g_input_bit_depth", c_uint), # Input frame bit-depth
        ("g_timebase", vpx_rational),   # Timebase numerator
        ("g_error_resilient", vpx_codec_er_flags_t), # Error resilient flags
        ("g_pass", vpx_enc_pass),          # Encoding pass (1 or 2), type: VpxEncPass
        ("g_lag_in_frames", c_uint), # Max lagged frames
        
        # rate control
        ("rc_dropframe_thresh", c_uint),  # Frame-drop threshold
        ("rc_resize_allowed", c_uint),    # Spatial resampling
        ("rc_scaled_width", c_uint),      # Internal coded width
        ("rc_scaled_height", c_uint),     # Internal coded height
        ("rc_resize_up_thresh", c_uint),  # Scale-up threshold  
        ("rc_resize_down_thresh", c_uint),# Scale-down threshold
        ("rc_end_usage", vpx_rc_mode),         # Rate control mode, type: VpxRcMode
        ("rc_twopass_stats_in", vpx_fixed_buf), # Two-pass stats buffer
        ("rc_firstpass_mb_stats_in", vpx_fixed_buf), # First pass mb stats buffer.
        ("rc_target_bitrate", c_uint),    # Target bitrate in Kbps
        
        # quantizer settings
        ("rc_min_quantizer", c_uint),     # Best quality QP
        ("rc_max_quantizer", c_uint),     # Worst quality QP
        
        # bitrate tolerance
        ("rc_undershoot_pct", c_uint),    # Undershoot control
        ("rc_overshoot_pct", c_uint),     # Overshoot control
        
        # decoder buffer model
        ("rc_buf_sz", c_uint),            # Decoder buffer size
        ("rc_buf_initial_sz", c_uint),    # Initial buffer size
        ("rc_buf_optimal_sz", c_uint),    # Optimal buffer size
        
        # 2 pass rate control
        ("rc_2pass_vbr_bias_pct", c_uint), # Bias for 2-pass VBR
        ("rc_2pass_vbr_minsection_pct", c_uint), # Min section in 2-pass VBR
        ("rc_2pass_vbr_maxsection_pct", c_uint), # Max section in 2-pass VBR
        ("rc_2pass_vbr_corpus_complexity", c_uint), # Corpus complexity for 2-pass VBR

        # keyframe settings  
        ("kf_mode", c_uint),              # Keyframe placement mode
        ("kf_min_dist", c_uint),          # Min keyframe interval
        ("kf_max_dist", c_uint),          # Max keyframe interval

        # spatial scalability settings
        ("ss_number_layers", c_uint),
        ("ss_enable_auto_alt_ref", c_int * VPX_SS_MAX_LAYERS),
        ("ss_target_bitrate", c_uint * VPX_SS_MAX_LAYERS),

        # temporal scalability settings
        ("ts_number_layers", c_uint),
        ("ts_target_bitrate", c_uint * VPX_TS_MAX_LAYERS),
        ("ts_rate_decimator", c_uint * VPX_TS_MAX_LAYERS),
        ("ts_periodicity", c_uint),
        ("ts_layer_id", c_uint * VPX_TS_MAX_PERIODICITY),

        # layer settings
        ("layer_target_bitrate", c_uint * VPX_MAX_LAYERS),
        ("temporal_layering_mode", c_int),

        # external rate control parameters
        ("use_vizier_rc_params", c_int),
        ("active_wq_factor", vpx_rational),
        ("err_per_mb_factor", vpx_rational),
        ("sr_default_decay_limit", vpx_rational),
        ("sr_diff_factor", vpx_rational),
        ("kf_err_per_mb_factor", vpx_rational),
        ("kf_frame_min_boost_factor", vpx_rational),
        ("kf_frame_max_boost_first_factor", vpx_rational),
        ("kf_frame_max_boost_subs_factor", vpx_rational),
        ("kf_max_total_boost_factor", vpx_rational),
        ("gf_max_total_boost_factor", vpx_rational),
        ("gf_frame_max_boost_factor", vpx_rational),
        ("zm_factor", vpx_rational),
        ("rd_mult_inter_qp_fac", vpx_rational),
        ("rd_mult_arf_qp_fac", vpx_rational), 
        ("rd_mult_key_qp_fac", vpx_rational),
    ]

vpx_codec_enc_config_default = libvpx.vpx_codec_enc_config_default
vpx_codec_enc_config_default.restype = c_int
vpx_codec_enc_config_default.argtypes = [ctypes.POINTER(vpx_codec_iface), ctypes.POINTER(vpx_codec_enc_cfg), c_uint]

class vpx_codec_ctx(Structure):
    _fields_ = [("name", c_char_p)]

VPX_IMAGE_ABI_VERSION = 5
VPX_CODEC_ABI_VERSION = 4 + VPX_IMAGE_ABI_VERSION
VPX_EXT_RATECTRL_ABI_VERSION = 1
VPX_ENCODER_ABI_VERSION = 15 + VPX_CODEC_ABI_VERSION + VPX_EXT_RATECTRL_ABI_VERSION

# codec_control const
VP8E_SET_CPUUSED = 13
VP8E_SET_STATIC_THRESHOLD = 17
VP8E_SET_MAX_INTRA_BITRATE_PCT = 26
VP9E_SET_AQ_MODE = 36
VP9E_SET_TILE_COLUMNS = 33
VP9E_SET_ROW_MT = 55
VP9E_SET_FRAME_PARALLEL_DECODING = 35
VP9E_SET_NOISE_SENSITIVITY = 38

# Constants
VPX_SS_MAX_LAYERS = 5

# Frame structure within union
class vpx_codec_frame_t(Structure):
    _fields_ = [
        ('buf', c_void_p),
        ('sz', c_size_t),
        ('pts', c_int64),  # vpx_codec_pts_t is typically int64
        ('duration', c_ulong),
        ('flags', c_int),  # vpx_codec_frame_flags_t
        ('partition_id', c_int),
        ('width', c_uint * VPX_SS_MAX_LAYERS),
        ('height', c_uint * VPX_SS_MAX_LAYERS),
        ('spatial_layer_encoded', c_uint8 * VPX_SS_MAX_LAYERS)
    ]

# PSNR structure
class vpx_psnr_pkt(Structure):
    _fields_ = [
        ('samples', c_uint * 4),
        ('sse', c_uint64 * 4),
        ('psnr', c_double * 4)
    ]

# Fixed buffer structure
class vpx_fixed_buf_t(Structure):
    _fields_ = [
        ('buf', c_void_p),
        ('sz', c_size_t)
    ]

# Union for packet data
class vpx_codec_cx_pkt_data(Union):
    _fields_ = [
        ('frame', vpx_codec_frame_t),
        ('twopass_stats', vpx_fixed_buf_t),
        ('firstpass_mb_stats', vpx_fixed_buf_t),
        ('psnr', vpx_psnr_pkt),
        ('raw', vpx_fixed_buf_t),
        ('pad', c_char * (128 - sizeof(c_int)))  # Ensure 128 byte alignment
    ]

# Main packet structure
class vpx_codec_cx_pkt(Structure):
    _fields_ = [
        ('kind', c_int),  # enum vpx_codec_cx_pkt_kind
        ('data', vpx_codec_cx_pkt_data)
    ]

# Update function signature
libvpx.vpx_codec_get_cx_data.argtypes = [
    POINTER(vpx_codec_ctx),
    POINTER(c_void_p)
]
libvpx.vpx_codec_get_cx_data.restype = POINTER(vpx_codec_cx_pkt)


class Encoder:
    ALPHA = 0.2
    MAX_NUM_RTX = 3
    MAX_UNACKED_US = 1000 * 1000  # 1s

    """
    Encoder::Encoder(const uint16_t display_width,
                    const uint16_t display_height,
                    const uint16_t frame_rate,
                    const string & output_path)
    : display_width_(display_width), display_height_(display_height),
        frame_rate_(frame_rate), output_fd_()
    {
        // open the output file
        if (not output_path.empty()) {
            output_fd_ = FileDescriptor(check_syscall(
                open(output_path.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0644)));
        }

        // populate VP9 configuration with default values
        check_call(vpx_codec_enc_config_default(&vpx_codec_vp9_cx_algo, &cfg_, 0),
                    VPX_CODEC_OK, "vpx_codec_enc_config_default");

        // copy the configuration below mostly from WebRTC (libvpx_vp9_encoder.cc)
        cfg_.g_w = display_width_;
        cfg_.g_h = display_height_;
        cfg_.g_timebase.num = 1;
        cfg_.g_timebase.den = frame_rate_; // WebRTC uses a 90 kHz clock
        cfg_.g_pass = VPX_RC_ONE_PASS;
        cfg_.g_lag_in_frames = 0; // disable lagged encoding
        // WebRTC disables error resilient mode unless for SVC
        cfg_.g_error_resilient = VPX_ERROR_RESILIENT_DEFAULT;
        cfg_.g_threads = 4; // encoder threads; should equal to column tiles below
        cfg_.rc_resize_allowed = 0; // WebRTC enables spatial sampling
        cfg_.rc_dropframe_thresh = 0; // WebRTC sets to 30 (% of target data buffer)
        cfg_.rc_buf_initial_sz = 500;
        cfg_.rc_buf_optimal_sz = 600;
        cfg_.rc_buf_sz = 1000;
        cfg_.rc_min_quantizer = 2;
        cfg_.rc_max_quantizer = 52;
        cfg_.rc_undershoot_pct = 50;
        cfg_.rc_overshoot_pct = 50;

        // prevent libvpx encoder from automatically placing key frames
        cfg_.kf_mode = VPX_KF_DISABLED;
        // WebRTC sets the two values below to 3000 frames (fixed keyframe interval)
        cfg_.kf_max_dist = numeric_limits<unsigned int>::max();
        cfg_.kf_min_dist = 0;

        cfg_.rc_end_usage = VPX_CBR;
        cfg_.rc_target_bitrate = target_bitrate_;

        // use no more than 16 or the number of avaialble CPUs
        const unsigned int cpu_used = min(get_nprocs(), 16);

        // more encoder settings
        check_call(vpx_codec_enc_init(&context_, &vpx_codec_vp9_cx_algo, &cfg_, 0),
                    VPX_CODEC_OK, "vpx_codec_enc_init");

        // this value affects motion estimation and *dominates* the encoding speed
        codec_control(&context_, VP8E_SET_CPUUSED, cpu_used);

        // enable encoder to skip static/low content blocks
        codec_control(&context_, VP8E_SET_STATIC_THRESHOLD, 1);

        // clamp the max bitrate of a keyframe to 900% of average per-frame bitrate
        codec_control(&context_, VP8E_SET_MAX_INTRA_BITRATE_PCT, 900);

        // enable encoder to adaptively change QP for each segment within a frame
        codec_control(&context_, VP9E_SET_AQ_MODE, 3);

        // set the number of column tiles in encoding a frame to 2 ** 2 = 4
        codec_control(&context_, VP9E_SET_TILE_COLUMNS, 2);

        // enable row-based multi-threading
        codec_control(&context_, VP9E_SET_ROW_MT, 1);

        // disable frame parallel decoding
        codec_control(&context_, VP9E_SET_FRAME_PARALLEL_DECODING, 0);

        // enable denoiser (but not on ARM since optimization is pending)
        codec_control(&context_, VP9E_SET_NOISE_SENSITIVITY, 1);

        cerr << "Initialized VP9 encoder (CPU used: " << cpu_used << ")" << endl;
    }
    """
    def __init__(self, display_width, display_height, frame_rate, output_path=""):
        self.display_width = display_width
        self.display_height = display_height
        self.frame_rate = frame_rate
        self.output_path = output_path
        self.output_fd: Optional[FileDescriptor] = None
        # print debugging info
        self.verbose = False
        # current target bitrate
        self.target_bitrate = 0
        # VPX encoding configuration and context
        self.context = vpx_codec_ctx()
        self.cfg = vpx_codec_enc_cfg()
        # frame ID to encode
        self.frame_id = 0
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

        if output_path:
            self.output_fd = FileDescriptor(check_syscall(os.open(output_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)))

        # Define the correct function signatures
        libvpx.vpx_codec_vp9_cx.restype = POINTER(vpx_codec_iface)
        libvpx.vpx_codec_enc_config_default.argtypes = [POINTER(vpx_codec_iface), POINTER(vpx_codec_enc_cfg), c_uint]

        # Replace the problematic line with:
        codec_iface = libvpx.vpx_codec_vp9_cx()

        # Initialize VP9 configuration with default values
        check_call(libvpx.vpx_codec_enc_config_default(codec_iface, byref(self.cfg), 0),
                   0, "vpx_codec_enc_config_default")   # VPX_CODEC_OK

        # Set configuration parameters
        self.cfg.g_w = display_width
        self.cfg.g_h = display_height
        self.cfg.g_timebase_num = 1
        self.cfg.g_timebase_den = frame_rate
        self.cfg.g_pass = 0  # VPX_RC_ONE_PASS
        self.cfg.g_lag_in_frames = 0
        self.cfg.g_error_resilient = 1  # VPX_ERROR_RESILIENT_DEFAULT
        self.cfg.g_threads = 4
        self.cfg.rc_resize_allowed = 0
        self.cfg.rc_dropframe_thresh = 0
        self.cfg.rc_buf_initial_sz = 500
        self.cfg.rc_buf_optimal_sz = 600
        self.cfg.rc_buf_sz = 1000
        self.cfg.rc_min_quantizer = 2
        self.cfg.rc_max_quantizer = 52
        self.cfg.rc_undershoot_pct = 50
        self.cfg.rc_overshoot_pct = 50
        self.cfg.kf_mode = 0  # VPX_KF_DISABLED
        self.cfg.kf_max_dist = ctypes.c_uint32(-1).value
        self.cfg.kf_min_dist = 0
        self.cfg.rc_end_usage = 1  # VPX_CBR
        self.cfg.rc_target_bitrate = self.target_bitrate

        # Initialize codec
        check_call(libvpx.vpx_codec_enc_init_ver(
            byref(self.context), 
            codec_iface, 
            byref(self.cfg), 
            0,
            25
            ),
            0, "vpx_codec_enc_init")  # VPX_CODEC_OK

        # Set additional codec controls
        cpu_used = min(os.cpu_count(), 16)
        check_call(libvpx.vpx_codec_control_(byref(self.context), VP8E_SET_CPUUSED, cpu_used), 0, "vpx_codec_control_")  # VP8E_SET_CPUUSED
        check_call(libvpx.vpx_codec_control_(byref(self.context), VP8E_SET_STATIC_THRESHOLD, 1), 0, "vpx_codec_control_")  # VP8E_SET_STATIC_THRESHOLD
        check_call(libvpx.vpx_codec_control_(byref(self.context), VP8E_SET_MAX_INTRA_BITRATE_PCT, 900), 0, "vpx_codec_control_")  # VP8E_SET_MAX_INTRA_BITRATE_PCT
        check_call(libvpx.vpx_codec_control_(byref(self.context), VP9E_SET_AQ_MODE, 3), 0, "vpx_codec_control_")  # VP9E_SET_AQ_MODE
        check_call(libvpx.vpx_codec_control_(byref(self.context), VP9E_SET_TILE_COLUMNS, 2), 0, "vpx_codec_control_")  # VP9E_SET_TILE_COLUMNS
        check_call(libvpx.vpx_codec_control_(byref(self.context), VP9E_SET_ROW_MT, 1), 0, "vpx_codec_control_")  # VP9E_SET_ROW_MT
        check_call(libvpx.vpx_codec_control_(byref(self.context), VP9E_SET_FRAME_PARALLEL_DECODING, 0), 0, "vpx_codec_control_")  # VP9E_SET_FRAME_PARALLEL_DECODING
        check_call(libvpx.vpx_codec_control_(byref(self.context), VP9E_SET_NOISE_SENSITIVITY, 1), 0, "vpx_codec_control_") # VP9E_SET_NOISE_SENSITIVITY

        print(f"Initialized VP9 encoder (CPU used: {cpu_used})")

    """
    Encoder::~Encoder()
    {
        if (vpx_codec_destroy(&context_) != VPX_CODEC_OK) {
            cerr << "~Encoder(): failed to destroy VPX encoder context" << endl;
        }
    }
    """
    def __del__(self):
        if libvpx.vpx_codec_destroy(byref(self.context)) != 0:
            print("~Encoder(): failed to destroy VPX encoder context")

    """
    void Encoder::compress_frame(const RawImage & raw_img)
    {
        const auto frame_generation_ts = timestamp_us();

        // encode raw_img into frame 'frame_id_'
        encode_frame(raw_img);

        // packetize frame 'frame_id_' into datagrams
        const size_t frame_size = packetize_encoded_frame();

        // output frame information
        if (output_fd_) {
            const auto frame_encoded_ts = timestamp_us();

            output_fd_->write(to_string(frame_id_) + "," +
                            to_string(target_bitrate_) + "," +
                            to_string(frame_size) + "," +
                            to_string(frame_generation_ts) + "," +
                            to_string(frame_encoded_ts) + "\n");
        }

        // move onto the next frame
        frame_id_++;
    }
    """
    def compress_frame(self, raw_img):
        frame_generation_ts = time.time()

        self.encode_frame(raw_img)
        frame_size = self.packetize_encoded_frame()

        if self.output_fd:
            frame_encoded_ts = time.time()
            self.output_fd.write(f"{self.frame_id},{self.target_bitrate},{frame_size},\
                                 {frame_generation_ts},{frame_encoded_ts}\n")

        self.frame_id += 1

    """
    void Encoder::encode_frame(const RawImage & raw_img)
    {
        if (raw_img.display_width() != display_width_ or
            raw_img.display_height() != display_height_) {
            throw runtime_error("Encoder: image dimensions don't match");
        }

        // check if a key frame needs to be encoded
        vpx_enc_frame_flags_t encode_flags = 0; // normal frame
        if (not unacked_.empty()) {
            const auto & first_unacked = unacked_.cbegin()->second;

            // give up if first unacked datagram was initially sent MAX_UNACKED_US ago
            const auto us_since_first_send = timestamp_us() - first_unacked.send_ts;

            if (us_since_first_send > MAX_UNACKED_US) {
            encode_flags = VPX_EFLAG_FORCE_KF; // force next frame to be key frame

            cerr << "* Recovery: gave up retransmissions and forced a key frame "
                << frame_id_ << endl;

            if (verbose_) {
                cerr << "Giving up on lost datagram: frame_id="
                    << first_unacked.frame_id << " frag_id=" << first_unacked.frag_id
                    << " rtx=" << first_unacked.num_rtx
                    << " us_since_first_send=" << us_since_first_send << endl;
            }

            // clean up
            send_buf_.clear();
            unacked_.clear();
            }
        }

        // encode a frame and calculate encoding time
        const auto encode_start = steady_clock::now();
        check_call(vpx_codec_encode(&context_, raw_img.get_vpx_image(), frame_id_, 1,
                                    encode_flags, VPX_DL_REALTIME),
                    VPX_CODEC_OK, "failed to encode a frame");
        const auto encode_end = steady_clock::now();
        const double encode_time_ms = duration<double, milli>(
                                        encode_end - encode_start).count();

        // track stats in the current period
        num_encoded_frames_++;
        total_encode_time_ms_ += encode_time_ms;
        max_encode_time_ms_ = max(max_encode_time_ms_, encode_time_ms);
    }
    """
    def encode_frame(self, raw_img: RawImage):
        if raw_img.display_width() != self.display_width or raw_img.display_height() != self.display_height:
            raise RuntimeError("Encoder: image dimensions don't match")

        # check if a key frame needs to be encoded
        encode_flags = 0    # normal frame

        if self.unacked:
            first_unacked = next(iter(self.unacked.values()))
            # give up if first unacked datagram was initially sent MAX_UNACKED_US ago
            us_since_first_send = timestamp_us() - first_unacked.send_ts

            if us_since_first_send > self.MAX_UNACKED_US:
                encode_flags = 1  # VPX_EFLAG_FORCE_KF; force next frame to be key frame

                print(f"* Recovery: gave up retransmissions and forced a key frame {self.frame_id}")

                if self.verbose:
                    print(f"Giving up on lost datagram: frame_id={first_unacked.frame_id} "
                        f"frag_id={first_unacked.frag_id} rtx={first_unacked.num_rtx} "
                        f"us_since_first_send={us_since_first_send}")

                # clean up
                self.send_buf.clear()
                self.unacked.clear()

        encode_start = time.time()
        check_call(libvpx.vpx_codec_encode(byref(self.context), raw_img.get_vpx_image(), self.frame_id, 1, encode_flags, 1),
                   0, "failed to encode a frame")  # VPX_CODEC_OK # VPX_DL_REALTIME
        encode_end = time.time()
        encode_time_ms = (encode_end - encode_start) * 1000

        # track stats in the current period
        self.num_encoded_frames += 1
        self.total_encode_time_ms += encode_time_ms
        self.max_encode_time_ms = max(self.max_encode_time_ms, encode_time_ms)

    """
    size_t Encoder::packetize_encoded_frame()
    {
        // read the encoded frame's "encoder packets" from 'context_'
        const vpx_codec_cx_pkt_t * encoder_pkt;
        vpx_codec_iter_t iter = nullptr;
        unsigned int frames_encoded = 0;
        size_t frame_size = 0;

        while ((encoder_pkt = vpx_codec_get_cx_data(&context_, &iter))) {
            if (encoder_pkt->kind == VPX_CODEC_CX_FRAME_PKT) {
                frames_encoded++;

                // there should be exactly one frame encoded
                if (frames_encoded > 1) {
                    throw runtime_error("Multiple frames were encoded at once");
                }

                frame_size = encoder_pkt->data.frame.sz;
                assert(frame_size > 0);

                // read the returned frame type
                auto frame_type = FrameType::NONKEY;
                if (encoder_pkt->data.frame.flags & VPX_FRAME_IS_KEY) {
                    frame_type = FrameType::KEY;

                    if (verbose_) {
                    cerr << "Encoded a key frame: frame_id=" << frame_id_ << endl;
                    }
                }

                // total fragments to divide this frame into
                const uint16_t frag_cnt = narrow_cast<uint16_t>(
                    frame_size / (Datagram::max_payload + 1) + 1);

                // next address to copy compressed frame data from
                uint8_t * buf_ptr = static_cast<uint8_t *>(encoder_pkt->data.frame.buf);
                const uint8_t * const buf_end = buf_ptr + frame_size;

                for (uint16_t frag_id = 0; frag_id < frag_cnt; frag_id++) {
                    // calculate payload size and construct the payload
                    const size_t payload_size = (frag_id < frag_cnt - 1) ?
                        Datagram::max_payload : buf_end - buf_ptr;

                    // enqueue a datagram
                    send_buf_.emplace_back(frame_id_, frame_type, frag_id, frag_cnt,
                    string_view {reinterpret_cast<const char *>(buf_ptr), payload_size});

                    buf_ptr += payload_size;
                }
            }
        }
        return frame_size;
    }
    """
    def packetize_encoded_frame(self):
        iter = c_void_p()
        frames_encoded = 0
        frame_size = 0

        while True:
            encoder_pkt = libvpx.vpx_codec_get_cx_data(byref(self.context), byref(iter))
            if not encoder_pkt:
                break
                
            if encoder_pkt.contents.kind == 0: # VPX_CODEC_CX_FRAME_PKT
                frames_encoded += 1
                if frames_encoded > 1:
                    raise RuntimeError("Multiple frames were encoded at once")
                    
                frame_size = encoder_pkt.contents.data.frame.sz
                frame_type = 'KEY' if (encoder_pkt.contents.data.frame.flags & 0) else 'DELTA'
                
                if self.verbose:
                    print(f"Encoded a {frame_type} frame: frame_id={self.frame_id}")

                # Calculate fragments needed
                frag_cnt = narrow_cast(int, (frame_size // (Datagram.max_payload + 1)) + 1)
                
                # Get buffer pointer
                buf_ptr = ctypes.cast(
                    encoder_pkt.contents.data.frame.buf,
                    ctypes.POINTER(ctypes.c_uint8 * frame_size)
                )
                
                # Create a memoryview for efficient slicing
                buffer = memoryview(buf_ptr.contents)
                
                # Split into fragments
                for frag_id in range(frag_cnt):
                    start = frag_id * Datagram.max_payload
                    end = min(start + Datagram.max_payload, frame_size)
                    payload = bytes(buffer[start:end])
                    
                    dgram = Datagram(
                        frame_id=self.frame_id,
                        frame_type=frame_type,
                        frag_id=frag_id,
                        frag_cnt=frag_cnt,
                        payload=payload
                    )
                    self.send_buf.append(dgram)

        return frame_size
    
    """
    void Encoder::add_unacked(const Datagram & datagram)
    {
        const auto seq_num = make_pair(datagram.frame_id, datagram.frag_id);
        auto [it, success] = unacked_.emplace(seq_num, datagram);

        if (not success) {
            throw runtime_error("datagram already exists in unacked");
        }

        it->second.last_send_ts = it->second.send_ts;
    }
    
    void Encoder::add_unacked(Datagram && datagram)
    {
        const auto seq_num = make_pair(datagram.frame_id, datagram.frag_id);
        auto [it, success] = unacked_.emplace(seq_num, move(datagram));

        if (not success) {
            throw runtime_error("datagram already exists in unacked");
        }

        it->second.last_send_ts = it->second.send_ts;
    }
    """
    def add_unacked(self, datagram: Datagram):
        seq_num = (datagram.frame_id, datagram.frag_id)
        if seq_num in self.unacked:
            raise RuntimeError("datagram already exists in unacked")

        self.unacked[seq_num] = datagram
        self.unacked[seq_num].last_send_ts = datagram.send_ts

    """
    void Encoder::handle_ack(const shared_ptr<AckMsg> & ack)
    {
    const auto curr_ts = timestamp_us();

    // observed an RTT sample
    add_rtt_sample(curr_ts - ack->send_ts);

    // find the acked datagram in 'unacked_'
    const auto acked_seq_num = make_pair(ack->frame_id, ack->frag_id);
    auto acked_it = unacked_.find(acked_seq_num);

    if (acked_it == unacked_.end()) {
        // do nothing else if ACK is not for an unacked datagram
        return;
    }

    // retransmit all unacked datagrams before the acked one (backward)
    for (auto rit = make_reverse_iterator(acked_it);
        rit != unacked_.rend(); rit++) {
        auto & datagram = rit->second;

        // skip if a datagram has been retransmitted MAX_NUM_RTX times
        if (datagram.num_rtx >= MAX_NUM_RTX) {
        continue;
        }

            // retransmit if it's the first RTX or the last RTX was about one RTT ago
            if (datagram.num_rtx == 0 or
                curr_ts - datagram.last_send_ts > ewma_rtt_us_.value()) {
            datagram.num_rtx++;
            datagram.last_send_ts = curr_ts;

            // retransmissions are more urgent
            send_buf_.emplace_front(datagram);
            }
        }

        // finally, erase the acked datagram from 'unacked_'
        unacked_.erase(acked_it);
    }
    """
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

    """
    void Encoder::add_rtt_sample(const unsigned int rtt_us)
    {
        // min RTT
        if (not min_rtt_us_ or rtt_us < *min_rtt_us_) {
            min_rtt_us_ = rtt_us;
        }

        // EWMA RTT
        if (not ewma_rtt_us_) {
            ewma_rtt_us_ = rtt_us;
        } else {
            ewma_rtt_us_ = ALPHA * rtt_us + (1 - ALPHA) * (*ewma_rtt_us_);
        }
    }
    """
    def add_rtt_sample(self, rtt_us: int):
        # min RTT
        if self.min_rtt_us is None or rtt_us < self.min_rtt_us:
            self.min_rtt_us = rtt_us

        # EWMA RTT
        if self.ewma_rtt_us is None:
            self.ewma_rtt_us = rtt_us
        else:
            self.ewma_rtt_us = self.ALPHA * rtt_us + (1 - self.ALPHA) * self.ewma_rtt_us

    """
    void Encoder::output_periodic_stats()
    {
        cerr << "Frames encoded in the last ~1s: " << num_encoded_frames_ << endl;

        if (num_encoded_frames_ > 0) {
            cerr << "  - Avg/Max encoding time (ms): "
                << double_to_string(total_encode_time_ms_ / num_encoded_frames_)
                << "/" << double_to_string(max_encode_time_ms_) << endl;
        }

        if (min_rtt_us_ and ewma_rtt_us_) {
            cerr << "  - Min/EWMA RTT (ms): " << double_to_string(*min_rtt_us_ / 1000.0)
                << "/" << double_to_string(*ewma_rtt_us_ / 1000.0) << endl;
        }

        // reset all but RTT-related stats
        num_encoded_frames_ = 0;
        total_encode_time_ms_ = 0.0;
        max_encode_time_ms_ = 0.0;
    }
    """
    def output_periodic_stats(self):
        print(f"Frames encoded in the last ~1s: {self.num_encoded_frames}")
        if self.num_encoded_frames > 0:
            avg_encode_time = self.total_encode_time_ms / self.num_encoded_frames
            print(f" - Avg/Max encoding time (ms): {avg_encode_time}/{self.max_encode_time_ms}")
        if self.min_rtt_us and self.ewma_rtt_us:
            print(f" - Min/EWMA RTT (ms): {self.min_rtt_us / 1000.0}/{self.ewma_rtt_us / 1000.0}")

        # reset all but RTT-related stats
        self.num_encoded_frames = 0
        self.total_encode_time_ms = 0.0
        self.max_encode_time_ms = 0.0

    """
    void Encoder::set_target_bitrate(const unsigned int bitrate_kbps)
    {
        target_bitrate_ = bitrate_kbps;

        cfg_.rc_target_bitrate = target_bitrate_;
        check_call(vpx_codec_enc_config_set(&context_, &cfg_),
                    VPX_CODEC_OK, "set_target_bitrate");
    }
    """
    def set_target_bitrate(self, bitrate_kbps: int):
        self.target_bitrate = bitrate_kbps
        
        self.cfg.rc_target_bitrate = bitrate_kbps
        check_call(libvpx.vpx_codec_enc_config_set(byref(self.context), byref(self.cfg)),
                   0, "set_target_bitrate") # VPX_CODEC_OK

def test_encoder():
    """Test the VP9 encoder with synthetic video frames"""
    import numpy as np


    # Set up encoder parameters
    width = 640
    height = 480
    framerate = 30
    output_path = "encoded_frames.csv"
    
    # Initialize encoder
    encoder = Encoder(
        display_width=width,
        display_height=height,
        frame_rate=framerate,
        output_path=output_path
    )
    
    # Set initial target bitrate (500 Kbps)
    encoder.set_target_bitrate(500)
    
    # Create 10 test frames
    num_frames = 10
    
    print(f"\nEncoding {num_frames} test frames...")
    
    for frame_num in range(num_frames):
        # Create synthetic frame (checkerboard)
        raw_data = np.zeros((height, width), dtype=np.uint8)
        raw_data[::2, ::2] = 255
        raw_data[1::2, 1::2] = 255
        offset = frame_num * 10
        raw_data = np.roll(raw_data, offset, axis=1)
        
        # Create YUV planes
        y_plane = raw_data.tobytes()
        u_plane = np.zeros((height//2, width//2), dtype=np.uint8).tobytes()
        v_plane = np.zeros((height//2, width//2), dtype=np.uint8).tobytes()
        
        # Create RawImage and copy planes
        raw_image = RawImage(width, height)
        raw_image.copy_y_from(y_plane)
        raw_image.copy_u_from(u_plane)
        raw_image.copy_v_from(v_plane)
        
        # Verify data integrity
        y_data = np.ctypeslib.as_array(raw_image.y_plane(), 
                                      shape=(raw_image.y_size(),))
        u_data = np.ctypeslib.as_array(raw_image.u_plane(), 
                                      shape=(raw_image.uv_size(),))
        v_data = np.ctypeslib.as_array(raw_image.v_plane(), 
                                      shape=(raw_image.uv_size(),))
        
        # Compress frame
        encoder.compress_frame(raw_image)
        print(f"Encoded frame {frame_num + 1}/{num_frames}")
        
        if (frame_num + 1) % 5 == 0:
            print("\nPeriodic Stats:")
            encoder.output_periodic_stats()
        
        time.sleep(1/framerate)
    
    print("\nEncoding complete!")
    print(f"Results written to {output_path}")

if __name__ == "__main__":
    # try:
    test_encoder()
    # except Exception as e:
    #     print(f"Error occurred: {e}")