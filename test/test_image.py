#!/usr/bin/env python3
import sys
import ctypes
import sdl2
from termcolor import colored
from pathlib import Path
from video.image import RawImage

def read_yuv_file(yuv_file: str, width: int, height: int) -> bytes:
    """Read and parse YUV file."""
    print(colored(f"Reading YUV file: {yuv_file}", "cyan"))
    
    with open(yuv_file, 'rb') as f:
        # Check file header
        header = f.read(10)
        f.seek(0)
        
        y_size = width * height
        uv_size = y_size // 4
        frame_size = y_size + (2 * uv_size)
        
        if header.startswith(b'YUV4MPEG2'):
            print(colored("Detected YUV4MPEG format", "green"))
            # Skip header
            header = f.readline()
            
            # Parse header info
            header_parts = header.split()
            for part in header_parts:
                if part.startswith(b'W'):
                    file_width = int(part[1:])
                elif part.startswith(b'H'): 
                    file_height = int(part[1:])
                    
            print(colored(f"File dimensions: {file_width}x{file_height}", "cyan"))
            
            if file_width != width or file_height != height:
                raise RuntimeError(
                    f"Dimension mismatch. Expected: {width}x{height}, "
                    f"Found: {file_width}x{file_height}"
                )
            
            # Skip frame header
            frame_header = f.readline()
            if not frame_header.startswith(b'FRAME'):
                raise RuntimeError("Invalid YUV4MPEG frame header")
                
            # Read one frame
            frame_data = f.read(frame_size)
            
        else:
            print(colored("Detected raw YUV format", "green"))
            # Read just first frame
            frame_data = f.read(frame_size)
            
        if len(frame_data) != frame_size:
            raise RuntimeError(
                f"Invalid frame size. Expected {frame_size} bytes, "
                f"got {len(frame_data)}"
            )
            
        return frame_data

def display_yuv_image(yuv_file: str, width: int, height: int):
    """Display YUV image using SDL2."""
    print(colored(f"\nProcessing {yuv_file} ({width}x{height})", "cyan"))

    # Initialize SDL
    if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) < 0:
        raise RuntimeError(f"SDL initialization failed: {sdl2.SDL_GetError().decode()}")

    window = sdl2.SDL_CreateWindow(
        b"YUV Image Display",
        sdl2.SDL_WINDOWPOS_UNDEFINED,
        sdl2.SDL_WINDOWPOS_UNDEFINED,
        width,
        height,
        sdl2.SDL_WINDOW_SHOWN
    )
    
    if not window:
        sdl2.SDL_Quit()
        raise RuntimeError(f"Window creation failed: {sdl2.SDL_GetError().decode()}")

    try:
        # Read YUV file
        with open(yuv_file, 'rb') as f:
            yuv_data = read_yuv_file(yuv_file, width, height)

        # Calculate plane sizes
        y_size = width * height
        uv_size = y_size // 4
        total_size = y_size + (2 * uv_size)

        if len(yuv_data) != total_size:
            raise RuntimeError(f"Invalid file size. Expected {total_size}, got {len(yuv_data)}")

        # Create RawImage
        image = RawImage(width, height)

        # Copy YUV planes
        image.copy_y_from(yuv_data[:y_size])
        image.copy_u_from(yuv_data[y_size:y_size + uv_size])
        image.copy_v_from(yuv_data[y_size + uv_size:])

        # Create SDL renderer and texture
        renderer = sdl2.SDL_CreateRenderer(
            window, -1, 
            sdl2.SDL_RENDERER_ACCELERATED
        )
        
        texture = sdl2.SDL_CreateTexture(
            renderer,
            sdl2.SDL_PIXELFORMAT_IYUV,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            width, height
        )

        # Update texture with YUV data
        sdl2.SDL_UpdateYUVTexture(
            texture, None,
            image.y_plane(), image.y_stride(),
            image.u_plane(), image.u_stride(),
            image.v_plane(), image.v_stride()
        )

        # Render
        sdl2.SDL_RenderClear(renderer)
        sdl2.SDL_RenderCopy(renderer, texture, None, None)
        sdl2.SDL_RenderPresent(renderer)

        # Event loop
        event = sdl2.SDL_Event()
        running = True
        while running:
            while sdl2.SDL_PollEvent(ctypes.byref(event)):
                if event.type == sdl2.SDL_QUIT:
                    running = False
                elif event.type == sdl2.SDL_KEYDOWN:
                    if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                        running = False
            sdl2.SDL_Delay(100)

        # Cleanup
        sdl2.SDL_DestroyTexture(texture)
        sdl2.SDL_DestroyRenderer(renderer)

    except Exception as e:
        print(colored(f"Error: {e}", "red"), file=sys.stderr)
        raise
    finally:
        sdl2.SDL_DestroyWindow(window)
        sdl2.SDL_Quit()

def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <yuv_file> <width> <height>", file=sys.stderr)
        return 1

    # try:
    yuv_file = sys.argv[1]
    width = int(sys.argv[2])
    height = int(sys.argv[3])

    if not Path(yuv_file).exists():
        raise RuntimeError(f"File not found: {yuv_file}")

    display_yuv_image(yuv_file, width, height)
    return 0

    # except Exception as e:
    #     print(colored(f"Error: {e}", "red"), file=sys.stderr)
    #     return 1

if __name__ == "__main__":
    sys.exit(main())