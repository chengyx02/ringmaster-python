#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse
import struct
from typing import Tuple

from video.yuv4mpeg import YUV4MPEG
from encoder import Encoder
from protocol import Datagram, MsgType, Msg, ConfigMsg
from utils.udp_socket import UDPSocket
from video.image import RawImage
from utils.address import Address
from utils.poller import Poller
from utils.timerfd import Timerfd, timespec
from utils.timestamp import timestamp_us

# try:
#     import debugpy; debugpy.connect(5678)
# except:
#     pass

"""
// global variables in an unnamed namespace
namespace {
  constexpr unsigned int BILLION = 1000 * 1000 * 1000;
}
"""
# Global constants
BILLION = 1000 * 1000 * 1000

"""
void print_usage(const string & program_name)
{
  cerr <<
  "Usage: " << program_name << " [options] port y4m\n\n"
  "Options:\n"
  "--mtu <MTU>                MTU for deciding UDP payload size\n"
  "-o, --output <file>        file to output performance results to\n"
  "-v, --verbose              enable more logging for debugging"
  << endl;
}
"""
def print_usage(program_name: str) -> None:
    usage_msg = f"""Usage: {program_name} [options] port y4m

Options:
    --mtu <MTU>                MTU for deciding UDP payload size
    -o, --output <file>        file to output performance results to 
    -v, --verbose              enable more logging for debugging
"""
    print(usage_msg, file=sys.stderr)


"""
pair<Address, ConfigMsg> recv_config_msg(UDPSocket & udp_sock)
{
  // wait until a valid ConfigMsg is received
  while (true) {
    const auto & [peer_addr, raw_data] = udp_sock.recvfrom();

    const shared_ptr<Msg> msg = Msg::parse_from_string(raw_data.value());
    if (msg == nullptr or msg->type != Msg::Type::CONFIG) {
      continue; // ignore invalid or non-config messages
    }

    const auto config_msg = dynamic_pointer_cast<ConfigMsg>(msg);
    if (config_msg) {
      return {peer_addr, *config_msg};
    }
  }
}
"""
def recv_config_msg(udp_sock: 'UDPSocket') -> Tuple['Address', 'ConfigMsg']:
    # wait until a valid ConfigMsg is received
    while True:
        peer_addr, raw_data = udp_sock.recvfrom()
        if not raw_data:
            continue
            
        msg = Msg.parse_from_string(raw_data)
        if msg is None or msg.type != MsgType.CONFIG:
            continue
            
        if isinstance(msg, ConfigMsg):
            return peer_addr, msg

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Video sender')
    parser.add_argument('--mtu', type=int, help='MTU for deciding UDP payload size')
    parser.add_argument('-o', '--output', help='File to output performance results to')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Enable more logging for debugging')
    parser.add_argument('port', type=int, help='Port number')
    parser.add_argument('y4m', help='YUV4MPEG input file')
    
    args = parser.parse_args()
    
    if args.mtu:
        Datagram.set_mtu(args.mtu)
    
    # Setup UDP socket
    udp_sock = UDPSocket()
    address = Address(ip="0", port=args.port)
    udp_sock.bind(address)
    print(f"Local address: {udp_sock.local_address()}", file=sys.stderr)
    
    # Wait for receiver
    print("Waiting for receiver...", file=sys.stderr)
    peer_addr, config_msg = recv_config_msg(udp_sock)
    print(f"Peer address: {peer_addr}", file=sys.stderr)
    udp_sock.connect(peer_addr)
    
    # Get config from peer
    width = config_msg.width
    height = config_msg.height
    frame_rate = config_msg.frame_rate
    target_bitrate = config_msg.target_bitrate
    
    print(f"Received config: width={width} height={height} "
          f"FPS={frame_rate} bitrate={target_bitrate}", file=sys.stderr)
    
    # set non-blocking socket
    udp_sock.set_blocking(False)
    
    # open the video file
    video_input = YUV4MPEG(args.y4m, width, height)

    # allocate a raw image
    raw_img = RawImage(width, height)

    # initialize the encoder
    encoder = Encoder(width, height, frame_rate, args.output)
    encoder.set_target_bitrate(target_bitrate)
    encoder.set_verbose(args.verbose)

    
    # setup polling
    poller = Poller()
    
    # create a periodic timer with the same period as the frame interval
    fps_timer = Timerfd()
    frame_interval = timespec()
    frame_interval.tv_sec = 0
    frame_interval.tv_nsec = int(BILLION / frame_rate)
    # Convert timespec to tuple format (sec, nsec)
    interval_tuple = (frame_interval.tv_sec, frame_interval.tv_nsec)
    fps_timer.set_time(interval_tuple, interval_tuple)
    
    # read a raw frame when the periodic timer fires
    def handle_fps_timer():
        # being lenient: read raw frames 'num_exp' times and use the last one
        num_exp = fps_timer.read_expirations()
        if num_exp > 1:
            print(f"Warning: skipping {num_exp - 1} raw frames", file=sys.stderr)
            
        for i in range(num_exp):
            # fetch a raw frame into 'raw_img' from the video input
            if not video_input.read_frame(raw_img):
                raise RuntimeError("Reached end of video input")
        
        # compress 'raw_img' into frame 'frame_id' and packetize it
        encoder.compress_frame(raw_img)
        
        # interested in socket being writable if there are datagrams to send
        if encoder.send_buf:
            poller.activate(udp_sock, Poller.Out)
    
    # when UDP socket is writable
    def handle_socket_write():
        send_buf = encoder.send_buf
        
        while send_buf:
            datagram = send_buf[0]
            # timestamp the sending time before sending
            datagram.send_ts = timestamp_us() # time.time_ns() // 1000  # microseconds
            
            if udp_sock.send(datagram.serialize_to_string()):
                if args.verbose:
                    print(f"Sent datagram: frame_id={datagram.frame_id} "
                          f"frag_id={datagram.frag_id} "
                          f"frag_cnt={datagram.frag_cnt} "
                          f"rtx={datagram.num_rtx}", file=sys.stderr)
                
                # move the sent datagram to unacked if not a retransmission
                if datagram.num_rtx == 0:
                    encoder.add_unacked(datagram)
                send_buf.popleft()
            else:   # EWOULDBLOCK; try again later
                datagram.send_ts = 0    # since it wasn't sent successfully
                break
        
        # not interested in socket being writable if no datagrams to send
        if not send_buf:
            poller.deactivate(udp_sock, Poller.Out)
    
    # when UDP socket is readable
    def handle_socket_read():

        while True:
            raw_data = udp_sock.recv()
            if not raw_data:    # EWOULDBLOCK; try again when data is available
                break
                
            msg = Msg.parse_from_string(raw_data)

            # ignore invalid or non-ACK messages
            if msg is None or msg.type != MsgType.ACK:
                continue
                
            ack = msg
            if args.verbose:
                print(f"Received ACK: frame_id={ack.frame_id} "
                      f"frag_id={ack.frag_id}", file=sys.stderr)
            
            # RTT estimation, retransmission, etc.
            encoder.handle_ack(ack)
            
            # send_buf might contain datagrams to be retransmitted now
            if encoder.send_buf:
                poller.activate(udp_sock, Poller.Out)
    
    # register events
    poller.register_event(fps_timer, Poller.In, handle_fps_timer)
    poller.register_event(udp_sock, Poller.Out, handle_socket_write) 
    poller.register_event(udp_sock, Poller.In, handle_socket_read)
    
    # create a periodic timer for outputting stats every second
    stats_timer = Timerfd()
    stats_interval = struct.pack('ll', 1, 0)  # 1 second
    stats_timer.set_time(stats_interval, stats_interval)
    
    def handle_stats():
        if stats_timer.read_expirations() == 0:
            return
        
        # output stats every second
        encoder.output_periodic_stats()
            
    poller.register_event(stats_timer, Poller.In, handle_stats)
    
    # Main loop
    while True:
        poller.poll(-1)
        
if __name__ == "__main__":
    # try:
    main()
    # except KeyboardInterrupt:
    #     sys.exit(0)