import os
from utils.file_descriptor import FileDescriptor  
from video.image import RawImage  
from video.video_input import VideoInput  
from utils.conversion import strict_stoi  
from utils.split import split
from utils.exception_rim import check_syscall

class YUV4MPEG(VideoInput):

    def __init__(self, video_file_path: str, display_width: int, display_height: int, loop: bool = True):
        self._fd = FileDescriptor(check_syscall(os.open(video_file_path, os.O_RDONLY)))
        self._display_width = display_width
        self._display_height = display_height
        self._loop = loop

        y4m_signature = "YUV4MPEG2"
        y4m_read = self._fd.readn(len(y4m_signature))
        if y4m_read.decode('utf-8') != y4m_signature:
            raise RuntimeError("invalid YUV4MPEG2 file signature")

        header = self._fd.getline()
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
        return self._display_width * self._display_height * 3 // 2


    def y_size(self) -> int:
        return self._display_width * self._display_height


    def uv_size(self) -> int:
        return self._display_width * self._display_height // 4

    
    def read_frame(self, raw_img: RawImage) -> bool:
        if raw_img.display_width() != self.display_width() or raw_img.display_height() != self.display_height():
            raise RuntimeError("YUV4MPEG: image dimensions don't match")

        frame_header = self._fd.getline()

        if self._fd.eof() and not frame_header:
            if self._loop:
                self._fd.reset_offset()
                self._fd.getline()
                frame_header = self._fd.getline()
            else:
                return False

        if frame_header[:5] != "FRAME":
            raise RuntimeError("invalid YUV4MPEG2 input format")

        raw_img.copy_y_from(self._fd.readn(self.y_size()))
        raw_img.copy_u_from(self._fd.readn(self.uv_size()))
        raw_img.copy_v_from(self._fd.readn(self.uv_size()))

        return True


    def fd(self) -> FileDescriptor:
        return self._fd


    def display_width(self) -> int:
        return self._display_width


    def display_height(self) -> int:
        return self._display_height