import ctypes
import numpy as np

# 加载 libvpx 库
try:
    vpx_lib = ctypes.cdll.LoadLibrary('/usr/lib/x86_64-linux-gnu/libvpx.so')
except OSError as e:
    print(f"Error loading libvpx.so: {e}")
    raise

class RawImage:
    def __init__(self, display_width, display_height):
        self.display_width = display_width
        self.display_height = display_height
        self.y_size = display_width * display_height
        self.uv_size = display_width * display_height // 4

        # 调用 libvpx 中的函数分配图像内存
        img_format = 0  # VPX_IMG_FMT_I420
        self.vpx_img_ptr = vpx_lib.vpx_img_alloc(None, img_format, display_width, display_height, 1)
        if not self.vpx_img_ptr:
            print("Failed to allocate vpx_image. Pointer is None.")
            raise RuntimeError("Failed to allocate vpx_image.")
        else:
            print(f"Allocated image pointer: {self.vpx_img_ptr}")

            # 检查图像指针内容是否为 None
            img_ptr = ctypes.cast(self.vpx_img_ptr, ctypes.POINTER(ctypes.c_void_p))
            if not img_ptr.contents:
                print("Image pointer contents is None after allocation.")
                # 尝试再次分配图像内存
                self.vpx_img_ptr = vpx_lib.vpx_img_alloc(None, img_format, display_width, display_height, 1)
                if not self.vpx_img_ptr:
                    raise RuntimeError("Image pointer contents is None after reallocation.")
                else:
                    print(f"Reallocated image pointer: {self.vpx_img_ptr}")
                    img_ptr = ctypes.cast(self.vpx_img_ptr, ctypes.POINTER(ctypes.c_void_p))
                    if not img_ptr[0]:
                        raise RuntimeError("Image pointer contents is still None after reallocation.")

    def __del__(self):
        # 释放图像内存（如果是自己分配的）
        if self.vpx_img_ptr:
            vpx_lib.vpx_img_free(self.vpx_img_ptr)

    def get_vpx_image(self):
        return self.vpx_img_ptr

    def display_width(self):
        return self.display_width

    def display_height(self):
        return self.display_height

    def y_size(self):
        return self.display_width * self.display_height

    def uv_size(self):
        return self.display_width * self.display_height // 4

    def y_plane(self):
        img_ptr = ctypes.cast(self.vpx_img_ptr, ctypes.POINTER(ctypes.c_void_p))
        if img_ptr:
            print(f"Image pointer cast to void pointer: {img_ptr}")
            if img_ptr[0]:
                y_plane_ptr = ctypes.cast(img_ptr[0].contents.planes[0], ctypes.POINTER(ctypes.c_uint8))
                print(f"Y plane pointer: {y_plane_ptr}")
                return y_plane_ptr
            else:
                print("Image pointer contents is None.")
                raise RuntimeError("Unable to obtain Y plane pointer.")
        else:
            print("Image pointer cast to void pointer is None.")
            raise RuntimeError("Unable to obtain Y plane pointer.")

    def u_plane(self):
        img_ptr = ctypes.cast(self.vpx_img_ptr, ctypes.POINTER(ctypes.c_void_p))
        if img_ptr:
            if img_ptr[0]:
                u_plane_ptr = ctypes.cast(img_ptr[0].contents.planes[1], ctypes.POINTER(ctypes.c_uint8))
                return u_plane_ptr
            else:
                print("Image pointer contents is None.")
                raise RuntimeError("Unable to obtain U plane pointer.")
        else:
            print("Image pointer cast to void pointer is None.")
            raise RuntimeError("Unable to obtain U plane pointer.")

    def v_plane(self):
        img_ptr = ctypes.cast(self.vpx_img_ptr, ctypes.POINTER(ctypes.c_void_p))
        if img_ptr:
            if img_ptr[0]:
                v_plane_ptr = ctypes.cast(img_ptr[0].contents.planes[2], ctypes.POINTER(ctypes.c_uint8))
                return v_plane_ptr
            else:
                print("Image pointer contents is None.")
                raise RuntimeError("Unable to obtain V plane pointer.")
        else:
            print("Image pointer cast to void pointer is None.")
            raise RuntimeError("Unable to obtain V plane pointer.")

    def y_stride(self):
        img_ptr = ctypes.cast(self.vpx_img_ptr, ctypes.POINTER(ctypes.c_void_p))
        if img_ptr and img_ptr[0]:
            return img_ptr[0].contents.stride[0]
        else:
            return 0

    def u_stride(self):
        img_ptr = ctypes.cast(self.vpx_img_ptr, ctypes.POINTER(ctypes.c_void_p))
        if img_ptr and img_ptr[0]:
            return img_ptr[0].contents.stride[1]
        else:
            return 0

    def v_stride(self):
        img_ptr = ctypes.cast(self.vpx_img_ptr, ctypes.POINTER(ctypes.c_void_p))
        if img_ptr and img_ptr[0]:
            return img_ptr[0].contents.stride[2]
        else:
            return 0

    def copy_from_yuyv(self, src):
        if len(src)!= self.y_size * 2:
            raise RuntimeError("RawImage: invalid YUYV size")

        dst_y = self.y_plane()
        dst_u = self.u_plane()
        dst_v = self.v_plane()

        # copy Y plane
        p = (ctypes.c_uint8 * len(src)).from_buffer_copy(src)
        for i in range(self.y_size):
            if dst_y:
                dst_y[i] = p[i * 2]
            else:
                raise RuntimeError("Y plane pointer is None during copy.")

        # copy U and V planes
        p = (ctypes.c_uint8 * len(src)).from_buffer_copy(src)
        for i in range(self.display_height // 2):
            for j in range(self.display_width // 2):
                if dst_u and dst_v:
                    dst_u[i * (self.display_width // 2) + j] = p[(i * self.display_width + j * 2) * 2 + 1]
                    dst_v[i * (self.display_width // 2) + j] = p[(i * self.display_width + j * 2) * 2 + 3]
                else:
                    raise RuntimeError("U or V plane pointer is None during copy.")

    def copy_y_from(self, src):
        if len(src)!= self.y_size:
            raise RuntimeError("RawImage: invalid size for Y plane")
        dst_y = self.y_plane()
        for i, byte in enumerate(src):
            if dst_y:
                dst_y[i] = byte
            else:
                raise RuntimeError("Y plane pointer is None during copy.")

    def copy_u_from(self, src):
        if len(src)!= self.uv_size:
            raise RuntimeError("RawImage: invalid size for U plane")
        dst_u = self.u_plane()
        for i, byte in enumerate(src):
            if dst_u:
                dst_u[i] = byte
            else:
                raise RuntimeError("U plane pointer is None during copy.")

    def copy_v_from(self, src):
        if len(src)!= self.uv_size:
            raise RuntimeError("RawImage: invalid size for V plane")
        dst_v = self.v_plane()
        for i, byte in enumerate(src):
            if dst_v:
                dst_v[i] = byte
            else:
                raise RuntimeError("V plane pointer is None during copy.")

# 使用 RawImage 类的示例
if __name__ == "__main__":
    width = 640
    height = 480
    image = RawImage(width, height)

    # 模拟 YUYV 数据
    yuyv_data = bytearray(width * height * 2)
    # 在这里可以根据实际情况填充 yuyv_data

    try:
        image.copy_from_yuyv(yuyv_data)
    except RuntimeError as e:
        print(f"Error: {e}")

    # 模拟 Y 平面数据
    y_data = bytearray(width * height)
    # 填充 y_data
    try:
        image.copy_y_from(y_data)
    except RuntimeError as e:
        print(f"Error: {e}")

    # 模拟 U 平面数据
    u_data = bytearray(width * height // 4)
    # 填充 u_data
    try:
        image.copy_u_from(u_data)
    except RuntimeError as e:
        print(f"Error: {e}")

    # 模拟 V 平面数据
    v_data = bytearray(width * height // 4)
    # 填充 v_data
    try:
        image.copy_v_from(v_data)
    except RuntimeError as e:
        print(f"Error: {e}")