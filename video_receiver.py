# Note: The Decoder class and its methods 
# (set_verbose, add_datagram, next_frame_complete, consume_next_frame) 
# are assumed to be implemented elsewhere in your Python project.
import argparse
import socket
import struct
import sys
from decoder import Datagram, Decoder

def print_usage(program_name):
    print(f"Usage: {program_name} [options] host port width height\n\n"
          "Options:\n"
          "--fps <FPS>          frame rate to request from sender (default: 30)\n"
          "--cbr <bitrate>      request CBR from sender\n"
          "--lazy <level>       0: decode and display frames (default)\n"
          "                     1: decode but not display frames\n"
          "                     2: neither decode nor display frames\n"
          "-o, --output <file>  file to output performance results to\n"
          "-v, --verbose        enable more logging for debugging")

def main():
    parser = argparse.ArgumentParser(description='Video Receiver')
    parser.add_argument('--fps', type=int, default=30, help='frame rate to request from sender (default: 30)')
    parser.add_argument('--cbr', type=int, default=500, help='request CBR from sender')
    parser.add_argument('--lazy', type=int, default=0, help='lazy level (0: decode and display, 1: decode but not display, 2: neither decode nor display)')
    parser.add_argument('-o', '--output', type=str, help='file to output performance results to')
    parser.add_argument('-v', '--verbose', action='store_true', help='enable more logging for debugging')
    parser.add_argument('host', type=str, help='host address')
    parser.add_argument('port', type=int, help='port number')
    parser.add_argument('width', type=int, help='video width')
    parser.add_argument('height', type=int, help='video height')
    args = parser.parse_args()

    frame_rate = args.fps
    target_bitrate = args.cbr
    lazy_level = args.lazy
    output_path = args.output
    verbose = args.verbose
    host = args.host
    port = args.port
    width = args.width
    height = args.height

    peer_addr = (host, port)
    print(f"Peer address: {peer_addr}")

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.connect(peer_addr)
    local_addr = udp_sock.getsockname()
    print(f"Local address: {local_addr}")

    config_msg = struct.pack('!HHHH', width, height, frame_rate, target_bitrate)
    udp_sock.send(config_msg)

    decoder = Decoder(width, height, lazy_level, output_path)
    decoder.set_verbose(verbose)

    while True:
        datagram, _ = udp_sock.recvfrom(65535)
        if not datagram:
            raise RuntimeError("failed to parse a datagram")

        ack_msg = struct.pack('!HH', datagram.frame_id, datagram.frag_id)
        udp_sock.send(ack_msg)

        if verbose:
            print(f"Acked datagram: frame_id={datagram.frame_id} frag_id={datagram.frag_id}")

        decoder.add_datagram(datagram)

        while decoder.next_frame_complete():
            decoder.consume_next_frame()

if __name__ == '__main__':
    main()