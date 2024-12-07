import argparse
import os
import socket
import struct
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Optional, Tuple, Union
from video.yuv4mpeg import YUV4MPEG, RawImage
from encoder import Encoder
from utils.poller import Poller
from utils.timerfd import Timerfd


class Datagram:
    HEADER_SIZE = 16  # Example header size, adjust as needed
    max_payload = 1500 - 28 - HEADER_SIZE

    def __init__(self, frame_id: int, frame_type: int, frag_id: int, frag_cnt: int, payload: bytes):
        self.frame_id = frame_id
        self.frame_type = frame_type
        self.frag_id = frag_id
        self.frag_cnt = frag_cnt
        self.payload = payload
        self.send_ts = 0  # Placeholder for send timestamp

    @classmethod
    def set_mtu(cls, mtu: int):
        if mtu > 1500 or mtu < 512:
            raise RuntimeError("reasonable MTU is between 512 and 1500 bytes")
        cls.max_payload = mtu - 28 - cls.HEADER_SIZE

    def serialize_to_string(self) -> bytes:
        header = struct.pack('!IBHHQ', self.frame_id, self.frame_type, self.frag_id, self.frag_cnt, self.send_ts)
        return header + self.payload

class MsgType:
    ACK = 0
    CONFIG = 1

class Msg:
    def __init__(self, msg_type: int):
        self.type = msg_type

    @staticmethod
    def parse_from_string(binary: bytes) -> Optional[Union['AckMsg', 'ConfigMsg']]:
        if len(binary) < 1:
            return None

        msg_type = struct.unpack('!B', binary[0:1])[0]
        if msg_type == MsgType.ACK:
            frame_id, frag_id, send_ts = struct.unpack('!IHQ', binary[1:15])
            return AckMsg(frame_id, frag_id, send_ts)
        elif msg_type == MsgType.CONFIG:
            width, height, frame_rate, target_bitrate = struct.unpack('!HHHI', binary[1:11])
            return ConfigMsg(width, height, frame_rate, target_bitrate)
        else:
            return None

class AckMsg(Msg):
    def __init__(self, frame_id: int, frag_id: int, send_ts: int):
        super().__init__(MsgType.ACK)
        self.frame_id = frame_id
        self.frag_id = frag_id
        self.send_ts = send_ts

class ConfigMsg(Msg):
    def __init__(self, width: int, height: int, frame_rate: int, target_bitrate: int):
        super().__init__(MsgType.CONFIG)
        self.width = width
        self.height = height
        self.frame_rate = frame_rate
        self.target_bitrate = target_bitrate

def print_usage(program_name: str):
    print(f"Usage: {program_name} [options] port y4m\n\n"
          "Options:\n"
          "--mtu <MTU>                MTU for deciding UDP payload size\n"
          "-o, --output <file>        file to output performance results to\n"
          "-v, --verbose              enable more logging for debugging")

def recv_config_msg(udp_sock: socket.socket) -> Tuple[Tuple[str, int], ConfigMsg]:
    while True:
        raw_data, peer_addr = udp_sock.recvfrom(65535)
        msg = Msg.parse_from_string(raw_data)
        if msg is None or msg.type != MsgType.CONFIG:
            continue
        config_msg = msg
        return peer_addr, config_msg

def main():
    parser = argparse.ArgumentParser(description='Video Sender')
    parser.add_argument('--mtu', type=int, help='MTU for deciding UDP payload size')
    parser.add_argument('-o', '--output', type=str, help='file to output performance results to')
    parser.add_argument('-v', '--verbose', action='store_true', help='enable more logging for debugging')
    parser.add_argument('port', type=int, help='port number', default=12345)
    parser.add_argument('y4m', type=str, help='Y4M video file path', default='/home/test/CYX/streamer-ringmaster/ice_4cif_30fps.y4m')
    args = parser.parse_args()

    output_path = args.output
    verbose = args.verbose

    if args.mtu:
        Datagram.set_mtu(args.mtu)

    port = args.port
    y4m_path = args.y4m

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(('0.0.0.0', port))
    print(f"Local address: {udp_sock.getsockname()}")

    print("Waiting for receiver...")
    peer_addr, config_msg = recv_config_msg(udp_sock)
    print(f"Peer address: {peer_addr}")
    udp_sock.connect(peer_addr)

    width = config_msg.width
    height = config_msg.height
    frame_rate = config_msg.frame_rate
    target_bitrate = config_msg.target_bitrate

    print(f"Received config: width={width} height={height} FPS={frame_rate} bitrate={target_bitrate}")

    udp_sock.setblocking(False)

    # Placeholder for YUV4MPEG and RawImage classes
    video_input = YUV4MPEG(y4m_path, width, height)
    raw_img = RawImage(width, height)

    encoder = Encoder(width, height, frame_rate, output_path)
    encoder.set_target_bitrate(target_bitrate)
    encoder.set_verbose(verbose)

    poller = Poller()

    fps_timer = Timerfd()
    frame_interval = 1 / frame_rate
    fps_timer.set_time(frame_interval, frame_interval)

    poller.register_event(fps_timer, Poller.In, lambda: handle_fps_timer(fps_timer, video_input, raw_img, encoder, poller, udp_sock, verbose))

    poller.register_event(udp_sock, Poller.Out, lambda: handle_udp_out(udp_sock, encoder, poller, verbose))

    poller.register_event(udp_sock, Poller.In, lambda: handle_udp_in(udp_sock, encoder, poller, verbose))

    stats_timer = Timerfd()
    stats_interval = 1
    stats_timer.set_time(stats_interval, stats_interval)

    poller.register_event(stats_timer, Poller.In, lambda: handle_stats_timer(stats_timer, encoder))

    while True:
        poller.poll(-1)

def handle_fps_timer(fps_timer, video_input, raw_img, encoder, poller, udp_sock, verbose):
    num_exp = fps_timer.read_expirations()
    if num_exp > 1:
        print(f"Warning: skipping {num_exp - 1} raw frames")

    for _ in range(num_exp):
        if not video_input.read_frame(raw_img):
            raise RuntimeError("Reached the end of video input")

    encoder.compress_frame(raw_img)

    if not encoder.send_buf().empty():
        poller.activate(udp_sock, Poller.Out)

def handle_udp_out(udp_sock, encoder, poller, verbose):
    send_buf = encoder.send_buf()

    while send_buf:
        datagram = send_buf[0]
        datagram.send_ts = time.time()

        try:
            udp_sock.send(datagram.serialize_to_string())
            if verbose:
                print(f"Sent datagram: frame_id={datagram.frame_id} frag_id={datagram.frag_id} frag_cnt={datagram.frag_cnt} rtx={datagram.num_rtx}")

            if datagram.num_rtx == 0:
                encoder.add_unacked(datagram)

            send_buf.popleft()
        except BlockingIOError:
            datagram.send_ts = 0
            break

    if not send_buf:
        poller.deactivate(udp_sock, Poller.Out)

def handle_udp_in(udp_sock, encoder, poller, verbose):
    while True:
        try:
            raw_data = udp_sock.recv(65535)
        except BlockingIOError:
            break

        msg = Msg.parse_from_string(raw_data)
        if msg is None or msg.type != MsgType.ACK:
            return

        ack = msg

        if verbose:
            print(f"Received ACK: frame_id={ack.frame_id} frag_id={ack.frag_id}")

        encoder.handle_ack(ack)

        if not encoder.send_buf().empty():
            poller.activate(udp_sock, Poller.Out)

def handle_stats_timer(stats_timer, encoder):
    if stats_timer.read_expirations() == 0:
        return

    encoder.output_periodic_stats()

if __name__ == '__main__':
    main()