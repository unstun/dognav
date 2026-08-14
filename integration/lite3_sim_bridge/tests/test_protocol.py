import socket
import struct
import threading
import unittest

from lite3_sim_bridge.protocol import (
    HEADER_SIZE,
    HEADER_STRUCT,
    MAX_PAYLOAD_BYTES,
    CommandV1,
    MessageType,
    ProtocolError,
    SequenceTracker,
    SensorFrameV1,
    StatusFlag,
    StatusV1,
    decode_command_payload,
    decode_frame,
    decode_header,
    decode_sensor_payload,
    decode_status_payload,
    encode_command_payload,
    encode_frame,
    encode_sensor_payload,
    encode_status_payload,
    pack_xyz_points,
    recv_frame,
    send_frame,
    unpack_xyz_points,
    xyz_f32_be_to_le,
)


class ProtocolTest(unittest.TestCase):
    def test_sequence_tracker_rejects_regression_and_counts_gaps(self):
        tracker = SequenceTracker()
        self.assertEqual(tracker.observe(4), 0)
        self.assertEqual(tracker.observe(7), 2)
        self.assertEqual(tracker.gap_count, 2)
        with self.assertRaises(ProtocolError):
            tracker.observe(7)

    def test_frame_round_trip(self):
        encoded = encode_frame(MessageType.CMD_VEL_V1, 7, 1000, b"payload")
        frame = decode_frame(encoded)
        self.assertEqual(frame.header.message_type, MessageType.CMD_VEL_V1)
        self.assertEqual(frame.header.sequence, 7)
        self.assertEqual(frame.header.timestamp_ns, 1000)
        self.assertEqual(frame.payload, b"payload")

    def test_header_rejects_magic_version_flags_reserved_and_oversize(self):
        encoded = bytearray(encode_frame(MessageType.HEARTBEAT_V1, 0, 0, b""))
        cases = []
        bad_magic = bytearray(encoded[:HEADER_SIZE])
        bad_magic[0:4] = b"BAD!"
        cases.append(bytes(bad_magic))
        bad_version = bytearray(encoded[:HEADER_SIZE])
        bad_version[4] = 2
        cases.append(bytes(bad_version))
        bad_flags = bytearray(encoded[:HEADER_SIZE])
        bad_flags[6:8] = b"\x00\x01"
        cases.append(bytes(bad_flags))
        fields = list(HEADER_STRUCT.unpack(encoded[:HEADER_SIZE]))
        fields[8] = 1
        cases.append(HEADER_STRUCT.pack(*fields))
        fields[8] = 0
        fields[5] = MAX_PAYLOAD_BYTES + 1
        cases.append(HEADER_STRUCT.pack(*fields))
        for header in cases:
            with self.subTest(header=header):
                with self.assertRaises(ProtocolError):
                    decode_header(header)

    def test_frame_rejects_truncation_trailing_bytes_and_crc_failure(self):
        encoded = encode_frame(MessageType.STATUS_V1, 2, 3, b"abc")
        with self.assertRaises(ProtocolError):
            decode_frame(encoded[:-1])
        with self.assertRaises(ProtocolError):
            decode_frame(encoded + b"extra")
        corrupted = bytearray(encoded)
        corrupted[-1] ^= 0xFF
        with self.assertRaises(ProtocolError):
            decode_frame(bytes(corrupted))

    def test_stream_handles_partial_and_coalesced_frames(self):
        sender, receiver = socket.socketpair()
        first = encode_frame(MessageType.HEARTBEAT_V1, 1, 10, b"")
        second = encode_frame(MessageType.CMD_VEL_V1, 2, 20, encode_command_payload(CommandV1(0.1, 0.2, 0.3)))
        combined = first + second

        def writer():
            for index in range(0, len(combined), 3):
                sender.sendall(combined[index : index + 3])
            sender.close()

        thread = threading.Thread(target=writer)
        thread.start()
        received_first = recv_frame(receiver)
        received_second = recv_frame(receiver)
        thread.join(timeout=1.0)
        receiver.close()
        self.assertEqual(received_first.header.sequence, 1)
        self.assertEqual(received_second.header.sequence, 2)
        self.assertAlmostEqual(decode_command_payload(received_second.payload).vy, 0.2)

    def test_send_frame_validates_before_write(self):
        sender, receiver = socket.socketpair()
        encoded = encode_frame(MessageType.HEARTBEAT_V1, 1, 2, b"")
        send_frame(sender, encoded)
        self.assertEqual(recv_frame(receiver).header.sequence, 1)
        with self.assertRaises(ProtocolError):
            send_frame(sender, encoded + b"x")
        sender.close()
        receiver.close()

    def test_sensor_payload_round_trip(self):
        point_count, point_bytes = pack_xyz_points(((1.0, 2.0, 3.0), (-1.5, 0.0, 4.5)))
        sensor = SensorFrameV1(
            body_position=(1.0, 2.0, 0.4),
            body_quaternion_xyzw=(0.0, 0.0, 0.0, 1.0),
            sensor_position=(1.1, 2.0, 0.7),
            sensor_quaternion_xyzw=(0.0, 0.0, 0.0, 1.0),
            config_sha256=b"a" * 32,
            point_count=point_count,
            points_xyz_f32_be=point_bytes,
        )
        decoded = decode_sensor_payload(encode_sensor_payload(sensor))
        self.assertEqual(decoded.body_position, sensor.body_position)
        self.assertEqual(decoded.config_sha256, sensor.config_sha256)
        self.assertEqual(unpack_xyz_points(decoded.point_count, decoded.points_xyz_f32_be), ((1.0, 2.0, 3.0), (-1.5, 0.0, 4.5)))

    def test_network_points_convert_to_explicit_little_endian_ros_bytes(self):
        _, network_bytes = pack_xyz_points(((1.0, -2.5, 3.25),))
        ros_bytes = xyz_f32_be_to_le(network_bytes)
        self.assertEqual(struct.unpack("<3f", ros_bytes), (1.0, -2.5, 3.25))
        self.assertNotEqual(network_bytes, ros_bytes)
        with self.assertRaisesRegex(ProtocolError, "four-byte aligned"):
            xyz_f32_be_to_le(b"bad")

    def test_sensor_rejects_bad_quaternion_point_length_and_nonfinite_point(self):
        count, points = pack_xyz_points(((1.0, 2.0, 3.0),))
        base = dict(
            body_position=(0.0, 0.0, 0.0),
            body_quaternion_xyzw=(0.0, 0.0, 0.0, 1.0),
            sensor_position=(0.0, 0.0, 0.0),
            sensor_quaternion_xyzw=(0.0, 0.0, 0.0, 1.0),
            config_sha256=b"b" * 32,
            point_count=count,
            points_xyz_f32_be=points,
        )
        with self.assertRaises(ProtocolError):
            encode_sensor_payload(SensorFrameV1(**dict(base, body_quaternion_xyzw=(0.0, 0.0, 0.0, 2.0))))
        with self.assertRaises(ProtocolError):
            encode_sensor_payload(SensorFrameV1(**dict(base, points_xyz_f32_be=b"")))
        with self.assertRaises(ProtocolError):
            pack_xyz_points(((float("nan"), 0.0, 0.0),))
        nan_points = struct.pack("!3f", float("nan"), 0.0, 0.0)
        with self.assertRaises(ProtocolError):
            decode_sensor_payload(
                encode_sensor_payload(SensorFrameV1(**dict(base, points_xyz_f32_be=points)))
                [:-len(points)]
                + nan_points
            )

    def test_command_payload_rejects_invalid_values_and_length(self):
        decoded = decode_command_payload(encode_command_payload(CommandV1(0.1, -0.2, 0.3)))
        self.assertAlmostEqual(decoded.vy, -0.2)
        with self.assertRaises(ProtocolError):
            encode_command_payload(CommandV1(float("inf"), 0.0, 0.0))
        with self.assertRaises(ProtocolError):
            decode_command_payload(b"short")

    def test_status_payload_round_trip_and_unknown_flag(self):
        status = StatusV1(
            physics_hz=200.0,
            policy_hz=50.0,
            sensor_hz=10.0,
            bridge_latency_ms=4.0,
            contact_count=4,
            dropped_frames=2,
            watchdog_events=1,
            flags=int(StatusFlag.CONTACT_SUPPORTED),
            termination_code=0,
        )
        self.assertEqual(decode_status_payload(encode_status_payload(status)), status)
        with self.assertRaises(ProtocolError):
            encode_status_payload(StatusV1(**dict(status.__dict__, flags=1 << 20)))


if __name__ == "__main__":
    unittest.main()
