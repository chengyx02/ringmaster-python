"""
This Python code mirrors the functionality of the provided C++ code, including initializing SDL, 
creating a window, renderer, and texture, displaying a frame using the RawImage class, 
and checking for SDL quit events. 
The VideoDisplay class provides methods for managing SDL resources and displaying video frames. 
The RawImage class is assumed to be defined in image.py.
"""

import ctypes
import sdl2
from sdl2 import SDL_Init, SDL_Quit, SDL_CreateWindow, SDL_CreateRenderer, SDL_CreateTexture, SDL_DestroyTexture, SDL_DestroyRenderer, SDL_DestroyWindow, SDL_PollEvent, SDL_UpdateYUVTexture, SDL_RenderClear, SDL_RenderCopy, SDL_RenderPresent, SDL_GetError
from sdl2 import SDL_INIT_VIDEO, SDL_WINDOWPOS_UNDEFINED, SDL_WINDOW_RESIZABLE, SDL_WINDOW_OPENGL, SDL_RENDERER_ACCELERATED, SDL_RENDERER_PRESENTVSYNC, SDL_PIXELFORMAT_IYUV, SDL_TEXTUREACCESS_STREAMING, SDL_QUIT
from image import RawImage  # Assuming RawImage class is defined in image.py

class VideoDisplay:
    def __init__(self, display_width: int, display_height: int):
        self.display_width = display_width
        self.display_height = display_height

        if SDL_Init(SDL_INIT_VIDEO) != 0:
            raise RuntimeError(SDL_GetError().decode('utf-8'))

        self.window = SDL_CreateWindow(
            b"Video Display",
            SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED,
            display_width, display_height,
            SDL_WINDOW_RESIZABLE | SDL_WINDOW_OPENGL
        )

        if not self.window:
            raise RuntimeError(SDL_GetError().decode('utf-8'))

        self.renderer = SDL_CreateRenderer(
            self.window, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC
        )

        if not self.renderer:
            raise RuntimeError(SDL_GetError().decode('utf-8'))

        self.texture = SDL_CreateTexture(
            self.renderer, SDL_PIXELFORMAT_IYUV, SDL_TEXTUREACCESS_STREAMING,
            display_width, display_height
        )

        if not self.texture:
            raise RuntimeError(SDL_GetError().decode('utf-8'))

        self.event = sdl2.SDL_Event()

    def __del__(self):
        SDL_DestroyTexture(self.texture)
        SDL_DestroyRenderer(self.renderer)
        SDL_DestroyWindow(self.window)
        SDL_Quit()

    def show_frame(self, raw_img: RawImage):
        if raw_img.display_width() != self.display_width or raw_img.display_height() != self.display_height:
            raise RuntimeError("VideoDisplay: image dimensions don't match")

        SDL_UpdateYUVTexture(
            self.texture, None,
            raw_img.y_plane(), raw_img.y_stride(),
            raw_img.u_plane(), raw_img.u_stride(),
            raw_img.v_plane(), raw_img.v_stride()
        )
        SDL_RenderClear(self.renderer)
        SDL_RenderCopy(self.renderer, self.texture, None, None)
        SDL_RenderPresent(self.renderer)

    def signal_quit(self) -> bool:
        while SDL_PollEvent(ctypes.byref(self.event)):
            if self.event.type == SDL_QUIT:
                return True
        return False

# Example usage
if __name__ == "__main__":
    try:
        display = VideoDisplay(640, 480)
        raw_image = RawImage(640, 480)
        yuyv_data = b'\x00' * (640 * 480 * 2)  # Example YUYV data
        raw_image.copy_from_yuyv(yuyv_data)
        display.show_frame(raw_image)
        while not display.signal_quit():
            pass
    except Exception as e:
        print(f"Error: {e}")