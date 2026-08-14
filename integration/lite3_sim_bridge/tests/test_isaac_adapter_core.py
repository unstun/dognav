import math
import unittest

from lite3_sim_bridge.isaac_adapter_core import (
    DEFAULT_QUALIFICATION_SCHEDULE,
    assert_command_visible_in_critic,
    canonical_config_sha256,
    local_minimum_obstacle_hits,
    point_to_segment_distance_2d,
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

    def test_local_minimum_filter_removes_slope_and_keeps_tree_and_rock(self):
        slope = []
        for x_index in range(6):
            for y_index in range(3):
                x = 0.30 * x_index
                y = 0.30 * y_index
                slope.append((x, y, 0.08 * x_index + 0.02 * y_index))
        # The obstacle cell has nearby rendered ground plus taller returns.
        slope.extend(
            (
                (0.90, 0.30, 0.26),
                (0.90, 0.30, 0.55),
                (0.90, 0.30, 1.20),
            )
        )
        obstacles, stats = local_minimum_obstacle_hits(
            slope,
            (-1.0, 0.0, 1.0),
            0.1,
            5.0,
            cell_size=0.30,
            height_threshold=0.22,
        )
        self.assertIn((0.90, 0.30, 0.55), obstacles)
        self.assertIn((0.90, 0.30, 1.20), obstacles)
        self.assertNotIn((0.90, 0.30, 0.26), obstacles)
        self.assertGreater(stats["filtered_ground_hit_count"], 10)
        self.assertEqual(stats["obstacle_hit_count"], 2)

    def test_local_minimum_filter_retains_sparse_hit_conservatively(self):
        obstacles, stats = local_minimum_obstacle_hits(
            ((1.0, 1.0, 0.7), (float("nan"), 0.0, 0.0), (20.0, 0.0, 0.0)),
            (0.0, 0.0, 1.0),
            0.1,
            5.0,
            cell_size=0.30,
            height_threshold=0.22,
        )
        self.assertEqual(obstacles, ((1.0, 1.0, 0.7),))
        self.assertEqual(stats["sparse_retained_hit_count"], 1)
        self.assertEqual(stats["finite_in_range_hit_count"], 1)

    def test_local_minimum_filter_rejects_invalid_parameters(self):
        with self.assertRaisesRegex(ValueError, "cell size"):
            local_minimum_obstacle_hits(
                (), (0.0, 0.0, 1.0), 0.1, 5.0, 0.0, 0.22
            )
        with self.assertRaisesRegex(ValueError, "height threshold"):
            local_minimum_obstacle_hits(
                (), (0.0, 0.0, 1.0), 0.1, 5.0, 0.30, float("nan")
            )

    def test_point_to_segment_distance_clamps_projection(self):
        self.assertAlmostEqual(
            point_to_segment_distance_2d((0.0, 1.0), (-1.0, 0.0), (1.0, 0.0)),
            1.0,
        )
        self.assertAlmostEqual(
            point_to_segment_distance_2d((3.0, 0.0), (-1.0, 0.0), (1.0, 0.0)),
            2.0,
        )
        self.assertAlmostEqual(
            point_to_segment_distance_2d((1.0, 1.0), (0.0, 0.0), (0.0, 0.0)),
            math.sqrt(2.0),
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
