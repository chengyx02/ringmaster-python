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

libvpx = ctypes.CDLL("libvpx.so")

"""
brief Allocate storage for a descriptor, using the given format
"""
libvpx.vpx_img_alloc.argtypes = [ctypes.POINTER(VpxImage), VpxImgFmt, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
libvpx.vpx_img_alloc.restype = ctypes.POINTER(VpxImage)

libvpx.vpx_img_wrap.argtypes = [ctypes.POINTER(VpxImage), VpxImgFmt, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_ubyte)]
libvpx.vpx_img_wrap.restype = ctypes.POINTER(VpxImage)

libvpx.vpx_img_set_rect.argtypes = [ctypes.POINTER(VpxImage), ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
libvpx.vpx_img_set_rect.restype = ctypes.c_int

libvpx.vpx_img_flip.argtypes = [ctypes.POINTER(VpxImage)]
libvpx.vpx_img_flip.restype = None

libvpx.vpx_img_free.argtypes = [ctypes.POINTER(VpxImage)]
libvpx.vpx_img_free.restype = None


# if __name__ == "__main__":
#     import numpy as np
#     from PIL import Image

#     # 加载图像
#     image = Image.open('photo.png').convert('YCbCr')
#     y, cb, cr = image.split()

#     # 将图像数据转换为 numpy 数组
#     y_data = np.array(y, dtype=np.uint8)
#     cb_data = np.array(cb.resize((cb.width // 2, cb.height // 2)), dtype=np.uint8)
#     cr_data = np.array(cr.resize((cr.width // 2, cr.height // 2)), dtype=np.uint8)

#     # 分配图像
#     img = libvpx.vpx_img_alloc(None, VpxImgFmt.VPX_IMG_FMT_I420, image.width, image.height, 1)
#     if img:
#         print("Image allocated successfully")

#         # 设置图像数据
#         img.contents.planes[0] = y_data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
#         img.contents.planes[1] = cb_data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
#         img.contents.planes[2] = cr_data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))

#         # 翻转图像
#         libvpx.vpx_img_flip(img)
#         print("Image flipped")

#         # 获取翻转后的图像数据
#         flipped_y_data = np.ctypeslib.as_array(img.contents.planes[0], shape=(image.height, image.width))
#         flipped_cb_data = np.ctypeslib.as_array(img.contents.planes[1], shape=(image.height // 2, image.width // 2))
#         flipped_cr_data = np.ctypeslib.as_array(img.contents.planes[2], shape=(image.height // 2, image.width // 2))

#         # 将翻转后的图像数据转换回 PIL 图像
#         flipped_y = Image.fromarray(flipped_y_data, mode='L')
#         flipped_cb = Image.fromarray(flipped_cb_data, mode='L').resize((image.width, image.height), Image.NEAREST)
#         flipped_cr = Image.fromarray(flipped_cr_data, mode='L').resize((image.width, image.height), Image.NEAREST)
#         flipped_image = Image.merge('YCbCr', (flipped_y, flipped_cb, flipped_cr)).convert('RGB')

#         # 保存或显示翻转后的图像
#         flipped_image.save('flipped_photo.png')
#         flipped_image.show()

#         # 释放图像
#         libvpx.vpx_img_free(img)
#         print("Image freed")
#     else:
#         print("Failed to allocate image")