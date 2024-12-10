#!/usr/bin/env python3
import sys
import time
from pathlib import Path
from video.sdl import VideoDisplay
from video.image import RawImage
from termcolor import colored

class YUVPlayer:
    def __init__(self, filename: str, width: int, height: int, fps: int):
        self.filename = filename
        self.width = width
        self.height = height
        self.fps = fps
        self.frame_size = width * height * 3 // 2  # YUV420 size
        self.display = VideoDisplay(width, height)
        
        # Open file
        try:
            self.file = open(filename, 'rb')
        except IOError as e:
            raise RuntimeError(f"Cannot open file: {filename}") from e
            
    def play(self):
        frame_duration = 1.0 / self.fps
        
        while True:
            frame_start = time.monotonic()
            
            # Read frame data
            frame_data = self.file.read(self.frame_size)
            if not frame_data or len(frame_data) < self.frame_size:
                break
                
            # Create frame image
            frame = RawImage(self.width, self.height)
            
            # Copy YUV planes
            y_size = self.width * self.height
            uv_size = y_size // 4
            
            frame.copy_y_from(frame_data[:y_size])
            frame.copy_u_from(frame_data[y_size:y_size + uv_size])
            frame.copy_v_from(frame_data[y_size + uv_size:])
            
            # Display frame
            self.display.show_frame(frame)
            
            # Check for quit
            if self.display.signal_quit():
                break
                
            # Maintain frame rate
            frame_end = time.monotonic()
            processing_time = frame_end - frame_start
            if processing_time < frame_duration:
                time.sleep(frame_duration - processing_time)
                
    def __del__(self):
        if hasattr(self, 'file'):
            self.file.close()

def main():
    if len(sys.argv) != 5:
        print(f"Usage: {sys.argv[0]} <yuv_file> <width> <height> <fps>", file=sys.stderr)
        return 1
        
    try:
        yuv_file = sys.argv[1]
        width = int(sys.argv[2])
        height = int(sys.argv[3])
        fps = int(sys.argv[4])
        
        if not Path(yuv_file).exists():
            raise RuntimeError(f"File not found: {yuv_file}")
            
        print(colored(f"Playing {yuv_file} ({width}x{height} @ {fps}fps)", "cyan"))
        
        player = YUVPlayer(yuv_file, width, height, fps)
        player.play()
        return 0
        
    except Exception as e:
        print(colored(f"Error: {e}", "red"), file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())