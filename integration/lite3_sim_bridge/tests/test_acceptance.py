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
                "maximum_coalesced_command_frames": 100,
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
                    "terrain_height_under_root_m": 0.05 * fraction,
                    "base_clearance_m": 0.31 - 0.05 * fraction,
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
                "planner_geometry_filter_enabled": True,
                "planner_geometry_filter_ground_hit_count": 100,
                "planner_geometry_filter_obstacle_hit_count": 30,
                "planner_geometry_filter_sparse_retained_hit_count": 3,
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

    def test_forest_navigation_requires_speed_geometry_filter_and_real_detour(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            video = root / "run.mp4"
            video.write_bytes(b"v" * 120000)
            video_sha = hashlib.sha256(video.read_bytes()).hexdigest()
            bag = root / "rosbag"
            bag.mkdir()
            (bag / "metadata.yaml").write_text(
                "rosbag2_bagfile_information: {}\n"
            )
            (bag / "run_0.db3").write_bytes(b"b" * 12000)
            thresholds = self._thresholds()
            thresholds["forest_navigation"] = {
                "goal_world_m": [4.0, 0.0, 0.35],
                "obstacle_x_window_m": [1.0, 3.0],
                "minimum_filter_enabled_fraction": 1.0,
                "minimum_filtered_ground_hits_per_frame": 50,
                "minimum_filtered_obstacle_hits_per_frame": 20,
                "maximum_sparse_retained_fraction": 0.20,
                "minimum_forward_command_mps": 0.25,
                "minimum_measured_speed_p75_mps": 0.25,
                "minimum_primary_center_clearance_m": 0.60,
                "minimum_line_deviation_m": 0.80,
                "minimum_path_length_excess_m": 0.20,
                "minimum_base_clearance_m": 0.20,
                "minimum_terrain_height_range_m": 0.04,
            }
            identity = {
                "acceptance_config_sha256": "frozen",
                "forest_scene": {
                    "navigation": {
                        "start_world_m": [0.0, 0.0, 0.31],
                        "goal_world_m": [4.0, 0.0, 0.35],
                        "primary_blocker": {"center_m": [2.0, 0.0, 0.4]},
                        "required_center_clearance_m": 0.64,
                        "direct_path_intersects_inflated_blocker": True,
                    }
                },
                "sensor": {
                    "forest_geometry_filter": {
                        "enabled": True,
                        "forbidden_inputs": [
                            "terrain_height_function",
                            "scene_prim_id",
                            "proxy_bounds",
                            "obstacle_label",
                        ],
                    }
                },
            }
            report = evaluate_acceptance(
                thresholds,
                self._metrics(),
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
                identity,
                self._ros_summary(),
                video,
                bag,
                "final_plan_success=1\nfinal_plan_success=1\n"
                "[FSM]: from EXEC_TRAJ to WAIT_TARGET\n",
                "frozen",
            )
            self.assertEqual(report["status"], "PASS")
            self.assertTrue(report["checks"]["forest_planner_detour"]["passed"])

            straight_metrics = self._metrics()
            for row in straight_metrics:
                row["root_pos_w"][1] = 0.0
            failed = evaluate_acceptance(
                thresholds,
                straight_metrics,
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
                identity,
                self._ros_summary(),
                video,
                bag,
                "final_plan_success=1\nfinal_plan_success=1\n"
                "[FSM]: from EXEC_TRAJ to WAIT_TARGET\n",
                "frozen",
            )
            self.assertEqual(failed["status"], "FAIL")
            self.assertFalse(
                failed["checks"]["forest_primary_blocker_clearance"]["passed"]
            )
            self.assertFalse(failed["checks"]["forest_planner_detour"]["passed"])

    def test_v6_requires_four_layer_speed_geometry_and_trace_overlay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            video = root / "run.mp4"
            overlay = root / "overlay.mp4"
            video.write_bytes(b"v" * 120000)
            overlay.write_bytes(b"o" * 130000)
            video_sha = hashlib.sha256(video.read_bytes()).hexdigest()
            overlay_sha = hashlib.sha256(overlay.read_bytes()).hexdigest()
            bag = root / "rosbag"
            bag.mkdir()
            (bag / "metadata.yaml").write_text(
                "rosbag2_bagfile_information: {}\n"
            )
            (bag / "run_0.db3").write_bytes(b"b" * 12000)

            thresholds = self._thresholds()
            thresholds["thresholds"]["command_component_max_abs"] = [
                1.0,
                0.35,
                1.0,
            ]
            thresholds["v6_review"] = {
                "expected_course": "forest_gen_nav_v6",
                "expected_forward_limit_mps": 1.0,
                "planner_acceleration_limit_mps2": 0.5,
                "high_command_minimum_vx_mps": 0.90,
                "high_command_maximum_abs_yaw_rps": 0.15,
                "minimum_high_command_sample_count": 20,
                "minimum_high_command_measured_speed_p75_mps": 0.70,
                "minimum_rock_terrain_clearance_m": 0.01,
                "maximum_proxy_bounds_error_m": 0.005,
                "expected_proxy_render_visible": False,
                "minimum_complete_bspline_records": 2,
                "minimum_overlay_video_bytes": 100000,
                "minimum_overlay_video_frames": 250,
                "maximum_plan_pose_alignment_error_ms": 150.0,
            }
            metrics = self._metrics()
            for row in metrics[:-110]:
                row["applied_command"] = [0.95, 0.0, 0.05]
                row["root_lin_vel_w"] = [0.80, 0.0, 0.0]
            identity = {
                "acceptance_config_sha256": "frozen",
                "course": {"name": "forest_gen_nav_v6"},
                "command_limits": [1.0, 0.35, 1.0],
            }
            geometry = {
                "passed": True,
                "proxy_records": [
                    {
                        "name": "rock_proxy",
                        "kind": "Rock",
                        "source_visual_terrain_clearance_m": 0.015,
                        "proxy_bounds_max_error_m": 0.0,
                        "expected_render_visible": False,
                        "visible_geometry_prim_paths": [],
                        "render_visibility_matches": True,
                    }
                ],
            }
            trajectory_events = [
                {
                    "kind": "bspline",
                    "trajectory_id": identifier,
                    "start_time_ns": identifier,
                    "order": 1,
                    "knots": [0.0, 0.0, 1.0, 1.0],
                    "control_points": [[0.0, 0.0, 0.3], [1.0, 0.2, 0.3]],
                }
                for identifier in (1, 2)
            ]
            input_hashes = {
                "raw_video": "raw",
                "ros_events": "events",
                "metrics": "metrics",
                "run_identity": "identity",
            }
            review_metadata = {
                "input_sha256": dict(input_hashes),
                "output": {
                    "sha256": overlay_sha,
                    "bytes": overlay.stat().st_size,
                    "frame_count": 310,
                },
                "mapping": {"maximum_plan_pose_alignment_error_ms": 20.0},
            }
            report = evaluate_acceptance(
                thresholds,
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
                identity,
                self._ros_summary(),
                video,
                bag,
                "final_plan_success=1\nfinal_plan_success=1\n"
                "[FSM]: from EXEC_TRAJ to WAIT_TARGET\n",
                "frozen",
                runtime_composition={
                    "forest_scene": {"static_geometry_checks": geometry}
                },
                overlay_video_path=overlay,
                trajectory_events=trajectory_events,
                trajectory_review_metadata=review_metadata,
                trajectory_review_input_sha256=input_hashes,
                effective_input_text="max_vx=1.0\n",
                planner_config_text=(
                    "    manager.max_vel: 1.00\n"
                    "    manager.max_acc: 0.5\n"
                    "    optimization.max_vel: 1.00\n"
                ),
                controller_config_text="    max_vx: 1.00\n",
            )
            self.assertEqual(report["status"], "PASS")
            self.assertTrue(
                report["checks"]["v6_synchronized_forward_limits"]["passed"]
            )
            self.assertTrue(report["checks"]["v6_overlay_input_hashes"]["passed"])

            geometry["proxy_records"][0]["visible_geometry_prim_paths"] = [
                "/World/visible_proxy"
            ]
            failed = evaluate_acceptance(
                thresholds,
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
                identity,
                self._ros_summary(),
                video,
                bag,
                "final_plan_success=1\nfinal_plan_success=1\n"
                "[FSM]: from EXEC_TRAJ to WAIT_TARGET\n",
                "frozen",
                runtime_composition={
                    "forest_scene": {"static_geometry_checks": geometry}
                },
                overlay_video_path=overlay,
                trajectory_events=trajectory_events,
                trajectory_review_metadata=review_metadata,
                trajectory_review_input_sha256=input_hashes,
                effective_input_text="max_vx=1.0\n",
                planner_config_text=(
                    "    manager.max_vel: 1.00\n"
                    "    manager.max_acc: 0.5\n"
                    "    optimization.max_vel: 1.00\n"
                ),
                controller_config_text="    max_vx: 1.00\n",
            )
            self.assertEqual(failed["status"], "FAIL")
            self.assertFalse(
                failed["checks"]["v6_proxy_review_visibility"]["passed"]
            )


if __name__ == "__main__":
    unittest.main()
