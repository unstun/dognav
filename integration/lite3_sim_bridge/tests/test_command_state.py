import unittest

from lite3_sim_bridge.command_state import CommandLimits, LatestCommandState
from lite3_sim_bridge.protocol import CommandV1, ProtocolError


class CommandStateTest(unittest.TestCase):
    def setUp(self):
        self.state = LatestCommandState(
            CommandLimits(max_vx=0.75, max_vy=0.35, max_wz=1.0),
            timeout_ns=250,
            max_source_age_ns=100,
            max_future_skew_ns=10,
        )

    def test_clamps_and_tracks_increasing_sequence(self):
        snapshot = self.state.update(CommandV1(9.0, -9.0, 2.0), 1, 950, 1000)
        self.assertEqual(snapshot.command, CommandV1(0.75, -0.35, 1.0))
        self.assertFalse(snapshot.stale)
        with self.assertRaises(ProtocolError):
            self.state.update(CommandV1(0.0, 0.0, 0.0), 1, 1000, 1000)

    def test_counts_sequence_gaps(self):
        self.state.update(CommandV1(0.1, 0.0, 0.0), 3, 1000, 1000)
        snapshot = self.state.update(CommandV1(0.2, 0.0, 0.0), 6, 1001, 1001)
        self.assertEqual(snapshot.sequence_gaps, 2)

    def test_rejects_stale_and_future_timestamp(self):
        with self.assertRaises(ProtocolError):
            self.state.update(CommandV1(0.0, 0.0, 0.0), 1, 899, 1000)
        with self.assertRaises(ProtocolError):
            self.state.update(CommandV1(0.0, 0.0, 0.0), 1, 1011, 1000)

    def test_batch_coalesces_stale_intermediate_but_rejects_stale_latest(self):
        active = self.state.update_batch(
            (
                (CommandV1(0.1, 0.0, 0.0), 1, 800, 1000),
                (CommandV1(0.2, 0.0, 0.0), 2, 950, 1000),
            )
        )
        self.assertEqual(active.command, CommandV1(0.2, 0.0, 0.0))
        self.assertEqual(active.sequence, 2)
        self.assertEqual(active.sequence_gaps, 0)

        with self.assertRaisesRegex(ProtocolError, "timestamp is stale"):
            self.state.update_batch(
                (
                    (CommandV1(0.3, 0.0, 0.0), 3, 950, 1100),
                    (CommandV1(0.4, 0.0, 0.0), 4, 999, 1100),
                )
            )
        self.assertEqual(self.state.snapshot(1000).sequence, 2)

    def test_batch_sequence_validation_is_atomic(self):
        self.state.update(CommandV1(0.1, 0.0, 0.0), 1, 1000, 1000)
        with self.assertRaisesRegex(ProtocolError, "sequence is not increasing"):
            self.state.update_batch(
                (
                    (CommandV1(0.2, 0.0, 0.0), 2, 1001, 1001),
                    (CommandV1(0.3, 0.0, 0.0), 2, 1002, 1002),
                )
            )
        snapshot = self.state.snapshot(1002)
        self.assertEqual(snapshot.sequence, 1)
        self.assertEqual(snapshot.sequence_gaps, 0)

    def test_watchdog_zeroes_once(self):
        self.state.update(CommandV1(0.2, 0.0, 0.0), 1, 1000, 1000)
        self.assertFalse(self.state.snapshot(1250).stale)
        expired = self.state.snapshot(1251)
        self.assertTrue(expired.stale)
        self.assertEqual(expired.command, CommandV1(0.0, 0.0, 0.0))
        self.assertEqual(expired.watchdog_events, 1)
        self.assertEqual(self.state.snapshot(2000).watchdog_events, 1)

    def test_disconnect_fails_closed(self):
        self.state.update(CommandV1(0.2, 0.0, 0.0), 1, 1000, 1000)
        disconnected = self.state.mark_disconnected()
        self.assertTrue(disconnected.stale)
        self.assertEqual(disconnected.reason, "disconnected")
        self.assertEqual(disconnected.command, CommandV1(0.0, 0.0, 0.0))
        self.assertEqual(disconnected.watchdog_events, 1)
        self.assertEqual(self.state.mark_disconnected().watchdog_events, 1)

    def test_invalid_limits_and_nonfinite_command(self):
        with self.assertRaises(ValueError):
            CommandLimits(max_vx=0.0)
        with self.assertRaises(ProtocolError):
            self.state.update(CommandV1(float("nan"), 0.0, 0.0), 1, 1000, 1000)


if __name__ == "__main__":
    unittest.main()
