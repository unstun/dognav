import math
import unittest

from lite3_sim_bridge.isaac_adapter_core import (
    DEFAULT_QUALIFICATION_SCHEDULE,
    assert_command_visible_in_critic,
    canonical_config_sha256,
    quaternion_wxyz_to_xyzw,
    rotation_matrix_from_wxyz,
    schedule_duration,
    schedule_state,
    world_hits_to_sensor_points,
)


class IsaacAdapterCoreTest(unittest.TestCase):
    def test_schedule_boundaries_and_disconnect(self):
        first, elapsed = schedule_state(0.25)
        self.assertEqual(first.name, "settle_zero")
        self.assertAlmostEqual(elapsed, 0.25)
        forward, elapsed = schedule_state(1.0)
        self.assertEqual(forward.name, "forward")
        self.assertEqual(elapsed, 0.0)
        last, _ = schedule_state(schedule_duration() + 1.0)
        self.assertEqual(last.name, "watchdog_disconnect")
        self.assertFalse(last.connected)
        self.assertGreater(schedule_duration(DEFAULT_QUALIFICATION_SCHEDULE), 8.0)

    def test_config_hash_is_canonical(self):
        left = canonical_config_sha256({"b": [2, 3], "a": 1})
        right = canonical_config_sha256({"a": 1, "b": [2, 3]})
        self.assertEqual(left, right)
        self.assertEqual(len(left), 32)

    def test_quaternion_conversion_and_rotation(self):
        xyzw = quaternion_wxyz_to_xyzw((2.0, 0.0, 0.0, 0.0))
        self.assertEqual(xyzw, (0.0, 0.0, 0.0, 1.0))
        rotation = rotation_matrix_from_wxyz(
            (math.cos(math.pi / 4), 0.0, 0.0, math.sin(math.pi / 4))
        )
        self.assertAlmostEqual(rotation[0][0], 0.0, places=6)
        self.assertAlmostEqual(rotation[1][0], 1.0, places=6)

    def test_world_hits_transform_filter_and_range(self):
        # Sensor yaw is +90 degrees. World +Y is sensor +X.
        points = world_hits_to_sensor_points(
            ((1.0, 3.0, 3.0), (float("inf"), 0.0, 0.0), (1.0, 1.99, 3.0)),
            (1.0, 2.0, 3.0),
            (math.cos(math.pi / 4), 0.0, 0.0, math.sin(math.pi / 4)),
            0.1,
            2.0,
        )
        self.assertEqual(len(points), 1)
        self.assertAlmostEqual(points[0][0], 1.0, places=6)
        self.assertAlmostEqual(points[0][1], 0.0, places=6)

    def test_world_hits_remove_declared_traversable_floor(self):
        points = world_hits_to_sensor_points(
            (
                (1.0, 0.0, 0.0),
                (1.0, 0.0, 0.05),
                (1.0, 0.0, 0.051),
            ),
            (0.0, 0.0, 1.0),
            (1.0, 0.0, 0.0, 0.0),
            0.1,
            2.0,
            minimum_world_z=0.05,
        )
        self.assertEqual(len(points), 1)
        self.assertAlmostEqual(points[0][0], 1.0, places=6)
        self.assertAlmostEqual(points[0][2], -0.949, places=6)

    def test_world_hits_reject_nonfinite_floor_threshold(self):
        with self.assertRaisesRegex(ValueError, "minimum world z"):
            world_hits_to_sensor_points(
                ((1.0, 0.0, 1.0),),
                (0.0, 0.0, 1.0),
                (1.0, 0.0, 0.0, 0.0),
                0.1,
                2.0,
                minimum_world_z=float("nan"),
            )

    def test_command_visibility(self):
        observation = [0.0] * 20
        observation[9:12] = [0.3, -0.1, 0.2]
        self.assertEqual(
            assert_command_visible_in_critic(observation, (0.3, -0.1, 0.2)),
            (0.3, -0.1, 0.2),
        )
        with self.assertRaisesRegex(ValueError, "not visible"):
            assert_command_visible_in_critic(observation, (0.2, -0.1, 0.2))


if __name__ == "__main__":
    unittest.main()
