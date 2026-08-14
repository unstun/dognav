from pathlib import Path
import tempfile
import unittest

from lite3_sim_bridge.run_isaac_v12_fallback import (
    _depth_gate,
    _sensor_gate,
    _urdf_contract,
)


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


class V3DepthGateTest(unittest.TestCase):
    def _records(self):
        intrinsic = [
            [50.0, 0.0, 43.0],
            [0.0, 50.0, 29.0],
            [0.0, 0.0, 1.0],
        ]
        return [
            {
                "sim_time_seconds": 0.1,
                "sensor_position_w": [0.2, 0.0, 0.45],
                "nonfinite_depth_count": 0,
                "valid_depth_pixel_count": 120,
                "obstacle_surface_pixel_count": 12,
                "intrinsic_matrix": intrinsic,
            },
            {
                "sim_time_seconds": 0.2,
                "sensor_position_w": [0.35, 0.0, 0.45],
                "nonfinite_depth_count": 0,
                "valid_depth_pixel_count": 118,
                "obstacle_surface_pixel_count": 9,
                "intrinsic_matrix": intrinsic,
            },
        ]

    def test_accepts_advancing_finite_depth_with_obstacle(self):
        checks, passed = _depth_gate(self._records())
        self.assertTrue(passed)
        self.assertTrue(checks["pose_dependent_frame"])

    def test_rejects_missing_obstacle_or_nonfinite_depth(self):
        records = self._records()
        records[0]["nonfinite_depth_count"] = 1
        records[0]["obstacle_surface_pixel_count"] = 0
        records[1]["obstacle_surface_pixel_count"] = 0
        checks, passed = _depth_gate(records)
        self.assertFalse(passed)
        self.assertFalse(checks["finite_depth"])
        self.assertFalse(checks["obstacle_returns"])

    def test_rejects_static_depth_frame(self):
        records = self._records()
        records[1]["sensor_position_w"] = records[0]["sensor_position_w"]
        checks, passed = _depth_gate(records)
        self.assertFalse(passed)
        self.assertFalse(checks["pose_dependent_frame"])


class SensorRigUrdfContractTest(unittest.TestCase):
    def test_extracts_topology_mass_collision_and_mesh_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mesh = root / "shape.stl"
            mesh.write_bytes(b"solid shape\nendsolid shape\n")
            urdf = root / "robot.urdf"
            urdf.write_text(
                """<robot name="fixture">
  <link name="base">
    <inertial><mass value="2.0"/><inertia ixx="1" ixy="0" ixz="0" iyy="1" iyz="0" izz="1"/></inertial>
    <visual><geometry><mesh filename="shape.stl"/></geometry></visual>
    <collision><geometry><box size="1 1 1"/></geometry></collision>
  </link>
  <link name="frame"/>
  <joint name="frame_joint" type="fixed"><parent link="base"/><child link="frame"/></joint>
</robot>\n""",
                encoding="utf-8",
            )
            contract = _urdf_contract(urdf)
        self.assertEqual(contract["link_count"], 2)
        self.assertEqual(contract["joint_count"], 1)
        self.assertEqual(contract["movable_joint_count"], 0)
        self.assertEqual(contract["fixed_joint_count"], 1)
        self.assertEqual(contract["collision_count"], 1)
        self.assertEqual(contract["total_declared_mass_kg"], 2.0)
        self.assertEqual(contract["links_without_inertial"], ["frame"])
        self.assertEqual(len(contract["referenced_meshes"]["shape.stl"]["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
