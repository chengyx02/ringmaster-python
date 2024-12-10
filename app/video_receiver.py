import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse
from termcolor import colored

from protocol import Datagram, ConfigMsg, AckMsg, FrameType
from decoder import  Decoder
from utils.conversion import narrow_cast
from utils.udp_socket import UDPSocket
from utils.address import Address

# try:
#     import debugpy; debugpy.connect(5678)
# except:
#     pass

def print_usage(program_name):
    usage_msg = f"""Usage: {program_name} [options] host port width height

    Options:
        --fps <FPS>          frame rate to request from sender (default: 30)
        --cbr <bitrate>      request CBR from sender
        --lazy <level>       0: decode and display frames (default)
                            1: decode but not display frames
                            2: neither decode nor display frames
        -o, --output <file>  file to output performance results to
        -v, --verbose        enable more logging for debugging
    """
    print(usage_msg, file=sys.stderr)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Video receiver')
    parser.add_argument('host', help='Host address')
    parser.add_argument('port', type=int, help='Port number')
    parser.add_argument('width', type=int, help='Video width')
    parser.add_argument('height', type=int, help='Video height')
    parser.add_argument('--fps', type=int, default=30,
                      help='Frame rate to request from sender (default: 30)')
    parser.add_argument('--cbr', type=int, default=0,
                      help='Request CBR from sender')
    parser.add_argument('--lazy', type=int, choices=[0, 1, 2], default=0,
                      help='0: decode and display frames (default)\n'
                           '1: decode but not display frames\n'
                           '2: neither decode nor display frames')
    parser.add_argument('-o', '--output', help='File to output performance results to')
    parser.add_argument('-v', '--verbose', action='store_true',
                      help='Enable more logging for debugging')
    
    args = parser.parse_args()
    return args

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Convert arguments to appropriate types
    frame_rate = narrow_cast(int, args.fps)
    target_bitrate = args.cbr
    lazy_level = args.lazy
    output_path = args.output
    verbose = args.verbose
    
    width = narrow_cast(int, args.width)
    height = narrow_cast(int, args.height)
    port = narrow_cast(int, args.port)
    host = args.host

    peer_addr = Address(ip=host, port=port)
    print(f"Peer address: {host}:{port}", file=sys.stderr)

    # create a UDP socket and "connect" it to the peer (sender)
    udp_sock = UDPSocket()
    udp_sock.connect(peer_addr)
    print(f"Local address: {udp_sock.local_address()}", file=sys.stderr)

    # request a specific configuration
    config_msg = ConfigMsg(width, height, frame_rate, target_bitrate)
    udp_sock.send(config_msg.serialize_to_string())

    if verbose:
        # initialize decoder with debug info
        print(colored(f"\nInitializing decoder with settings:", "cyan"), file=sys.stderr)
        print(colored(f"Resolution: {width}x{height}", "cyan"), file=sys.stderr)
        print(colored(f"Lazy level: {lazy_level}", "cyan"), file=sys.stderr)
        print(colored(f"Output path: {output_path}", "cyan"), file=sys.stderr)
        print(colored(f"Verbose: {verbose}", "cyan"), file=sys.stderr)

    # initialize decoder
    decoder = Decoder(width, height, lazy_level, output_path)
    decoder.set_verbose(verbose)

    # main loop
    if verbose:
        frames_processed = 0
    while True:
        # Receive and parse datagram
        data = udp_sock.recv()
        if not data:
            continue
        
        # parse a datagram received from sender
        datagram = Datagram(0, FrameType.UNKNOWN, 0, 0, b"")
        if not datagram.parse_from_string(data):
            raise RuntimeError("Failed to parse datagram")

        # send an ACK back to sender
        ack = AckMsg(
            frame_id=datagram.frame_id, 
            frag_id=datagram.frag_id,
            send_ts=datagram.send_ts
        )
        udp_sock.send(ack.serialize_to_string())

        if verbose:
            print(f"Acked datagram: frame_id={datagram.frame_id} "
                    f"frag_id={datagram.frag_id}", file=sys.stderr)

        # process the received datagram in the decoder
        decoder.add_datagram(datagram)

        # check if the expected frame(s) is complete
        while decoder.next_frame_complete():
            if verbose:
                frames_processed += 1
                print(colored(f"Processing complete frame {frames_processed}", "green"), 
                    file=sys.stderr)
            # depending on the lazy level, might decode and display the next frame
            decoder.consume_next_frame()

        if verbose:
            print(colored(f"\nProcessed {frames_processed} frames", "cyan"), 
                file=sys.stderr)

if __name__ == "__main__":
    sys.exit(main())
