from ctypes import Structure, Union, c_long, cast, memmove
from ctypes import POINTER, sizeof, byref
from ctypes import c_int, c_uint, c_int64, c_uint64, c_uint32, c_uint16, c_uint8
from ctypes import c_void_p, c_char_p
from ctypes import c_ulong
from ctypes import c_ubyte
from ctypes import c_double
from ctypes import c_char
from ctypes import CDLL

# Load the vpx library
libvpx = CDLL('libvpx.so')

"""
vpx image

"""

"""
brief Current ABI version number
"""
VPX_IMAGE_ABI_VERSION = 5  # hideinitializer

VPX_IMG_FMT_PLANAR = 0x100       # Image is a planar format.
VPX_IMG_FMT_UV_FLIP = 0x200      # V plane precedes U in memory.
VPX_IMG_FMT_HAS_ALPHA = 0x400    # Image has an alpha channel.
VPX_IMG_FMT_HIGHBITDEPTH = 0x800 # Image uses 16bit framebuffer.

"""
brief List of supported image formats
"""
vpx_img_fmt = c_int
VPX_IMG_FMT_NONE = 0
VPX_IMG_FMT_YV12 = VPX_IMG_FMT_PLANAR | VPX_IMG_FMT_UV_FLIP | 1  # planar YVU
VPX_IMG_FMT_I420 = VPX_IMG_FMT_PLANAR | 2
VPX_IMG_FMT_I422 = VPX_IMG_FMT_PLANAR | 5
VPX_IMG_FMT_I444 = VPX_IMG_FMT_PLANAR | 6
VPX_IMG_FMT_I440 = VPX_IMG_FMT_PLANAR | 7
VPX_IMG_FMT_NV12 = VPX_IMG_FMT_PLANAR | 9
VPX_IMG_FMT_I42016 = VPX_IMG_FMT_I420 | VPX_IMG_FMT_HIGHBITDEPTH
VPX_IMG_FMT_I42216 = VPX_IMG_FMT_I422 | VPX_IMG_FMT_HIGHBITDEPTH
VPX_IMG_FMT_I44416 = VPX_IMG_FMT_I444 | VPX_IMG_FMT_HIGHBITDEPTH
VPX_IMG_FMT_I44016 = VPX_IMG_FMT_I440 | VPX_IMG_FMT_HIGHBITDEPTH

"""
brief List of supported color spaces
"""
vpx_color_space = c_int
VPX_CS_UNKNOWN = 0   # Unknown
VPX_CS_BT_601 = 1    # BT.601
VPX_CS_BT_709 = 2    # BT.709
VPX_CS_SMPTE_170 = 3 # SMPTE.170
VPX_CS_SMPTE_240 = 4 # SMPTE.240
VPX_CS_BT_2020 = 5   # BT.2020
VPX_CS_RESERVED = 6  # Reserved
VPX_CS_SRGB = 7      # sRGB

"""
brief List of supported color range
"""
vpx_color_range = c_int
VPX_CR_STUDIO_RANGE = 0 # Y [16..235], UV [16..240]
VPX_CR_FULL_RANGE = 1   # YUV/RGB [0..255]

"""
brief Image Descriptor
"""
class vpx_image(Structure):
    _fields_ = [
        ("fmt", vpx_img_fmt),               # Image Format
        ("cs", vpx_color_space),            # Color Space
        ("range", vpx_color_range),         # Color Range
        ("w", c_uint),                      # Stored image width
        ("h", c_uint),                      # Stored image height
        ("bit_depth", c_uint),              # Stored image bit-depth
        ("d_w", c_uint),                    # Displayed image width
        ("d_h", c_uint),                    # Displayed image height
        ("r_w", c_uint),                    # Intended rendering image width
        ("r_h", c_uint),                    # Intended rendering image height
        ("x_chroma_shift", c_uint),         # subsampling order, X
        ("y_chroma_shift", c_uint),         # subsampling order, Y
        ("planes", POINTER(c_ubyte) * 4),   # pointer to the top left pixel for each plane
        ("stride", c_int * 4),              # stride between rows for each plane
        ("bps", c_int),                     # bits per sample (for packed formats)
        ("user_priv", c_void_p),            # The following member may be set by the application to associate data with this image.
        ("img_data", POINTER(c_ubyte)),     # private
        ("img_data_owner", c_int),          # private
        ("self_allocd", c_int),             # private
        ("fb_priv", c_void_p),              # Frame buffer data associated with the image.
    ]

VPX_PLANE_PACKED = 0  # /**< To be used for all packed formats */
VPX_PLANE_Y = 0       # /**< Y (Luminance) plane */
VPX_PLANE_U = 1       # /**< U (Chroma) plane */
VPX_PLANE_V = 2       # /**< V (Chroma) plane */
VPX_PLANE_ALPHA = 3   # /**< A (Transparency) plane */

"""
brief Representation of a rectangle on a surface
"""
class vpx_image_rect(Structure):
    _fields_ = [
        ("x", c_uint), # leftmost column
        ("y", c_uint), # topmost row
        ("w", c_uint), # width
        ("h", c_uint), # height
    ]

vpx_image_t = vpx_image

libvpx.vpx_img_alloc.restype = POINTER(vpx_image)
libvpx.vpx_img_alloc.argtypes = [POINTER(vpx_image), vpx_img_fmt, c_uint16, c_uint16, c_uint16]
libvpx.vpx_img_free.argtypes = [POINTER(vpx_image)]








"""
Codec

"""
# Define vpx_codec_iface_t struct and functions
class vpx_codec_iface(Structure):
    _fields_ = [("name", c_char_p)]


# Constants for array sizes
VPX_SS_MAX_LAYERS = 5
VPX_TS_MAX_LAYERS = 5 
VPX_TS_MAX_PERIODICITY = 16
VPX_MAX_LAYERS = 12 # 3 temporal + 4 spatial layers are allowed.

# Define vpx_bit_depth
VPX_BITS_8 = 8   # 8 bits
VPX_BITS_10 = 10 # 10 bits 
VPX_BITS_12 = 12 # 12 bits
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

# Define vpx_enc_pass
VPX_RC_ONE_PASS = 0    # Single pass mode
VPX_RC_FIRST_PASS = 1  # First pass of multi-pass mode  
VPX_RC_LAST_PASS = 2   # Final pass of multi-pass mode
vpx_enc_pass = c_int    # enum

# Define vpx_rc_mode
VPX_VBR = 0  # Variable Bit Rate mode
VPX_CBR = 1  # Constant Bit Rate mode  
VPX_CQ = 2   # Constrained Quality mode
VPX_Q = 3    # Constant Quality mode
vpx_rc_mode = c_int # enum

# define vpx_kf_mode
VPX_KF_FIXED = 0      # deprecated, implies VPX_KF_DISABLED 
VPX_KF_AUTO = 1       # Encoder determines optimal placement automatically
VPX_KF_DISABLED = 0   # Encoder does not place keyframes.
vpx_kf_mode = c_int # enum

size_t = c_ulong
uint8_t = c_uint8

# Define vpx_fixed_buf
class vpx_fixed_buf(Structure):
    _fields_ = [
        ("buf", c_void_p),     # Pointer to the data
        ("sz", size_t)       # Length of the buffer, in chars
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
        ("kf_mode", vpx_kf_mode),         # Keyframe placement mode
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

vpx_codec_iface_t = vpx_codec_iface
vpx_codec_enc_cfg_t = vpx_codec_enc_cfg


# define vpx_codec_err_t
VPX_CODEC_OK = 0  # Operation completed without error
VPX_CODEC_ERROR = 1  # Unspecified error
VPX_CODEC_MEM_ERROR = 2  # Memory operation failed
VPX_CODEC_ABI_MISMATCH = 3  # ABI version mismatch
VPX_CODEC_INCAPABLE = 4  # Algorithm does not have required capability
# The bitstream was unable to be parsed at the highest level
VPX_CODEC_UNSUP_BITSTREAM = 5  
# Encoded bitstream uses an unsupported feature
VPX_CODEC_UNSUP_FEATURE = 6
# The coded data for this stream is corrupt or incomplete
VPX_CODEC_CORRUPT_FRAME = 7
VPX_CODEC_INVALID_PARAM = 8  # An application-supplied parameter is not valid
VPX_CODEC_LIST_END = 9  # An iterator reached the end of list
vpx_codec_err_t = c_int # enum


vpx_codec_flags_t = c_long


class vpx_codec_dec_cfg(Structure):
    _fields_ = [
        ('threads', c_uint),
        ('w', c_uint),
        ('h', c_uint),
    ]


# Config union
class N13vpx_codec_ctx3DOT_2E(Union):
    _fields_ = [
        ('dec', POINTER(vpx_codec_dec_cfg)),
        ('enc', POINTER(vpx_codec_enc_cfg)), 
        ('raw', c_void_p)
    ]

class vpx_codec_priv(Structure):
    _fields_ = []   

vpx_codec_priv_t = vpx_codec_priv


class vpx_codec_ctx(Structure):
    _fields_ = [
        ('name', c_char_p),                     # Printable interface name
        ('iface', POINTER(vpx_codec_iface_t)),  # Interface pointers
        ('err', vpx_codec_err_t),               # Last returned error
        ('err_detail', c_char_p),               # Detailed error info
        ('init_flags', vpx_codec_flags_t),      # Init flags
        ('config', N13vpx_codec_ctx3DOT_2E),    # Configuration union
        ('priv', POINTER(vpx_codec_priv_t))     # Private storage
    ]

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

VPX_ERROR_RESILIENT_DEFAULT = 0x1

# define vpx_codec_cx_pkt_kind
vpx_codec_cx_pkt_kind = c_int
VPX_CODEC_CX_FRAME_PKT = 0,     # Compressed video frame
VPX_CODEC_STATS_PKT = 1         # Two-pass statistics for this frame
VPX_CODEC_FPMB_STATS_PKT = 2    # first pass mb statistics for this frame
VPX_CODEC_PSNR_PKT = 3          # PSNR statistics for this frame
VPX_CODEC_CUSTOM_PKT = 256      # Algorithm extensions

# frame is the start of a GOP
VPX_FRAME_IS_KEY = 0x1

# Frame structure within union
class vpx_codec_frame_t(Structure):
    _fields_ = [
        ('buf', c_void_p),
        ('sz', size_t),
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
        ('sz', size_t)
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

uint32_t = c_uint32
vpx_codec_frame_flags_t = uint32_t
int64_t = c_int64
vpx_codec_pts_t = int64_t



class N16vpx_codec_cx_pkt3DOT_63DOT_7E(Structure):
    _fields_ = [
        ('buf', c_void_p),
        ('sz', size_t),
        ('pts', vpx_codec_pts_t),
        ('duration', c_ulong),
        ('flags', vpx_codec_frame_flags_t),
    ]

class N16vpx_codec_cx_pkt3DOT_6E(Union):
    _fields_ = [
        ('frame', N16vpx_codec_cx_pkt3DOT_63DOT_7E),
        ('twopass_stats', vpx_fixed_buf),
        ('psnr', vpx_psnr_pkt),
        ('raw', vpx_fixed_buf),
        ('pad', c_char * 124),
    ]

# Main packet structure
class vpx_codec_cx_pkt(Structure):
    _fields_ = [
        ('kind', vpx_codec_cx_pkt_kind),  # enum vpx_codec_cx_pkt_kind
        ('data', N16vpx_codec_cx_pkt3DOT_6E)
    ]

vpx_codec_cx_pkt_t = vpx_codec_cx_pkt
vpx_codec_ctx_t = vpx_codec_ctx
vpx_codec_iter_t = c_void_p


vpx_image_t = vpx_image
vpx_enc_frame_flags_t = c_long
int64_t = c_int64
vpx_codec_pts_t = int64_t

VPX_DL_REALTIME = 1

vpx_codec_vp9_cx_algo = (vpx_codec_iface_t).in_dll(libvpx, 'vpx_codec_vp9_cx_algo')

vpx_codec_vp9_cx = libvpx.vpx_codec_vp9_cx
vpx_codec_vp9_cx.restype = POINTER(vpx_codec_iface_t)
vpx_codec_vp9_cx.argtypes = []
vpx_codec_vp9_cx.__doc__ = \
"""vpx_codec_iface_t * vpx_codec_vp9_cx(void)
/xtra/libvpx/vpx/vp8cx.h:45"""

vpx_codec_enc_init_ver = libvpx.vpx_codec_enc_init_ver
vpx_codec_enc_init_ver.restype = vpx_codec_err_t
vpx_codec_enc_init_ver.argtypes = [POINTER(vpx_codec_ctx_t), POINTER(vpx_codec_iface_t), POINTER(vpx_codec_enc_cfg_t), vpx_codec_flags_t, c_int]
vpx_codec_enc_init_ver.__doc__ = \
"""vpx_codec_err_t vpx_codec_enc_init_ver(vpx_codec_ctx_t * ctx, vpx_codec_iface_t * iface, vpx_codec_enc_cfg_t * cfg, vpx_codec_flags_t flags, int ver)
/xtra/libvpx/vpx/vpx_encoder.h:581"""

def vpx_codec_enc_init(ctx,iface,cfg,flags): return vpx_codec_enc_init_ver(ctx, iface, cfg, flags, VPX_ENCODER_ABI_VERSION) # macro

# Update function signature
vpx_codec_get_cx_data = libvpx.vpx_codec_get_cx_data
vpx_codec_get_cx_data.restype = POINTER(vpx_codec_cx_pkt_t)
vpx_codec_get_cx_data.argtypes = [
    POINTER(vpx_codec_ctx_t),
    POINTER(vpx_codec_iter_t)
]
vpx_codec_get_cx_data.__doc__ = \
"""unknown * vpx_codec_get_cx_data(vpx_codec_ctx_t * ctx, vpx_codec_iter_t * iter)
/xtra/libvpx/vpx/vpx_encoder.h:771"""

# Define the correct function signatures
vpx_codec_vp9_cx = libvpx.vpx_codec_vp9_cx()
vpx_codec_vp9_cx.restype = POINTER(vpx_codec_iface_t)

vpx_codec_enc_config_default = libvpx.vpx_codec_enc_config_default
vpx_codec_enc_config_default.restype = vpx_codec_err_t
vpx_codec_enc_config_default.argtypes = [POINTER(vpx_codec_iface_t), POINTER(vpx_codec_enc_cfg_t), c_uint]

vpx_codec_control_ = libvpx.vpx_codec_control_
vpx_codec_control_.restype = vpx_codec_err_t
vpx_codec_control_.argtypes = [POINTER(vpx_codec_ctx_t), c_int]
vpx_codec_control_.__doc__ = \
"""vpx_codec_err_t vpx_codec_control_(vpx_codec_ctx_t * ctx, int ctrl_id)
/xtra/libvpx/vpx/vpx_codec.h:375"""


vpx_codec_encode = libvpx.vpx_codec_encode
vpx_codec_encode.restype = vpx_codec_err_t
vpx_codec_encode.argtypes = [POINTER(vpx_codec_ctx_t), POINTER(vpx_image_t), vpx_codec_pts_t, c_ulong, vpx_enc_frame_flags_t, c_ulong]
vpx_codec_encode.__doc__ = \
"""vpx_codec_err_t vpx_codec_encode(vpx_codec_ctx_t * ctx, unknown * img, vpx_codec_pts_t pts, long unsigned int duration, vpx_enc_frame_flags_t flags, long unsigned int deadline)
/xtra/libvpx/vpx/vpx_encoder.h:695"""



vpx_codec_destroy = libvpx.vpx_codec_destroy
vpx_codec_destroy.restype = vpx_codec_err_t
vpx_codec_destroy.argtypes = [POINTER(vpx_codec_ctx_t)]
vpx_codec_destroy.__doc__ = \
"""vpx_codec_err_t vpx_codec_destroy(vpx_codec_ctx_t * ctx)
/xtra/libvpx/vpx/vpx_codec.h:336"""

vpx_codec_enc_config_set = libvpx.vpx_codec_enc_config_set
vpx_codec_enc_config_set.restype = vpx_codec_err_t
vpx_codec_enc_config_set.argtypes = [POINTER(vpx_codec_ctx_t), POINTER(vpx_codec_enc_cfg_t)]
vpx_codec_enc_config_set.__doc__ = \
"""vpx_codec_err_t vpx_codec_enc_config_set(vpx_codec_ctx_t * ctx, unknown * cfg)
/xtra/libvpx/vpx/vpx_encoder.h:631"""



"""
Decoder
"""


vpx_codec_err_t = c_int # enum
vpx_codec_flags_t = c_long

# Config union
class N13vpx_codec_ctx3DOT_2E(Union):
    _fields_ = [
        ('dec', POINTER(vpx_codec_dec_cfg)),
        ('enc', POINTER(vpx_codec_enc_cfg)), 
        ('raw', c_void_p)
    ]

class vpx_codec_priv(Structure):
    _fields_ = []   

vpx_codec_priv_t = vpx_codec_priv




VPX_DECODER_ABI_VERSION = 3 + VPX_CODEC_ABI_VERSION

vpx_codec_dec_cfg_t = vpx_codec_dec_cfg

vpx_codec_vp9_dx_algo = (vpx_codec_iface_t).in_dll(libvpx, 'vpx_codec_vp9_dx_algo')

vpx_codec_dec_init_ver = libvpx.vpx_codec_dec_init_ver
vpx_codec_dec_init_ver.restype = vpx_codec_err_t
vpx_codec_dec_init_ver.argtypes = [POINTER(vpx_codec_ctx_t), POINTER(vpx_codec_iface_t), POINTER(vpx_codec_dec_cfg_t), vpx_codec_flags_t, c_int]
vpx_codec_dec_init_ver.__doc__ = \
"""vpx_codec_err_t vpx_codec_dec_init_ver(vpx_codec_ctx_t * ctx, vpx_codec_iface_t * iface, vpx_codec_dec_cfg_t * cfg, vpx_codec_flags_t flags, int ver)
/xtra/libvpx/vpx/vpx_decoder.h:126"""

vpx_codec_destroy = libvpx.vpx_codec_destroy
vpx_codec_destroy.restype = vpx_codec_err_t
vpx_codec_destroy.argtypes = [POINTER(vpx_codec_ctx_t)]
vpx_codec_destroy.__doc__ = \
"""vpx_codec_err_t vpx_codec_destroy(vpx_codec_ctx_t * ctx)
/xtra/libvpx/vpx/vpx_codec.h:336"""



vpx_codec_decode = libvpx.vpx_codec_decode
vpx_codec_decode.restype = vpx_codec_err_t
vpx_codec_decode.argtypes = [POINTER(vpx_codec_ctx_t), \
                             POINTER(uint8_t), \
                             c_uint, c_void_p, c_long]
vpx_codec_decode.__doc__ = \
"""vpx_codec_err_t vpx_codec_decode(vpx_codec_ctx_t * ctx, unknown * data, unsigned int data_sz, void * user_priv, long int deadline)
/xtra/libvpx/vpx/vpx_decoder.h:203"""

vpx_codec_iter_t = c_void_p
vpx_image_t = vpx_image

vpx_codec_get_frame = libvpx.vpx_codec_get_frame
vpx_codec_get_frame.restype = POINTER(vpx_image_t)
vpx_codec_get_frame.argtypes = [POINTER(vpx_codec_ctx_t), POINTER(vpx_codec_iter_t)]
vpx_codec_get_frame.__doc__ = \
"""vpx_image_t * vpx_codec_get_frame(vpx_codec_ctx_t * ctx, vpx_codec_iter_t * iter)
/xtra/libvpx/vpx/vpx_decoder.h:222"""