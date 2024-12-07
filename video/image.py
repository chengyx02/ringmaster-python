"""
This Python code mirrors the functionality of the provided C++ code, 
including managing a vpx_image_t structure, copying image data from a YUYV-formatted buffer, 
and copying individual planes. The RawImage class provides methods for allocating, owning, 
and managing the vpx_image_t structure, as well as copying data to the image planes. 
The vpx_image_t structure and related functions are assumed to be defined in the vpx library.
"""

import ctypes


"""
brief Current ABI version number

internal
If this file is altered in any way that changes the ABI, this value
must be bumped.  Examples include, but are not limited to, changing
types, removing or reassigning enums, adding/removing/rearranging
fields to structures
"""
VPX_IMAGE_ABI_VERSION = 5  # hideinitializer

VPX_IMG_FMT_PLANAR = 0x100       # Image is a planar format.
VPX_IMG_FMT_UV_FLIP = 0x200      # V plane precedes U in memory.
VPX_IMG_FMT_HAS_ALPHA = 0x400    # Image has an alpha channel.
VPX_IMG_FMT_HIGHBITDEPTH = 0x800 # Image uses 16bit framebuffer.

"""
brief List of supported image formats
"""
class VpxImgFmt(ctypes.c_int):
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
class VpxColorSpace(ctypes.c_int):
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
class VpxColorRange(ctypes.c_int):
    VPX_CR_STUDIO_RANGE = 0 # Y [16..235], UV [16..240]
    VPX_CR_FULL_RANGE = 1   # YUV/RGB [0..255]

"""
brief Image Descriptor
"""
class VpxImage(ctypes.Structure):
    _fields_ = [
        ("fmt", VpxImgFmt),            # Image Format
        ("cs", VpxColorSpace),         # Color Space
        ("range", VpxColorRange),      # Color Range
        ("w", ctypes.c_uint),          # Stored image width
        ("h", ctypes.c_uint),          # Stored image height
        ("bit_depth", ctypes.c_uint),  # Stored image bit-depth
        ("d_w", ctypes.c_uint),        # Displayed image width
        ("d_h", ctypes.c_uint),        # Displayed image height
        ("r_w", ctypes.c_uint),        # Intended rendering image width
        ("r_h", ctypes.c_uint),        # Intended rendering image height
        ("x_chroma_shift", ctypes.c_uint), # subsampling order, X
        ("y_chroma_shift", ctypes.c_uint), # subsampling order, Y
        ("planes", ctypes.POINTER(ctypes.c_ubyte) * 4), # pointer to the top left pixel for each plane
        ("stride", ctypes.c_int * 4),  # stride between rows for each plane
        ("bps", ctypes.c_int),         # bits per sample (for packed formats)
        ("user_priv", ctypes.c_void_p),# The following member may be set by the application to associate data with this image.
        ("img_data", ctypes.POINTER(ctypes.c_ubyte)), # private
        ("img_data_owner", ctypes.c_int), # private
        ("self_allocd", ctypes.c_int), # private
        ("fb_priv", ctypes.c_void_p),  # Frame buffer data associated with the image.
    ]

VPX_PLANE_PACKED = 0  # /**< To be used for all packed formats */
VPX_PLANE_Y = 0       # /**< Y (Luminance) plane */
VPX_PLANE_U = 1       # /**< U (Chroma) plane */
VPX_PLANE_V = 2       # /**< V (Chroma) plane */
VPX_PLANE_ALPHA = 3   # /**< A (Transparency) plane */

"""
brief Representation of a rectangle on a surface
"""
class VpxImageRect(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_uint), # leftmost column
        ("y", ctypes.c_uint), # topmost row
        ("w", ctypes.c_uint), # width
        ("h", ctypes.c_uint), # height
    ]

# Load the vpx library
"""
extern "C" {
#include <vpx/vpx_image.h>
}
"""
vpx = ctypes.CDLL('libvpx.so')

vpx.vpx_img_alloc.restype = ctypes.POINTER(VpxImage)
vpx.vpx_img_alloc.argtypes = [ctypes.POINTER(VpxImage), VpxImgFmt, ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint16]
vpx.vpx_img_free.argtypes = [ctypes.POINTER(VpxImage)]


class RawImage:
    """
    // constructor that allocates and owns the vpx_image
    RawImage::RawImage(const uint16_t display_width, const uint16_t display_height)
    : vpx_img_(vpx_img_alloc(nullptr, VPX_IMG_FMT_I420,
                            display_width, display_height, 1)),
        own_vpx_img_(true),
        display_width_(display_width),
        display_height_(display_height)
    {}

    // constructor with a non-owning pointer to vpx_image
    RawImage::RawImage(vpx_image_t * const vpx_img)
    : vpx_img_(vpx_img),
        own_vpx_img_(false),
        display_width_(),
        display_height_()
    {
        if (not vpx_img) {
            throw runtime_error("RawImage: unable to construct from a null vpx_img");
        }

        if (vpx_img->fmt != VPX_IMG_FMT_I420) {
            throw runtime_error("RawImage: only supports I420");
        }

        display_width_ = vpx_img->d_w;
        display_height_ = vpx_img->d_h;
    }
    """
    def __init__(self, display_width: ctypes.c_uint16, display_height: ctypes.c_uint16, vpx_img: ctypes.POINTER(VpxImage) = None): # type: ignore
        if vpx_img is None:
            self._vpx_img = vpx.vpx_img_alloc(None, VpxImgFmt.VPX_IMG_FMT_I420, display_width, display_height, 1)
            if not self._vpx_img:
                raise RuntimeError("RawImage: failed to allocate vpx_image")
            self._own_vpx_img = True
            self._display_width = display_width
            self._display_height = display_height
        else:
            self._vpx_img = vpx_img
            self._own_vpx_img = False
            if self._vpx_img.contents.fmt != VpxImgFmt.VPX_IMG_FMT_I420:
                raise RuntimeError("RawImage: only supports I420")
            self._display_width = self._vpx_img.contents.d_w
            self._display_height = self._vpx_img.contents.d_h

    """
    RawImage::~RawImage()
    {
        // free vpx_image only if the class owns it
        if (own_vpx_img_) {
            vpx_img_free(vpx_img_);
        }
    }
    """
    def __del__(self):
        if self._own_vpx_img:
            vpx.vpx_img_free(self._vpx_img)

    def display_width(self) -> ctypes.c_uint16:
        return self._display_width

    def display_height(self) -> ctypes.c_uint16:
        return self._display_height

    def y_size(self) -> ctypes.c_size_t:
        return self._display_width * self._display_height

    def uv_size(self) -> ctypes.c_size_t:
        return self._display_width * self._display_height // 4

    def y_plane(self):
        return ctypes.cast(self._vpx_img.contents.planes[VPX_PLANE_Y], ctypes.POINTER(ctypes.c_uint8))

    def u_plane(self):
        return ctypes.cast(self._vpx_img.contents.planes[VPX_PLANE_U], ctypes.POINTER(ctypes.c_uint8))

    def v_plane(self):
        return ctypes.cast(self._vpx_img.contents.planes[VPX_PLANE_V], ctypes.POINTER(ctypes.c_uint8))

    def y_stride(self) -> ctypes.c_int:
        return self._vpx_img.contents.stride[VPX_PLANE_Y]

    def u_stride(self) -> ctypes.c_int:
        return self._vpx_img.contents.stride[VPX_PLANE_U]

    def v_stride(self) -> ctypes.c_int:
        return self._vpx_img.contents.stride[VPX_PLANE_V]

    """
    void RawImage::copy_from_yuyv(const string_view src)
    {
        // expects YUYV to have size of 2 * W * H
        if (src.size() != y_size() * 2) {
            throw runtime_error("RawImage: invalid YUYV size");
        }

        uint8_t * dst_y = y_plane();
        uint8_t * dst_u = u_plane();
        uint8_t * dst_v = v_plane();

        // copy Y plane
        const uint8_t * p = reinterpret_cast<const uint8_t *>(src.data());
        for (unsigned i = 0; i < y_size(); i++, p += 2) {
            *dst_y++ = *p;
        }

        // copy U and V planes
        p = reinterpret_cast<const uint8_t *>(src.data());
        for (unsigned i = 0; i < display_height_ / 2; i++, p += 2 * display_width_) {
            for (unsigned j = 0; j < display_width_ / 2; j++, p += 4) {
            *dst_u++ = p[1];
            *dst_v++ = p[3];
            }
        }
    }
    """
    def copy_from_yuyv(self, src: bytes):
        if len(src) != self.y_size() * 2:
            raise RuntimeError("RawImage: invalid YUYV size")

        dst_y = self.y_plane()
        dst_u = self.u_plane()
        dst_v = self.v_plane()

        # Use ctypes.create_string_buffer to create a stable buffer
        p = (ctypes.c_uint8 * len(src)).from_buffer_copy(src)

        # y_size = self.y_size()
        # dst_y_length = self.display_width * self.display_height
        # print(f"y_size: {y_size}, length of dst_y (calculated): {dst_y_length}, len(p): {len(p)})")

        for i in range(self.y_size()):
            dst_y[i] = (p[i * 2])

        for i in range(self._display_height // 2):
            for j in range(self._display_width // 2):
                dst_u[i * (self._display_width // 2) + j] = (p[(i * 2 * self._display_width + j * 2) * 2 + 1])
                dst_v[i * (self._display_width // 2) + j] = (p[(i * 2 * self._display_width + j * 2) * 2 + 3])

    """
    void RawImage::copy_y_from(const string_view src)
    {
        if (src.size() != y_size()) {
            throw runtime_error("RawImage: invalid size for Y plane");
        }

        memcpy(y_plane(), src.data(), src.size());
    }
    """
    def copy_y_from(self, src: bytes):
        if len(src) != self.y_size():
            raise RuntimeError("RawImage: invalid size for Y plane")
        ctypes.memmove(self.y_plane(), src, len(src))

    """
    void RawImage::copy_u_from(const string_view src)
    {
        if (src.size() != uv_size()) {
            throw runtime_error("RawImage: invalid size for U plane");
        }

        memcpy(u_plane(), src.data(), src.size());
    }
    """
    def copy_u_from(self, src: bytes):
        if len(src) != self.uv_size():
            raise RuntimeError("RawImage: invalid size for U plane")
        ctypes.memmove(self.u_plane(), src, len(src))

    """
    void RawImage::copy_v_from(const string_view src)
    {
        if (src.size() != uv_size()) {
            throw runtime_error("RawImage: invalid size for V plane");
        }

        memcpy(v_plane(), src.data(), src.size());
    }
    """
    def copy_v_from(self, src: bytes):
        if len(src) != self.uv_size():
            raise RuntimeError("RawImage: invalid size for V plane")
        ctypes.memmove(self.v_plane(), src, len(src))

    """
    // return the underlying vpx_image
    vpx_image * get_vpx_image() const { return vpx_img_; }
    """
    def get_vpx_image(self):
        return self._vpx_img


# import numpy as np
# # Example usage
# raw_image = RawImage(640, 480)
# yuyv_data = b'\x00' * (640 * 480 * 3 // 2)  # Example YUYV data
# raw_image.copy_y_from(yuyv_data[:640 * 480])
# raw_image.copy_u_from(yuyv_data[640 * 480:640 * 480 + 640 * 480 // 4])
# raw_image.copy_v_from(yuyv_data[640 * 480 + 640 * 480 // 4:])

# print("YUYV data copied to RawImage")

# # Verify data integrity
# y_plane = np.ctypeslib.as_array(raw_image.y_plane(), shape=(640 * 480,))
# u_plane = np.ctypeslib.as_array(raw_image.u_plane(), shape=(640 * 480 // 4,))
# v_plane = np.ctypeslib.as_array(raw_image.v_plane(), shape=(640 * 480 // 4,))

# print(f"Y plane data length: {len(y_plane)}, expected: {640 * 480}")
# print(f"U plane data length: {len(u_plane)}, expected: {640 * 480 // 4}")
# print(f"V plane data length: {len(v_plane)}, expected: {640 * 480 // 4}")

# # Check if the data is as expected (all zeros in this example)
# if all(value == 0 for value in y_plane):
#     print("Y plane data is correct")
# else:
#     print("Y plane data is incorrect")

# if all(value == 0 for value in u_plane):
#     print("U plane data is correct")
# else:
#     print("U plane data is incorrect")

# if all(value == 0 for value in v_plane):
#     print("V plane data is correct")
# else:
#     print("V plane data is incorrect")
