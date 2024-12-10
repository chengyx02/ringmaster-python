from abc import ABC, abstractmethod
from .image import RawImage

"""
class VideoInput
{
public:
  VideoInput() {}
  virtual ~VideoInput() {}

  virtual uint16_t display_width() const = 0;
  virtual uint16_t display_height() const = 0;

  // read a raw frame into raw_img
  virtual bool read_frame(RawImage & raw_img) = 0;
};
"""
class VideoInput(ABC):
    def __init__(self):
        super().__init__()

    def __del__(self):
        pass

    @abstractmethod
    def display_width(self) -> int:
        pass

    @abstractmethod
    def display_height(self) -> int:
        pass

    @abstractmethod
    def read_frame(self, raw_img: RawImage) -> bool:
        pass
