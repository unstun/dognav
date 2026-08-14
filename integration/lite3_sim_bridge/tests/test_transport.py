import socket
import time
import unittest

from lite3_sim_bridge.command_state import CommandLimits, LatestCommandState
from lite3_sim_bridge.protocol import (
    CommandV1,
    MessageType,
    encode_command_payload,
    encode_frame,
)
from lite3_sim_bridge.transport import (
    CommandClient,
    CommandReceiverServer,
    FrameStreamClient,
    TelemetryPublisherServer,
)


def wait_until(predicate, timeout_seconds=2.0):
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.01)
    raise AssertionError("condition did not become true")


class TransportTest(unittest.TestCase):
    def test_telemetry_publish_and_reconnect(self):
        server = TelemetryPublisherServer(port=0, io_timeout_seconds=0.05)
        server.start()
        first_client = FrameStreamClient(*server.endpoint, timeout_seconds=0.5)
        first_client.connect()
        wait_until(lambda: server.stats().accepted_connections == 1)
        first = encode_frame(MessageType.HEARTBEAT_V1, 1, 1, b"")
        self.assertTrue(server.publish(first))
        self.assertEqual(first_client.receive().header.sequence, 1)
        first_client.close()

        # The next write discovers the closed peer and clears the active slot.
        server.publish(encode_frame(MessageType.HEARTBEAT_V1, 2, 2, b""))
        second_client = FrameStreamClient(*server.endpoint, timeout_seconds=0.5)
        second_client.connect()
        wait_until(lambda: server.stats().accepted_connections == 2)
        third = encode_frame(MessageType.HEARTBEAT_V1, 3, 3, b"")
        wait_until(lambda: server.publish(third))
        self.assertEqual(second_client.receive().header.sequence, 3)
        self.assertGreaterEqual(server.stats().frames_sent, 2)
        second_client.close()
        server.stop()

    def test_command_receive_disconnect_and_reconnect(self):
        limits = CommandLimits(0.75, 0.35, 1.0)
        state = LatestCommandState(
            limits,
            timeout_ns=500_000_000,
            max_source_age_ns=500_000_000,
            max_future_skew_ns=50_000_000,
        )
        server = CommandReceiverServer(state, port=0, io_timeout_seconds=0.05)
        server.start()
        first_client = CommandClient(*server.endpoint, limits=limits, timeout_seconds=0.5)
        first_client.connect()
        sent = first_client.send_command(CommandV1(9.0, -9.0, 2.0))
        self.assertEqual(sent, CommandV1(0.75, -0.35, 1.0))
        active = wait_until(lambda: not server.snapshot().stale and server.snapshot())
        self.assertAlmostEqual(active.command.vx, sent.vx)
        self.assertAlmostEqual(active.command.vy, sent.vy)
        self.assertAlmostEqual(active.command.wz, sent.wz)
        first_client.close()
        wait_until(lambda: server.snapshot().reason == "disconnected")

        second_client = CommandClient(
            *server.endpoint,
            limits=limits,
            timeout_seconds=0.5,
            initial_sequence=first_client.sequence,
        )
        second_client.connect()
        second_client.send_command(CommandV1(0.1, 0.0, 0.0))
        reconnected = wait_until(
            lambda: server.snapshot().sequence == 2 and not server.snapshot().stale and server.snapshot()
        )
        self.assertAlmostEqual(reconnected.command.vx, 0.1)
        self.assertEqual(server.stats().reconnects, 1)
        second_client.close()
        server.stop()

    def test_command_protocol_error_fails_closed(self):
        limits = CommandLimits()
        state = LatestCommandState(limits)
        server = CommandReceiverServer(state, port=0, io_timeout_seconds=0.05)
        server.start()
        client = FrameStreamClient(*server.endpoint, timeout_seconds=0.5)
        client.connect()
        client.send(encode_frame(MessageType.STATUS_V1, 1, time.monotonic_ns(), b""))
        wait_until(lambda: server.stats().protocol_errors == 1)
        self.assertTrue(server.snapshot().stale)
        self.assertEqual(
            server.stats().last_protocol_error,
            "command stream received a non-command frame",
        )
        client.close()
        server.stop()

    def test_command_backlog_applies_only_fresh_latest_frame(self):
        limits = CommandLimits(0.75, 0.35, 1.0)
        state = LatestCommandState(
            limits,
            timeout_ns=250_000_000,
            max_source_age_ns=50_000_000,
            max_future_skew_ns=25_000_000,
        )
        server = CommandReceiverServer(state, port=0, io_timeout_seconds=0.05)
        server.start()
        client = socket.create_connection(server.endpoint, timeout=0.5)
        now_ns = time.monotonic_ns()
        frames = []
        for sequence in range(1, 6):
            timestamp_ns = now_ns if sequence == 5 else now_ns - 200_000_000
            frames.append(
                encode_frame(
                    MessageType.CMD_VEL_V1,
                    sequence,
                    timestamp_ns,
                    encode_command_payload(CommandV1(0.1 * sequence, 0.0, 0.0)),
                )
            )
        client.sendall(b"".join(frames))

        active = wait_until(
            lambda: server.snapshot().sequence == 5
            and not server.snapshot().stale
            and server.snapshot()
        )
        self.assertAlmostEqual(active.command.vx, 0.5)
        self.assertEqual(active.sequence_gaps, 0)
        self.assertEqual(active.watchdog_events, 0)
        self.assertEqual(server.stats().protocol_errors, 0)
        self.assertEqual(server.stats().coalesced_frames, 4)
        client.close()
        server.stop()


if __name__ == "__main__":
    unittest.main()
