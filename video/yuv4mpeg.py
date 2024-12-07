import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional
from utils.file_descriptor import FileDescriptor  
from video.image import RawImage  
from video.video_input import VideoInput  
from utils.conversion import strict_stoi  
from utils.split import split
from utils.exception_rim import UnixError, check_syscall

class YUV4MPEG(VideoInput):
    """
    YUV4MPEG::YUV4MPEG(const string & video_file_path,
                    const uint16_t display_width,
                    const uint16_t display_height,
                    const bool loop)
        : fd_(check_syscall(open(video_file_path.c_str(), O_RDONLY))),
            display_width_(display_width),
            display_height_(display_height),
            loop_(loop)
    {
        const string y4m_signature = "YUV4MPEG2";
        if (fd_.readn(y4m_signature.size()) != y4m_signature) {
            throw runtime_error("invalid YUV4MPEG2 file signature");
        }

        const string & header = fd_.getline();
        const vector<string> & tokens = split(header, " ");

        for (const auto & token : tokens) {
            if (token.empty()) {
            continue;
            }

            switch (token[0]) {
            case 'W': // width
                if (strict_stoi(token.substr(1)) != display_width) {
                throw runtime_error("wrong YUV4MPEG2 frame width");
                }
                break;

            case 'H': // height
                if (strict_stoi(token.substr(1)) != display_height) {
                throw runtime_error("wrong YUV4MPEG2 frame height");
                }
                break;

            case 'C': // color space
                if (token.substr(0, 4) != "C420") {
                throw runtime_error("only YUV420 color space is supported");
                }
                break;

            default:
                break;
            }
        }
    }
    """
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

    """
    size_t frame_size() const { return display_width_ * display_height_ * 3 / 2; }
    """
    def frame_size(self) -> int:
        return self._display_width * self._display_height * 3 // 2

    """
    size_t y_size() const { return display_width_ * display_height_; }
    """
    def y_size(self) -> int:
        return self._display_width * self._display_height

    """
    size_t uv_size() const { return display_width_ * display_height_ / 4; }
    """
    def uv_size(self) -> int:
        return self._display_width * self._display_height // 4

    """
    bool YUV4MPEG::read_frame(RawImage & raw_img)
    {
        if (raw_img.display_width() != display_width_ or
            raw_img.display_height() != display_height_) {
            throw runtime_error("YUV4MPEG: image dimensions don't match");
        }

        string frame_header = fd_.getline();

        if (fd_.eof() and frame_header.empty()) {
            if (loop_) {
            // reset the file offset to the beginning and skip the header line
            fd_.reset_offset();
            fd_.getline();

            // should read "FRAME" again
            frame_header = fd_.getline();
            } else {
            // cannot read past end of file if not set to the 'loop' mode
            return false;
            }
        }

        if (frame_header.substr(0, 5) != "FRAME") {
            throw runtime_error("invalid YUV4MPEG2 input format");
        }

        // read Y, U, V planes in order
        raw_img.copy_y_from(fd_.readn(y_size()));
        raw_img.copy_u_from(fd_.readn(uv_size()));
        raw_img.copy_v_from(fd_.readn(uv_size()));

        return true;
    }
    """
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

    """
    FileDescriptor & fd() { return fd_; }
    """
    def fd(self) -> FileDescriptor:
        return self._fd

    """
    uint16_t display_width() const override { return display_width_; }
    """
    def display_width(self) -> int:
        return self._display_width

    """
    uint16_t display_height() const override { return display_height_; }
    """
    def display_height(self) -> int:
        return self._display_height

# Example usage
if __name__ == "__main__":
    yuv4mpeg = YUV4MPEG("../ice_4cif_30fps.y4m", 704, 576)
    raw_image = RawImage(704, 576)

    while yuv4mpeg.read_frame(raw_image):
        # Ensure the dimensions are correct
        height = raw_image.display_height()
        width = raw_image.display_width()

        # Calculate expected sizes
        y_size = height * width
        uv_size = (height // 2) * (width // 2)

        # Log the sizes for debugging
        print(f"Frame read successfully")
        print(f"Frame dimensions: {width}x{height}")

        break