import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from video.vpx_image import VpxImgFmt, VpxImage # type: ignore
import ctypes

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

if __name__ == "__main__":
    import numpy as np
    from PIL import Image

    # 加载图像
    image = Image.open('photo.png').convert('YCbCr')
    y, cb, cr = image.split()

    # 将图像数据转换为 numpy 数组
    y_data = np.array(y, dtype=np.uint8)
    cb_data = np.array(cb.resize((cb.width // 2, cb.height // 2)), dtype=np.uint8)
    cr_data = np.array(cr.resize((cr.width // 2, cr.height // 2)), dtype=np.uint8)

    # 分配图像
    img = libvpx.vpx_img_alloc(None, VpxImgFmt.VPX_IMG_FMT_I420, image.width, image.height, 1)
    if img:
        print("Image allocated successfully")

        # 设置图像数据
        img.contents.planes[0] = y_data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
        img.contents.planes[1] = cb_data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
        img.contents.planes[2] = cr_data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))

        # 翻转图像
        libvpx.vpx_img_flip(img)
        print("Image flipped")

        # 获取翻转后的图像数据
        flipped_y_data = np.ctypeslib.as_array(img.contents.planes[0], shape=(image.height, image.width))
        flipped_cb_data = np.ctypeslib.as_array(img.contents.planes[1], shape=(image.height // 2, image.width // 2))
        flipped_cr_data = np.ctypeslib.as_array(img.contents.planes[2], shape=(image.height // 2, image.width // 2))

        # 将翻转后的图像数据转换回 PIL 图像
        flipped_y = Image.fromarray(flipped_y_data, mode='L')
        flipped_cb = Image.fromarray(flipped_cb_data, mode='L').resize((image.width, image.height), Image.NEAREST)
        flipped_cr = Image.fromarray(flipped_cr_data, mode='L').resize((image.width, image.height), Image.NEAREST)
        flipped_image = Image.merge('YCbCr', (flipped_y, flipped_cb, flipped_cr)).convert('RGB')

        # 保存或显示翻转后的图像
        flipped_image.save('flipped_photo.png')
        flipped_image.show()

        # 释放图像
        libvpx.vpx_img_free(img)
        print("Image freed")
    else:
        print("Failed to allocate image")