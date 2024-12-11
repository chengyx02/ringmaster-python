# Ringmaster-python

This project is a Python implementation for Ringmaster.

The original C++ code is from [ringmaster](https://github.com/microsoft/ringmaster) and [lng205/ringmaster](https://github.com/lng205/ringmaster).

## Dependencies

To run the code, you need to install the following dependencies on Linux (Ubuntu):

```bash
sudo apt install g++ libvpx-dev libsdl2-dev
```

Download the demo raw [ice_4cif_30fps.y4m](https://media.xiph.org/video/derf/y4m/ice_4cif_30fps.y4m).

## Installation

To set up the environment using `conda`:

```bash
conda create -n pyringmaster python=3.9
conda activate pyringmaster
conda install -c conda-forge gcc # Alternative
pip install -r requirements.txt
```

Alternatively, to set up the environment using `venv`:

```bash
python -m venv pyringmaster
source pyringmaster/bin/activate
pip install -r requirements.txt
```

## Usage

For video sender:
```bash
python app/video_sender.py 12345 ice_4cif_30fps.y4m
```

For video receiver:
```bash
python app/video_receiver.py 127.0.0.1 12345 704 576 --fps 30 --cbr 500
```

## Structure

utils:
- `address.py`: Manages socket addresses and provides utility functions for address manipulation.
- `conversion.py`: Contains functions for type conversion and validation.
- `exception_rim.py`: Handles custom exceptions and system call error checking.
- `file_descriptor.py`: Provides file descriptor management and I/O operations.
- `poller.py`: Implements a polling mechanism for handling multiple I/O events.
- `serialization.py`: Contains classes and functions for serializing and deserializing data.
- `socket_rim.py`: Manages socket operations, including creation, binding, and option manipulation.
- `split.py`: Provides a function to split strings based on a separator.
- `timerfd.py`: Implements timer file descriptors using ctypes.
- `timestamp.py`: Provides functions for timestamp generation.
- `udp_socket.py`: Manages UDP socket operations.
- `vpx_wrap.py`: Wraps libvpx functions and structures for video encoding and decoding.

video:
- `image.py`: Manages raw image data and provides functions for image manipulation.
- `sdl.py`: Implements video display using SDL2.
- `yuv4mpeg.py`: Handles YUV4MPEG video input and provides functions for reading video frames.

app:
- `decoder.py`: Implements the video decoder, including frame consumption and worker thread management.
- `encoder.py`: Implements the video encoder, including frame compression and packetization.
- `protocol.py`: Defines the protocol for communication, including message and datagram structures.
- `video_receiver.py`: Implements the video receiver, including argument parsing and main loop.
- `video_sender.py`: Implements the video sender, including argument parsing, frame reading, and main loop.

