from utils.vpx_wrap import *

from ctypes import c_size_t, c_uint16, c_uint8
from ctypes import POINTER, cast, memmove
from ctypes import c_int


class RawImage:

    def __init__(self, display_width: c_uint16, display_height: c_uint16, vpx_img: POINTER(vpx_image) = None): # type: ignore
        if vpx_img is None:
            self._vpx_img = libvpx.vpx_img_alloc(None, VPX_IMG_FMT_I420, display_width, display_height, 1)
            if not self._vpx_img:
                raise RuntimeError("RawImage: failed to allocate vpx_image")
            self._own_vpx_img = True
            self._display_width = display_width
            self._display_height = display_height
        else:
            self._vpx_img = vpx_img
            self._own_vpx_img = False
            if self._vpx_img.contents.fmt != VPX_IMG_FMT_I420:
                # Debug output for format comparison
                current_fmt = self._vpx_img.contents.fmt
                expected_fmt = VPX_IMG_FMT_I420
                print(f"Current format raw value: {current_fmt}")
                print(f"Current format type: {type(current_fmt)}")
                print(f"Expected format: {int(expected_fmt)}")
                raise RuntimeError("RawImage: only supports I420")
            self._display_width = self._vpx_img.contents.d_w
            self._display_height = self._vpx_img.contents.d_h


    def __del__(self):
        if self._own_vpx_img:
            libvpx.vpx_img_free(self._vpx_img)


    def display_width(self) -> c_uint16:
        return self._display_width


    def display_height(self) -> c_uint16:
        return self._display_height


    def y_size(self) -> c_size_t:
        return self._display_width * self._display_height


    def uv_size(self) -> c_size_t:
        return self._display_width * self._display_height // 4


    def y_plane(self):
        return cast(self._vpx_img.contents.planes[VPX_PLANE_Y], POINTER(c_uint8))


    def u_plane(self):
        return cast(self._vpx_img.contents.planes[VPX_PLANE_U], POINTER(c_uint8))


    def v_plane(self):
        return cast(self._vpx_img.contents.planes[VPX_PLANE_V], POINTER(c_uint8))


    def y_stride(self) -> c_int:
        return self._vpx_img.contents.stride[VPX_PLANE_Y]


    def u_stride(self) -> c_int:
        return self._vpx_img.contents.stride[VPX_PLANE_U]


    def v_stride(self) -> c_int:
        return self._vpx_img.contents.stride[VPX_PLANE_V]


    def copy_from_yuyv(self, src: bytes):
        if len(src) != self.y_size() * 2:
            raise RuntimeError("RawImage: invalid YUYV size")

        dst_y = self.y_plane()
        dst_u = self.u_plane()
        dst_v = self.v_plane()

        # Use ctypes.create_string_buffer to create a stable buffer
        p = (c_uint8 * len(src)).from_buffer_copy(src)

        for i in range(self.y_size()):
            dst_y[i] = (p[i * 2])

        for i in range(self._display_height // 2):
            for j in range(self._display_width // 2):
                dst_u[i * (self._display_width // 2) + j] = (p[(i * 2 * self._display_width + j * 2) * 2 + 1])
                dst_v[i * (self._display_width // 2) + j] = (p[(i * 2 * self._display_width + j * 2) * 2 + 3])


    def copy_y_from(self, src: bytes):
        if len(src) != self.y_size():
            raise RuntimeError("RawImage: invalid size for Y plane")
        
        memmove(self.y_plane(), src, len(src))


    def copy_u_from(self, src: bytes):
        if len(src) != self.uv_size():
            raise RuntimeError("RawImage: invalid size for U plane")
        
        memmove(self.u_plane(), src, len(src))


    def copy_v_from(self, src: bytes):
        if len(src) != self.uv_size():
            raise RuntimeError("RawImage: invalid size for V plane")
        
        memmove(self.v_plane(), src, len(src))


    def get_vpx_image(self):
        return self._vpx_img
