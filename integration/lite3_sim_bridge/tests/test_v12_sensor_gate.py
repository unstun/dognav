import unittest

from lite3_sim_bridge.run_isaac_v12_fallback import _sensor_gate


class V12SensorGateTest(unittest.TestCase):
    def _records(self):
        return [
            {
                "sim_time_seconds": 0.1,
                "sensor_position_w": [0.0, 0.0, 0.4],
                "point_count": 20,
                "finite_point_count": 20,
                "ground_hit_count": 10,
                "obstacle_surface_hit_count": 3,
                "centroid_sensor": [1.0, 0.0, -0.2],
            },
            {
                "sim_time_seconds": 0.2,
                "sensor_position_w": [0.2, 0.0, 0.4],
                "point_count": 18,
                "finite_point_count": 18,
                "ground_hit_count": 8,
                "obstacle_surface_hit_count": 2,
                "centroid_sensor": [0.9, 0.1, -0.2],
            },
        ]

    def test_accepts_advancing_pose_dependent_obstacle_cloud(self):
        checks, passed = _sensor_gate(self._records())
        self.assertTrue(passed)
        self.assertTrue(checks["pose_dependent_geometry"])

    def test_rejects_static_or_nonfinite_cloud(self):
        records = self._records()
        records[1]["sensor_position_w"] = records[0]["sensor_position_w"]
        records[1]["centroid_sensor"] = records[0]["centroid_sensor"]
        records[1]["finite_point_count"] = 17
        checks, passed = _sensor_gate(records)
        self.assertFalse(passed)
        self.assertFalse(checks["finite"])
        self.assertFalse(checks["pose_dependent_geometry"])

    def test_rejects_ground_only_returns(self):
        records = self._records()
        for row in records:
            row["obstacle_surface_hit_count"] = 0
        checks, passed = _sensor_gate(records)
        self.assertFalse(passed)
        self.assertFalse(checks["obstacle_returns"])


if __name__ == "__main__":
    unittest.main()
