import os
from typing import Optional
from utils.file_descriptor import FileDescriptor  # Assuming FileDescriptor class is defined in file_descriptor.py
from video.image import RawImage  # Assuming RawImage class is defined in image.py
from video.video_input import VideoInput  # Assuming VideoInput class is defined in video_input.py
from utils.conversion import strict_stoi  # Assuming strict_stoi function is defined in conversion.py
from utils.split import split  # Assuming split function is defined in split.py

class UnixError(Exception):
    def __init__(self, tag=None):
        self.errno = os.errno
        self.strerror = os.strerror(self.errno)
        self.tag = tag
        super().__init__(self.__str__())

    def __str__(self):
        if self.tag:
            return f"{self.tag}: {self.strerror} (errno {self.errno})"
        else:
            return f"{self.strerror} (errno {self.errno})"

def check_syscall(return_value, tag=None):
    if return_value >= 0:
        return return_value
    raise UnixError(tag)

class YUV4MPEG(VideoInput):
    def __init__(self, video_file_path: str, display_width: int, display_height: int, loop: bool = True):
        self.fd = FileDescriptor(check_syscall(os.open(video_file_path, os.O_RDONLY)))
        self.display_width = display_width
        self.display_height = display_height
        self.loop = loop

        y4m_signature = "YUV4MPEG2"
        if self.fd.readn(len(y4m_signature)) != y4m_signature:
            raise RuntimeError("invalid YUV4MPEG2 file signature")

        header = self.fd.getline()
        tokens = split(header, " ")

        for token in tokens:
            if not token:
                continue

            if token[0] == 'W':  # width
                if strict_stoi(token[1:]) != display_width:
                    raise RuntimeError("wrong YUV4MPEG2 frame width")
            elif token[0] == 'H':  # height
                if strict_stoi(token[1:]) != display_height:
                    raise RuntimeError("wrong YUV4MPEG2 frame height")
            elif token[0] == 'C':  # color space
                if token[:4] != "C420":
                    raise RuntimeError("only YUV420 color space is supported")

    def frame_size(self) -> int:
        return self.display_width * self.display_height * 3 // 2

    def y_size(self) -> int:
        return self.display_width * self.display_height

    def uv_size(self) -> int:
        return self.display_width * self.display_height // 4

    def read_frame(self, raw_img: RawImage) -> bool:
        if raw_img.display_width() != self.display_width or raw_img.display_height() != self.display_height:
            raise RuntimeError("YUV4MPEG: image dimensions don't match")

        frame_header = self.fd.getline()

        if self.fd.eof() and not frame_header:
            if self.loop:
                self.fd.reset_offset()
                self.fd.getline()
                frame_header = self.fd.getline()
            else:
                return False

        if frame_header[:5] != "FRAME":
            raise RuntimeError("invalid YUV4MPEG2 input format")

        raw_img.copy_y_from(self.fd.readn(self.y_size()))
        raw_img.copy_u_from(self.fd.readn(self.uv_size()))
        raw_img.copy_v_from(self.fd.readn(self.uv_size()))

        return True

    def fd(self) -> FileDescriptor:
        return self.fd

    def display_width(self) -> int:
        return self.display_width

    def display_height(self) -> int:
        return self.display_height

# Example usage
if __name__ == "__main__":
    try:
        yuv4mpeg = YUV4MPEG("example.y4m", 640, 480)
        raw_image = RawImage(640, 480)
        while yuv4mpeg.read_frame(raw_image):
            print("Frame read successfully")
    except Exception as e:
        print(f"Error: {e}")