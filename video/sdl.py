import ctypes
import sdl2
from .image import RawImage


class VideoDisplay:

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
            self._display_width, self._display_height
        )

        if not self._texture:
            raise RuntimeError(sdl2.SDL_GetError().decode('utf-8'))

        self.event = sdl2.SDL_Event()


    def __del__(self):
        sdl2.SDL_DestroyTexture(self._texture)
        sdl2.SDL_DestroyRenderer(self._renderer)
        sdl2.SDL_DestroyWindow(self._window)
        sdl2.SDL_Quit()


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


    def signal_quit(self) -> bool:
        while sdl2.SDL_PollEvent(ctypes.byref(self.event)):
            if self.event.type == sdl2.SDL_QUIT:
                return True
        return False