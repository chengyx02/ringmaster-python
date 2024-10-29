from abc import ABC, abstractmethod
from video.image import RawImage  # Assuming RawImage class is defined in image.py

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

# Example usage
class ExampleVideoInput(VideoInput):
    def __init__(self, width: int, height: int):
        super().__init__()
        self._width = width
        self._height = height

    def display_width(self) -> int:
        return self._width

    def display_height(self) -> int:
        return self._height

    def read_frame(self, raw_img: RawImage) -> bool:
        # Example implementation
        return True

if __name__ == "__main__":
    example_input = ExampleVideoInput(640, 480)
    print(f"Width: {example_input.display_width()}")
    print(f"Height: {example_input.display_height()}")