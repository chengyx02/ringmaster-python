from app.protocol import *

def example_usage():
    # Create a Datagram instance
    datagram = Datagram(
        frame_id=12345,
        frame_type=FrameType.KEY,
        frag_id=1,
        frag_cnt=1,
        payload=b"Hello, World!"
    )

    # Serialize the Datagram to a binary string
    serialized_datagram = datagram.serialize_to_string()
    print("Serialized Datagram:", serialized_datagram)

    # Parse the binary string back to a Datagram instance
    parsed_datagram = Datagram(0, FrameType.UNKNOWN, 0, 0, b"")
    if parsed_datagram.parse_from_string(serialized_datagram):
        print("Parsed Datagram:")
        print("  frame_id:", parsed_datagram.frame_id)
        print("  frame_type:", parsed_datagram.frame_type)
        print("  frag_id:", parsed_datagram.frag_id)
        print("  frag_cnt:", parsed_datagram.frag_cnt)
        print("  send_ts:", parsed_datagram.send_ts)
        print("  payload:", parsed_datagram.payload)
    else:
        print("Failed to parse Datagram")

    # Create an AckMsg instance from the parsed Datagram
    ack_msg = AckMsg(
        frame_id=parsed_datagram.frame_id,
        frag_id=parsed_datagram.frag_id,
        send_ts=parsed_datagram.send_ts
    )

    # Serialize the AckMsg to a binary string
    serialized_ack_msg = ack_msg.serialize_to_string()
    print("Serialized AckMsg:", serialized_ack_msg)

    # Parse the binary string back to an AckMsg instance
    parsed_msg = Msg.parse_from_string(serialized_ack_msg)
    if isinstance(parsed_msg, AckMsg):
        print("Parsed AckMsg:")
        print("  frame_id:", parsed_msg.frame_id)
        print("  frag_id:", parsed_msg.frag_id)
        print("  send_ts:", parsed_msg.send_ts)
    else:
        print("Failed to parse AckMsg")

    # Create a ConfigMsg instance
    config_msg = ConfigMsg(
        width=1920,
        height=1080,
        frame_rate=30,
        target_bitrate=5000000
    )

    # Serialize the ConfigMsg to a binary string
    serialized_config_msg = config_msg.serialize_to_string()
    print("Serialized ConfigMsg:", serialized_config_msg)

    # Parse the binary string back to a ConfigMsg instance
    parsed_msg = Msg.parse_from_string(serialized_config_msg)
    if isinstance(parsed_msg, ConfigMsg):
        print("Parsed ConfigMsg:")
        print("  width:", parsed_msg.width)
        print("  height:", parsed_msg.height)
        print("  frame_rate:", parsed_msg.frame_rate)
        print("  target_bitrate:", parsed_msg.target_bitrate)
    else:
        print("Failed to parse ConfigMsg")

if __name__ == "__main__":
    example_usage()