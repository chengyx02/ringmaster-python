"""
This Python code mirrors the functionality of the provided C++ code, including initializing SDL, 
creating a window, renderer, and texture, displaying a frame using the RawImage class, 
and checking for SDL quit events. 
The VideoDisplay class provides methods for managing SDL resources and displaying video frames. 
The RawImage class is assumed to be defined in image.py.
"""

import ctypes
import sdl2
from image import RawImage

class VideoDisplay:
    """
    VideoDisplay::VideoDisplay(const uint16_t display_width,
                           const uint16_t display_height)
        : display_width_(display_width), display_height_(display_height)
    {
        if (SDL_Init(SDL_INIT_VIDEO) != 0) {
            throw runtime_error(SDL_GetError());
        }

        window_ = SDL_CreateWindow(
            "Video Display",
            SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED,
            display_width, display_height,
            SDL_WINDOW_RESIZABLE | SDL_WINDOW_OPENGL);

        if (window_ == nullptr) {
            throw runtime_error(SDL_GetError());
        }

        renderer_ = SDL_CreateRenderer(
            window_, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);

        if (renderer_ == nullptr) {
            throw runtime_error(SDL_GetError());
        }

        texture_ = SDL_CreateTexture(
            renderer_, SDL_PIXELFORMAT_IYUV, SDL_TEXTUREACCESS_STREAMING,
            display_width, display_height);

        if (texture_ == nullptr) {
            throw runtime_error(SDL_GetError());
        }

        event_ = make_unique<SDL_Event>();
    }
    """
    def __init__(self, display_width: int, display_height: int):
        self._display_width = display_width
        self._display_height = display_height
        self._window = None
        self._renderer = None
        self._texture = None

        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
            raise RuntimeError(sdl2.SDL_GetError().decode('utf-8'))

        self._window = sdl2.SDL_CreateWindow(
            b"Video Display",
            sdl2.SDL_WINDOWPOS_UNDEFINED, sdl2.SDL_WINDOWPOS_UNDEFINED,
            display_width, display_height,
            sdl2.SDL_WINDOW_RESIZABLE | sdl2.SDL_WINDOW_OPENGL
        )

        if not self._window:
            raise RuntimeError(sdl2.SDL_GetError().decode('utf-8'))

        self._renderer = sdl2.SDL_CreateRenderer(
            self._window, -1, sdl2.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC
        )

        if not self._renderer:
            raise RuntimeError(sdl2.SDL_GetError().decode('utf-8'))

        self._texture = sdl2.SDL_CreateTexture(
            self._renderer, sdl2.SDL_PIXELFORMAT_IYUV, sdl2.SDL_TEXTUREACCESS_STREAMING,
            display_width, display_height
        )

        if not self._texture:
            raise RuntimeError(sdl2.SDL_GetError().decode('utf-8'))

        self.event = sdl2.SDL_Event()

    """
    VideoDisplay::~VideoDisplay()
    {
        SDL_DestroyTexture(texture_);
        SDL_DestroyRenderer(renderer_);
        SDL_DestroyWindow(window_);
        SDL_Quit();
    }
    """
    def __del__(self):
        sdl2.SDL_DestroyTexture(self._texture)
        sdl2.SDL_DestroyRenderer(self._renderer)
        sdl2.SDL_DestroyWindow(self._window)
        sdl2.SDL_Quit()

    """
    void VideoDisplay::show_frame(const RawImage & raw_img)
    {
        if (raw_img.display_width() != display_width_ or
            raw_img.display_height() != display_height_) {
            throw runtime_error("VideoDisplay: image dimensions don't match");
        }

        SDL_UpdateYUVTexture(texture_, nullptr,
            raw_img.y_plane(), raw_img.y_stride(),
            raw_img.u_plane(), raw_img.u_stride(),
            raw_img.v_plane(), raw_img.v_stride());
        SDL_RenderClear(renderer_);
        SDL_RenderCopy(renderer_, texture_, nullptr, nullptr);
        SDL_RenderPresent(renderer_);
    }
    """
    def show_frame(self, raw_img: RawImage):
        if raw_img._display_width != self._display_width or raw_img._display_height != self._display_height:
            raise RuntimeError("VideoDisplay: image dimensions don't match")

        sdl2.SDL_UpdateYUVTexture(
            self._texture, None,
            raw_img.y_plane(), raw_img.y_stride(),
            raw_img.u_plane(), raw_img.u_stride(),
            raw_img.v_plane(), raw_img.v_stride()
        )
        sdl2.SDL_RenderClear(self._renderer)
        sdl2.SDL_RenderCopy(self._renderer, self._texture, None, None)
        sdl2.SDL_RenderPresent(self._renderer)

    """
    bool VideoDisplay::signal_quit()
    {
        while (SDL_PollEvent(event_.get())) {
            if (event_->type == SDL_QUIT) {
            return true;
            }
        }

        return false;
    }
    """
    def signal_quit(self) -> bool:
        while sdl2.SDL_PollEvent(ctypes.byref(self.event)):
            if self.event.type == sdl2.SDL_QUIT:
                return True
        return False

# Example usage
if __name__ == "__main__":

    display = VideoDisplay(640, 480)
    raw_image = RawImage(640, 480)
    # yuyv_data = b'\x00' * (640 * 480 * 2)  # Example YUYV data

    # Generate random YUYV data
    import random
    yuyv_data = bytearray()
    for _ in range(640 * 480 // 2):  # Each iteration generates 4 bytes for 2 pixels
        y1 = random.randint(0, 255)
        u = random.randint(0, 255)
        y2 = random.randint(0, 255)
        v = random.randint(0, 255)
        yuyv_data.extend([y1, u, y2, v])

    raw_image.copy_from_yuyv(yuyv_data)
    display.show_frame(raw_image)
    while not display.signal_quit():
        pass