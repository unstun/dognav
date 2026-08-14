import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest

from lite3_sim_bridge.acceptance import _percentile, evaluate_acceptance


class AcceptanceTest(unittest.TestCase):
    def _thresholds(self):
        return {
            "claim": "test gate",
            "goal_world_m": [4.0, 0.0, 0.35],
            "obstacle": {"detour_x_window_m": [1.4, 2.6]},
            "thresholds": {
                "minimum_record_count": 600,
                "minimum_sim_duration_seconds": 12.0,
                "goal_xy_tolerance_m": 0.12,
                "goal_z_tolerance_m": 0.08,
                "stop_window_seconds": 2.0,
                "stop_command_max_abs": 0.05,
                "stop_planar_speed_max_mps": 0.12,
                "minimum_nonzero_command_records": 250,
                "command_component_max_abs": [0.75, 0.35, 1.0],
                "command_bound_epsilon": 0.005,
                "root_height_range_m": [0.25, 0.42],
                "maximum_step_displacement_m": 0.05,
                "minimum_supported_contact_fraction": 0.97,
                "maximum_nonfoot_contact_n": 75.0,
                "minimum_detour_abs_y_m": 0.80,
                "policy_rate_hz_range": [45.0, 55.0],
                "sensor_rate_hz_range": [8.0, 12.0],
                "minimum_cloud_nonempty_fraction": 0.99,
                "minimum_cloud_points": 10,
                "minimum_obstacle_surface_hits": 20,
                "maximum_unexpected_above_floor_hits": 0,
                "minimum_sensor_pose_displacement_m": 3.5,
                "maximum_sequence_gaps": 0,
                "maximum_watchdog_events": 0,
                "maximum_command_age_p95_ms": 100.0,
                "minimum_unique_trajectories": 2,
                "minimum_synchronized_sensor_fraction": 0.95,
                "maximum_transport_protocol_errors": 0,
                "maximum_telemetry_reconnects": 1,
                "minimum_video_frames": 250,
                "minimum_video_duration_seconds": 10.0,
                "minimum_video_bytes": 100000,
                "minimum_rosbag_bytes": 10000,
                "minimum_planner_successes": 2,
                "maximum_planner_failures": 0,
                "maximum_origin_occupancy_errors": 0,
            },
        }

    def _metrics(self):
        rows = []
        count = 620
        for index in range(count):
            fraction = index / (count - 1)
            x = 4.0 * fraction
            y = -0.95 * math.sin(math.pi * fraction)
            stopped = index >= count - 110
            rows.append(
                {
                    "sim_time_seconds": 0.02 * index,
                    "root_pos_w": [x, y, 0.31],
                    "root_lin_vel_w": [0.0 if stopped else 0.3, 0.0, 0.0],
                    "applied_command": [0.0, 0.0, 0.0]
                    if stopped
                    else [0.3, 0.0, 0.2],
                    "contact_count": 2,
                    "nonfoot_contact_max_n": 0.0,
                    "finite": True,
                    "done": False,
                    "sequence_gaps": 0,
                    "watchdog_events": 0,
                    "command_age_ms": 10.0,
                }
            )
        return rows

    def _sensor_metrics(self):
        return [
            {
                "sim_time_seconds": 0.1 * index,
                "sensor_position_w": [4.0 * index / 124, 0.0, 0.42],
                "point_count": 30,
                "obstacle_surface_hit_count": 30,
                "unexpected_above_floor_hit_count": 0,
            }
            for index in range(125)
        ]

    def _ros_summary(self):
        topic = {
            "count": 125,
            "duration_seconds": 12.4,
            "rate_hz": 10.0,
            "nonincreasing_stamp_count": 0,
        }
        return {
            "topics": {
                "body_pose": dict(topic),
                "sensor_pose": dict(topic),
                "cloud": dict(topic),
                "cmd_vel": {"count": 620, "rate_hz": 50.0},
                "bspline": {"count": 3, "rate_hz": 0.3},
            },
            "unique_trajectory_count": 3,
            "synchronized_sensor_triplet_fraction": 1.0,
            "cloud_points": {"minimum": 30, "maximum": 30, "mean": 30.0},
        }

    def _v3_thresholds(self):
        thresholds = self._thresholds()
        thresholds["v3_sensor_rig"] = {
            "canonical_urdf_sha256": "canonical",
            "isaac_urdf_sha256": "isaac",
            "lidar_frame": "mid360_scan_frame",
            "depth_frame": "d435i_depth_optical_frame",
            "expected_body_count": 24,
            "expected_joint_count": 23,
            "expected_fixed_joint_count": 11,
            "expected_movable_joint_count": 12,
            "expected_collision_count": 29,
            "runtime_mass_range_kg": [13.2817, 13.2819],
            "minimum_depth_frames": 120,
            "depth_rate_hz_range": [8.0, 12.0],
            "minimum_depth_nonempty_fraction": 0.99,
            "minimum_depth_obstacle_pixels": 20,
            "minimum_depth_pose_displacement_m": 3.5,
            "depth_dimensions": [87, 58],
            "minimum_self_occluded_lidar_hits": 1,
            "minimum_depth_artifact_count": 3,
        }
        return thresholds

    def _depth_metrics(self):
        return [
            {
                "sim_time_seconds": 0.1 * index,
                "sensor_position_w": [4.0 * index / 124, 0.0, 0.4],
                "valid_depth_pixel_count": 100,
                "nonfinite_depth_count": 0,
                "obstacle_surface_pixel_count": 30,
                "width": 87,
                "height": 58,
            }
            for index in range(125)
        ]

    def test_percentile_interpolates(self):
        self.assertAlmostEqual(_percentile([0.0, 10.0, 20.0], 0.75), 15.0)
        with self.assertRaises(ValueError):
            _percentile([], 0.5)

    def test_accepts_complete_run_and_rejects_collision(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            video = root / "run.mp4"
            video.write_bytes(b"v" * 120000)
            video_sha = hashlib.sha256(video.read_bytes()).hexdigest()
            bag = root / "rosbag"
            bag.mkdir()
            (bag / "metadata.yaml").write_text("rosbag2_bagfile_information: {}\n")
            (bag / "run_0.db3").write_bytes(b"b" * 12000)
            metrics = self._metrics()
            report = evaluate_acceptance(
                self._thresholds(),
                metrics,
                self._sensor_metrics(),
                {
                    "status": "PASS",
                    "runtime_error": None,
                    "command_transport": {"protocol_errors": 0},
                    "telemetry_transport": {"protocol_errors": 0, "reconnects": 1},
                    "video": {
                        "frame_count": 310,
                        "encoded_duration_seconds": 12.4,
                        "sha256": video_sha,
                    },
                },
                {"acceptance_config_sha256": "frozen"},
                self._ros_summary(),
                video,
                bag,
                "final_plan_success=1\nfinal_plan_success=1\n"
                "[FSM]: from EXEC_TRAJ to WAIT_TARGET\n",
                "frozen",
            )
            self.assertEqual(report["status"], "PASS")

            metrics[300]["nonfoot_contact_max_n"] = 100.0
            failed = evaluate_acceptance(
                self._thresholds(),
                metrics,
                self._sensor_metrics(),
                {
                    "status": "PASS",
                    "runtime_error": None,
                    "command_transport": {"protocol_errors": 0},
                    "telemetry_transport": {"protocol_errors": 0, "reconnects": 1},
                    "video": {
                        "frame_count": 310,
                        "encoded_duration_seconds": 12.4,
                        "sha256": video_sha,
                    },
                },
                {"acceptance_config_sha256": "frozen"},
                self._ros_summary(),
                video,
                bag,
                "final_plan_success=1\nfinal_plan_success=1\n"
                "[FSM]: from EXEC_TRAJ to WAIT_TARGET\n",
                "frozen",
            )
            self.assertEqual(failed["status"], "FAIL")
            self.assertFalse(failed["checks"]["no_collision"]["passed"])

    def test_v3_requires_asset_depth_and_runtime_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            video = root / "run.mp4"
            video.write_bytes(b"v" * 120000)
            video_sha = hashlib.sha256(video.read_bytes()).hexdigest()
            bag = root / "rosbag"
            bag.mkdir()
            (bag / "metadata.yaml").write_text("rosbag2_bagfile_information: {}\n")
            (bag / "run_0.db3").write_bytes(b"b" * 12000)
            artifacts = {}
            for name in ("depth.npy", "depth_mm.png", "depth_preview.png"):
                path = root / name
                path.write_bytes(name.encode("ascii"))
                artifacts[name] = {
                    "path": name,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            sensor_metrics = self._sensor_metrics()
            for row in sensor_metrics:
                row["self_occluded_hit_count"] = 12
            identity = {
                "acceptance_config_sha256": "frozen",
                "robot_asset": {
                    "canonical_asset_sha256": "canonical",
                    "asset_sha256": "isaac",
                },
                "sensor": {"parent_frame": "mid360_scan_frame"},
                "depth_camera": {"parent_frame": "d435i_depth_optical_frame"},
            }
            composition = {
                "runtime_body_names": [str(index) for index in range(24)],
                "imported_joint_prim_paths": [str(index) for index in range(23)],
                "imported_fixed_joint_prim_paths": [str(index) for index in range(11)],
                "imported_movable_joint_prim_paths": [str(index) for index in range(12)],
                "imported_collision_prim_paths": [str(index) for index in range(29)],
                "runtime_total_mass_kg": 13.281788,
                "silent_default_mass_check": {"status": "pass"},
            }
            report = evaluate_acceptance(
                self._v3_thresholds(),
                self._metrics(),
                sensor_metrics,
                {
                    "status": "PASS",
                    "runtime_error": None,
                    "command_transport": {"protocol_errors": 0},
                    "telemetry_transport": {"protocol_errors": 0, "reconnects": 1},
                    "video": {
                        "frame_count": 310,
                        "encoded_duration_seconds": 12.4,
                        "sha256": video_sha,
                    },
                    "depth_artifact": {"artifacts": artifacts},
                },
                identity,
                self._ros_summary(),
                video,
                bag,
                "final_plan_success=1\nfinal_plan_success=1\n"
                "[FSM]: from EXEC_TRAJ to WAIT_TARGET\n",
                "frozen",
                self._depth_metrics(),
                composition,
                root,
            )
            self.assertEqual(report["status"], "PASS")
            identity["robot_asset"]["asset_sha256"] = "wrong"
            failed = evaluate_acceptance(
                self._v3_thresholds(),
                self._metrics(),
                sensor_metrics,
                {
                    "status": "PASS",
                    "runtime_error": None,
                    "command_transport": {"protocol_errors": 0},
                    "telemetry_transport": {"protocol_errors": 0, "reconnects": 1},
                    "video": {
                        "frame_count": 310,
                        "encoded_duration_seconds": 12.4,
                        "sha256": video_sha,
                    },
                    "depth_artifact": {"artifacts": artifacts},
                },
                identity,
                self._ros_summary(),
                video,
                bag,
                "final_plan_success=1\nfinal_plan_success=1\n"
                "[FSM]: from EXEC_TRAJ to WAIT_TARGET\n",
                "frozen",
                self._depth_metrics(),
                composition,
                root,
            )
            self.assertEqual(failed["status"], "FAIL")
            self.assertFalse(failed["checks"]["v3_isaac_urdf_hash"]["passed"])


if __name__ == "__main__":
    unittest.main()
