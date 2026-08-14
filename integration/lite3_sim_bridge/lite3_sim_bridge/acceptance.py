"""Evaluate a frozen SCAN-to-Lite3 physical-simulation acceptance run."""

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

from .isaac_adapter_core import point_to_segment_distance_2d


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_jsonl(path: Path) -> List[Mapping[str, object]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if not rows:
        raise ValueError(f"required JSONL is empty: {path}")
    return rows


def _percentile(values: Iterable[float], quantile: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered or not 0.0 <= quantile <= 1.0:
        raise ValueError("percentile needs values and a quantile within [0, 1]")
    index = (len(ordered) - 1) * quantile
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    fraction = index - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _rate(rows: Sequence[Mapping[str, object]]) -> float:
    duration = float(rows[-1]["sim_time_seconds"]) - float(rows[0]["sim_time_seconds"])
    return 0.0 if len(rows) < 2 or duration <= 0.0 else (len(rows) - 1) / duration


def evaluate_acceptance(
    thresholds: Mapping[str, object],
    metrics: Sequence[Mapping[str, object]],
    sensor_metrics: Sequence[Mapping[str, object]],
    isaac_report: Mapping[str, object],
    run_identity: Mapping[str, object],
    ros_summary: Mapping[str, object],
    video_path: Path,
    rosbag_dir: Path,
    foxy_log_text: str,
    threshold_sha256: str,
    depth_metrics: Sequence[Mapping[str, object]] = None,
    runtime_composition: Mapping[str, object] = None,
    depth_artifact_root: Path = None,
) -> Dict[str, object]:
    limits = thresholds["thresholds"]
    goal = thresholds["goal_world_m"]
    checks = {}

    def add(name: str, passed: bool, value, expected) -> None:
        checks[name] = {"passed": bool(passed), "value": value, "expected": expected}

    duration = float(metrics[-1]["sim_time_seconds"]) - float(
        metrics[0]["sim_time_seconds"]
    )
    final_position = [float(value) for value in metrics[-1]["root_pos_w"]]
    goal_xy_error = math.dist(final_position[:2], [float(goal[0]), float(goal[1])])
    goal_z_error = abs(final_position[2] - float(goal[2]))
    stop_start = float(metrics[-1]["sim_time_seconds"]) - float(
        limits["stop_window_seconds"]
    )
    stop_rows = [row for row in metrics if float(row["sim_time_seconds"]) >= stop_start]
    stop_command = max(
        max(abs(float(value)) for value in row["applied_command"]) for row in stop_rows
    )
    stop_speed = max(
        math.hypot(float(row["root_lin_vel_w"][0]), float(row["root_lin_vel_w"][1]))
        for row in stop_rows
    )
    command_max = [
        max(abs(float(row["applied_command"][index])) for row in metrics)
        for index in range(3)
    ]
    command_bounds = [float(value) for value in limits["command_component_max_abs"]]
    bound_epsilon = float(limits["command_bound_epsilon"])
    step_displacements = [
        math.dist(left["root_pos_w"], right["root_pos_w"])
        for left, right in zip(metrics, metrics[1:])
    ]
    support_fraction = sum(int(row["contact_count"]) >= 1 for row in metrics) / len(metrics)
    obstacle_window = thresholds["obstacle"]["detour_x_window_m"]
    near_obstacle = [
        row
        for row in metrics
        if float(obstacle_window[0])
        <= float(row["root_pos_w"][0])
        <= float(obstacle_window[1])
    ]
    detour_abs_y = (
        min(abs(float(row["root_pos_w"][1])) for row in near_obstacle)
        if near_obstacle
        else 0.0
    )
    policy_rate = _rate(metrics)
    sensor_rate = _rate(sensor_metrics)
    cloud_nonempty = sum(int(row["point_count"]) > 0 for row in sensor_metrics) / len(
        sensor_metrics
    )
    sensor_displacement = math.dist(
        sensor_metrics[0]["sensor_position_w"], sensor_metrics[-1]["sensor_position_w"]
    )
    command_age_p95 = _percentile(
        (float(row["command_age_ms"]) for row in metrics), 0.95
    )

    add("isaac_runtime_pass", isaac_report.get("status") == "PASS", isaac_report.get("status"), "PASS")
    add("isaac_runtime_error", isaac_report.get("runtime_error") is None, isaac_report.get("runtime_error"), None)
    add("record_count", len(metrics) >= int(limits["minimum_record_count"]), len(metrics), limits["minimum_record_count"])
    add("sim_duration", duration >= float(limits["minimum_sim_duration_seconds"]), duration, limits["minimum_sim_duration_seconds"])
    add("goal_xy", goal_xy_error <= float(limits["goal_xy_tolerance_m"]), goal_xy_error, limits["goal_xy_tolerance_m"])
    add("goal_z", goal_z_error <= float(limits["goal_z_tolerance_m"]), goal_z_error, limits["goal_z_tolerance_m"])
    add("stopped_command", stop_command <= float(limits["stop_command_max_abs"]), stop_command, limits["stop_command_max_abs"])
    add("stopped_motion", stop_speed <= float(limits["stop_planar_speed_max_mps"]), stop_speed, limits["stop_planar_speed_max_mps"])
    nonzero_count = sum(
        max(abs(float(value)) for value in row["applied_command"]) > 0.05
        for row in metrics
    )
    add("nonzero_commands", nonzero_count >= int(limits["minimum_nonzero_command_records"]), nonzero_count, limits["minimum_nonzero_command_records"])
    add("command_bounds", all(value <= bound + bound_epsilon for value, bound in zip(command_max, command_bounds)), command_max, command_bounds)
    add("finite_policy", all(bool(row["finite"]) for row in metrics), all(bool(row["finite"]) for row in metrics), True)
    add("no_termination", not any(bool(row["done"]) for row in metrics), any(bool(row["done"]) for row in metrics), False)
    heights = [float(row["root_pos_w"][2]) for row in metrics]
    height_range = [min(heights), max(heights)]
    expected_heights = [float(value) for value in limits["root_height_range_m"]]
    add("root_height", height_range[0] >= expected_heights[0] and height_range[1] <= expected_heights[1], height_range, expected_heights)
    max_step = max(step_displacements) if step_displacements else 0.0
    add("no_base_teleport", max_step <= float(limits["maximum_step_displacement_m"]), max_step, limits["maximum_step_displacement_m"])
    add("contact_support", support_fraction >= float(limits["minimum_supported_contact_fraction"]), support_fraction, limits["minimum_supported_contact_fraction"])
    max_nonfoot = max(float(row["nonfoot_contact_max_n"]) for row in metrics)
    add("no_collision", max_nonfoot <= float(limits["maximum_nonfoot_contact_n"]), max_nonfoot, limits["maximum_nonfoot_contact_n"])
    add("obstacle_detour", detour_abs_y >= float(limits["minimum_detour_abs_y_m"]), detour_abs_y, limits["minimum_detour_abs_y_m"])
    rate_range = [float(value) for value in limits["policy_rate_hz_range"]]
    add("policy_rate", rate_range[0] <= policy_rate <= rate_range[1], policy_rate, rate_range)
    sensor_rate_range = [float(value) for value in limits["sensor_rate_hz_range"]]
    add("sensor_rate", sensor_rate_range[0] <= sensor_rate <= sensor_rate_range[1], sensor_rate, sensor_rate_range)
    add("cloud_nonempty", cloud_nonempty >= float(limits["minimum_cloud_nonempty_fraction"]), cloud_nonempty, limits["minimum_cloud_nonempty_fraction"])
    min_points = min(int(row["point_count"]) for row in sensor_metrics)
    add("cloud_points", min_points >= int(limits["minimum_cloud_points"]), min_points, limits["minimum_cloud_points"])
    max_obstacle_hits = max(int(row["obstacle_surface_hit_count"]) for row in sensor_metrics)
    add("obstacle_returns", max_obstacle_hits >= int(limits["minimum_obstacle_surface_hits"]), max_obstacle_hits, limits["minimum_obstacle_surface_hits"])
    max_unexpected = max(int(row["unexpected_above_floor_hit_count"]) for row in sensor_metrics)
    add("unexpected_returns", max_unexpected <= int(limits["maximum_unexpected_above_floor_hits"]), max_unexpected, limits["maximum_unexpected_above_floor_hits"])
    add("pose_dependent_sensor", sensor_displacement >= float(limits["minimum_sensor_pose_displacement_m"]), sensor_displacement, limits["minimum_sensor_pose_displacement_m"])
    max_gaps = max(int(row["sequence_gaps"]) for row in metrics)
    add("sequence_gaps", max_gaps <= int(limits["maximum_sequence_gaps"]), max_gaps, limits["maximum_sequence_gaps"])
    max_watchdogs = max(int(row["watchdog_events"]) for row in metrics)
    add("watchdog_events", max_watchdogs <= int(limits["maximum_watchdog_events"]), max_watchdogs, limits["maximum_watchdog_events"])
    add("command_age_p95", command_age_p95 <= float(limits["maximum_command_age_p95_ms"]), command_age_p95, limits["maximum_command_age_p95_ms"])

    monitor_topics = ros_summary["topics"]
    for topic in ("body_pose", "sensor_pose", "cloud"):
        topic_rate = float(monitor_topics[topic]["rate_hz"])
        add(f"ros_{topic}_rate", sensor_rate_range[0] <= topic_rate <= sensor_rate_range[1], topic_rate, sensor_rate_range)
        add(f"ros_{topic}_timestamps", int(monitor_topics[topic]["nonincreasing_stamp_count"]) == 0, monitor_topics[topic]["nonincreasing_stamp_count"], 0)
    add("ros_trajectories", int(ros_summary["unique_trajectory_count"]) >= int(limits["minimum_unique_trajectories"]), ros_summary["unique_trajectory_count"], limits["minimum_unique_trajectories"])
    add("ros_sensor_sync", float(ros_summary["synchronized_sensor_triplet_fraction"]) >= float(limits["minimum_synchronized_sensor_fraction"]), ros_summary["synchronized_sensor_triplet_fraction"], limits["minimum_synchronized_sensor_fraction"])
    add("ros_cloud_points", int(ros_summary["cloud_points"]["minimum"]) >= int(limits["minimum_cloud_points"]), ros_summary["cloud_points"]["minimum"], limits["minimum_cloud_points"])

    command_transport = isaac_report["command_transport"]
    telemetry_transport = isaac_report["telemetry_transport"]
    protocol_errors = int(command_transport["protocol_errors"]) + int(telemetry_transport["protocol_errors"])
    add("transport_protocol_errors", protocol_errors <= int(limits["maximum_transport_protocol_errors"]), protocol_errors, limits["maximum_transport_protocol_errors"])
    if "maximum_coalesced_command_frames" in limits:
        coalesced_commands = int(command_transport.get("coalesced_frames", 0))
        add(
            "coalesced_command_frames",
            coalesced_commands
            <= int(limits["maximum_coalesced_command_frames"]),
            coalesced_commands,
            limits["maximum_coalesced_command_frames"],
        )
    add("telemetry_reconnects", int(telemetry_transport["reconnects"]) <= int(limits["maximum_telemetry_reconnects"]), telemetry_transport["reconnects"], limits["maximum_telemetry_reconnects"])

    video = isaac_report.get("video", {})
    add("video_regular_file", video_path.is_file(), video_path.is_file(), True)
    add("video_frames", int(video.get("frame_count", 0)) >= int(limits["minimum_video_frames"]), video.get("frame_count", 0), limits["minimum_video_frames"])
    add("video_duration", float(video.get("encoded_duration_seconds", 0.0)) >= float(limits["minimum_video_duration_seconds"]), video.get("encoded_duration_seconds", 0.0), limits["minimum_video_duration_seconds"])
    video_bytes = video_path.stat().st_size if video_path.is_file() else 0
    add("video_bytes", video_bytes >= int(limits["minimum_video_bytes"]), video_bytes, limits["minimum_video_bytes"])
    video_hash = _sha256(video_path) if video_path.is_file() else None
    add("video_hash", video_hash == video.get("sha256"), video_hash, video.get("sha256"))

    bag_metadata = rosbag_dir / "metadata.yaml"
    bag_files = list(rosbag_dir.glob("*.db3"))
    bag_bytes = sum(path.stat().st_size for path in bag_files)
    add("rosbag_metadata", bag_metadata.is_file(), bag_metadata.is_file(), True)
    add("rosbag_bytes", bag_bytes >= int(limits["minimum_rosbag_bytes"]), bag_bytes, limits["minimum_rosbag_bytes"])

    planner_successes = foxy_log_text.count("final_plan_success=1")
    planner_failures = foxy_log_text.count("final_plan_success=0")
    origin_errors = foxy_log_text.count("inside an obstacle")
    add("planner_successes", planner_successes >= int(limits["minimum_planner_successes"]), planner_successes, limits["minimum_planner_successes"])
    add("planner_failures", planner_failures <= int(limits["maximum_planner_failures"]), planner_failures, limits["maximum_planner_failures"])
    add("origin_occupancy_errors", origin_errors <= int(limits["maximum_origin_occupancy_errors"]), origin_errors, limits["maximum_origin_occupancy_errors"])
    add("planner_wait_target", "from EXEC_TRAJ to WAIT_TARGET" in foxy_log_text, "from EXEC_TRAJ to WAIT_TARGET" in foxy_log_text, True)
    add("clean_process_exit", "process has died" not in foxy_log_text and "KeyboardInterrupt" not in foxy_log_text, {"process_has_died": "process has died" in foxy_log_text, "keyboard_interrupt": "KeyboardInterrupt" in foxy_log_text}, False)
    add("threshold_identity", run_identity.get("acceptance_config_sha256") == threshold_sha256, run_identity.get("acceptance_config_sha256"), threshold_sha256)

    v3 = thresholds.get("v3_sensor_rig")
    if v3 is not None:
        depth_rows = list(depth_metrics or [])
        composition = runtime_composition or {}
        robot_asset = run_identity.get("robot_asset", {})
        add(
            "v3_canonical_urdf_hash",
            robot_asset.get("canonical_asset_sha256")
            == v3["canonical_urdf_sha256"],
            robot_asset.get("canonical_asset_sha256"),
            v3["canonical_urdf_sha256"],
        )
        add(
            "v3_isaac_urdf_hash",
            robot_asset.get("asset_sha256") == v3["isaac_urdf_sha256"],
            robot_asset.get("asset_sha256"),
            v3["isaac_urdf_sha256"],
        )
        add(
            "v3_lidar_frame",
            run_identity.get("sensor", {}).get("parent_frame")
            == v3["lidar_frame"],
            run_identity.get("sensor", {}).get("parent_frame"),
            v3["lidar_frame"],
        )
        add(
            "v3_depth_frame",
            run_identity.get("depth_camera", {}).get("parent_frame")
            == v3["depth_frame"],
            run_identity.get("depth_camera", {}).get("parent_frame"),
            v3["depth_frame"],
        )
        runtime_body_names = composition.get("runtime_body_names", [])
        runtime_joints = composition.get("imported_joint_prim_paths", [])
        runtime_fixed_joints = composition.get(
            "imported_fixed_joint_prim_paths", []
        )
        runtime_movable_joints = composition.get(
            "imported_movable_joint_prim_paths", []
        )
        runtime_collisions = composition.get("imported_collision_prim_paths", [])
        add(
            "v3_runtime_body_count",
            len(runtime_body_names) == int(v3["expected_body_count"]),
            len(runtime_body_names),
            v3["expected_body_count"],
        )
        add(
            "v3_runtime_joint_count",
            len(runtime_joints) == int(v3["expected_joint_count"]),
            len(runtime_joints),
            v3["expected_joint_count"],
        )
        add(
            "v3_runtime_fixed_joint_count",
            len(runtime_fixed_joints) == int(v3["expected_fixed_joint_count"]),
            len(runtime_fixed_joints),
            v3["expected_fixed_joint_count"],
        )
        add(
            "v3_runtime_movable_joint_count",
            len(runtime_movable_joints)
            == int(v3["expected_movable_joint_count"]),
            len(runtime_movable_joints),
            v3["expected_movable_joint_count"],
        )
        add(
            "v3_runtime_collision_count",
            len(runtime_collisions) == int(v3["expected_collision_count"]),
            len(runtime_collisions),
            v3["expected_collision_count"],
        )
        runtime_mass = composition.get("runtime_total_mass_kg")
        mass_range = [float(value) for value in v3["runtime_mass_range_kg"]]
        add(
            "v3_runtime_mass",
            runtime_mass is not None
            and mass_range[0] <= float(runtime_mass) <= mass_range[1],
            runtime_mass,
            mass_range,
        )
        add(
            "v3_no_silent_default_mass",
            composition.get("silent_default_mass_check", {}).get("status")
            == "pass",
            composition.get("silent_default_mass_check"),
            "pass",
        )
        add(
            "v3_depth_records",
            len(depth_rows) >= int(v3["minimum_depth_frames"]),
            len(depth_rows),
            v3["minimum_depth_frames"],
        )
        if depth_rows:
            depth_rate = _rate(depth_rows)
            depth_rate_range = [float(value) for value in v3["depth_rate_hz_range"]]
            depth_nonempty_fraction = sum(
                int(row["valid_depth_pixel_count"]) > 0 for row in depth_rows
            ) / len(depth_rows)
            depth_displacement = math.dist(
                depth_rows[0]["sensor_position_w"],
                depth_rows[-1]["sensor_position_w"],
            )
            add(
                "v3_depth_rate",
                depth_rate_range[0] <= depth_rate <= depth_rate_range[1],
                depth_rate,
                depth_rate_range,
            )
            add(
                "v3_depth_finite",
                all(int(row["nonfinite_depth_count"]) == 0 for row in depth_rows),
                max(int(row["nonfinite_depth_count"]) for row in depth_rows),
                0,
            )
            add(
                "v3_depth_nonempty",
                depth_nonempty_fraction
                >= float(v3["minimum_depth_nonempty_fraction"]),
                depth_nonempty_fraction,
                v3["minimum_depth_nonempty_fraction"],
            )
            depth_obstacle_pixels = max(
                int(row["obstacle_surface_pixel_count"]) for row in depth_rows
            )
            add(
                "v3_depth_obstacle",
                depth_obstacle_pixels
                >= int(v3["minimum_depth_obstacle_pixels"]),
                depth_obstacle_pixels,
                v3["minimum_depth_obstacle_pixels"],
            )
            add(
                "v3_depth_pose_dependent",
                depth_displacement
                >= float(v3["minimum_depth_pose_displacement_m"]),
                depth_displacement,
                v3["minimum_depth_pose_displacement_m"],
            )
            dimensions = [
                int(depth_rows[0]["width"]),
                int(depth_rows[0]["height"]),
            ]
            add(
                "v3_depth_dimensions",
                dimensions == list(v3["depth_dimensions"]),
                dimensions,
                v3["depth_dimensions"],
            )
        else:
            for name in (
                "v3_depth_rate",
                "v3_depth_finite",
                "v3_depth_nonempty",
                "v3_depth_obstacle",
                "v3_depth_pose_dependent",
                "v3_depth_dimensions",
            ):
                add(name, False, None, "depth metrics required")
        self_occluded = max(
            (int(row.get("self_occluded_hit_count", 0)) for row in sensor_metrics),
            default=0,
        )
        add(
            "v3_lidar_self_occlusion",
            self_occluded >= int(v3["minimum_self_occluded_lidar_hits"]),
            self_occluded,
            v3["minimum_self_occluded_lidar_hits"],
        )
        depth_artifact = isaac_report.get("depth_artifact") or {}
        artifact_records = depth_artifact.get("artifacts", {})
        artifact_checks = {}
        for record in artifact_records.values():
            artifact_path = (
                None
                if depth_artifact_root is None
                else depth_artifact_root / record["path"]
            )
            artifact_checks[record["path"]] = (
                artifact_path is not None
                and artifact_path.is_file()
                and _sha256(artifact_path) == record["sha256"]
            )
        add(
            "v3_depth_artifacts",
            len(artifact_checks) >= int(v3["minimum_depth_artifact_count"])
            and all(artifact_checks.values()),
            artifact_checks,
            v3["minimum_depth_artifact_count"],
        )

    forest = thresholds.get("forest_navigation")
    if forest is not None:
        navigation = run_identity.get("forest_scene", {}).get("navigation") or {}
        primary = navigation.get("primary_blocker") or {}
        start = [float(value) for value in navigation.get("start_world_m", [])]
        nav_goal = [float(value) for value in navigation.get("goal_world_m", [])]
        center = [float(value) for value in primary.get("center_m", [])]
        identity_valid = len(start) == 3 and len(nav_goal) == 3 and len(center) == 3
        expected_goal = [float(value) for value in forest["goal_world_m"]]
        add(
            "forest_goal_identity",
            identity_valid and nav_goal == expected_goal,
            nav_goal,
            expected_goal,
        )
        direct_distance = (
            point_to_segment_distance_2d(center[:2], start[:2], nav_goal[:2])
            if identity_valid
            else math.inf
        )
        required_clearance = float(
            navigation.get("required_center_clearance_m", math.inf)
        )
        add(
            "forest_direct_path_blocked",
            identity_valid
            and bool(navigation.get("direct_path_intersects_inflated_blocker"))
            and direct_distance < required_clearance,
            {
                "center_to_segment_m": direct_distance,
                "required_center_clearance_m": required_clearance,
            },
            "center_to_segment < required_center_clearance",
        )
        sensor_filter = run_identity.get("sensor", {}).get(
            "forest_geometry_filter", {}
        )
        forbidden_inputs = set(sensor_filter.get("forbidden_inputs", []))
        add(
            "forest_geometry_only_planner_input",
            sensor_filter.get("enabled") is True
            and forbidden_inputs
            == {
                "terrain_height_function",
                "scene_prim_id",
                "proxy_bounds",
                "obstacle_label",
            },
            sensor_filter,
            "rendered XYZ geometry filter with all scene-truth inputs forbidden",
        )

        filter_enabled_fraction = sum(
            bool(row.get("planner_geometry_filter_enabled"))
            for row in sensor_metrics
        ) / len(sensor_metrics)
        minimum_filtered_ground = min(
            int(row.get("planner_geometry_filter_ground_hit_count", 0))
            for row in sensor_metrics
        )
        minimum_filtered_obstacles = min(
            int(row.get("planner_geometry_filter_obstacle_hit_count", 0))
            for row in sensor_metrics
        )
        maximum_sparse_fraction = max(
            int(row.get("planner_geometry_filter_sparse_retained_hit_count", 0))
            / max(
                1,
                int(row.get("planner_geometry_filter_obstacle_hit_count", 0)),
            )
            for row in sensor_metrics
        )
        add(
            "forest_filter_enabled",
            filter_enabled_fraction
            >= float(forest["minimum_filter_enabled_fraction"]),
            filter_enabled_fraction,
            forest["minimum_filter_enabled_fraction"],
        )
        add(
            "forest_filter_removes_terrain",
            minimum_filtered_ground
            >= int(forest["minimum_filtered_ground_hits_per_frame"]),
            minimum_filtered_ground,
            forest["minimum_filtered_ground_hits_per_frame"],
        )
        add(
            "forest_filter_keeps_obstacles",
            minimum_filtered_obstacles
            >= int(forest["minimum_filtered_obstacle_hits_per_frame"]),
            minimum_filtered_obstacles,
            forest["minimum_filtered_obstacle_hits_per_frame"],
        )
        add(
            "forest_filter_sparse_fraction",
            maximum_sparse_fraction
            <= float(forest["maximum_sparse_retained_fraction"]),
            maximum_sparse_fraction,
            forest["maximum_sparse_retained_fraction"],
        )

        moving_rows = [
            row
            for row in metrics
            if math.hypot(
                float(row["applied_command"][0]),
                float(row["applied_command"][1]),
            )
            >= 0.10
        ]
        max_forward_command = max(
            (float(row["applied_command"][0]) for row in metrics), default=0.0
        )
        moving_speeds = [
            math.hypot(
                float(row["root_lin_vel_w"][0]),
                float(row["root_lin_vel_w"][1]),
            )
            for row in moving_rows
        ]
        speed_p75 = _percentile(moving_speeds, 0.75) if moving_speeds else 0.0
        add(
            "forest_forward_command_speed",
            max_forward_command >= float(forest["minimum_forward_command_mps"]),
            max_forward_command,
            forest["minimum_forward_command_mps"],
        )
        add(
            "forest_measured_speed_p75",
            speed_p75 >= float(forest["minimum_measured_speed_p75_mps"]),
            speed_p75,
            forest["minimum_measured_speed_p75_mps"],
        )

        if identity_valid:
            primary_clearance = min(
                math.dist(
                    [float(value) for value in row["root_pos_w"][:2]],
                    center[:2],
                )
                for row in metrics
            )
            obstacle_window = [
                float(value) for value in forest["obstacle_x_window_m"]
            ]
            obstacle_rows = [
                row
                for row in metrics
                if obstacle_window[0]
                <= float(row["root_pos_w"][0])
                <= obstacle_window[1]
            ]
            maximum_line_deviation = max(
                (
                    point_to_segment_distance_2d(
                        [float(value) for value in row["root_pos_w"][:2]],
                        start[:2],
                        nav_goal[:2],
                    )
                    for row in obstacle_rows
                ),
                default=0.0,
            )
            path_length = sum(
                math.dist(
                    [float(value) for value in left["root_pos_w"][:2]],
                    [float(value) for value in right["root_pos_w"][:2]],
                )
                for left, right in zip(metrics, metrics[1:])
            )
            direct_length = math.dist(start[:2], nav_goal[:2])
            path_excess = path_length - direct_length
        else:
            primary_clearance = 0.0
            maximum_line_deviation = 0.0
            path_excess = 0.0
        add(
            "forest_primary_blocker_clearance",
            primary_clearance
            >= float(forest["minimum_primary_center_clearance_m"]),
            primary_clearance,
            forest["minimum_primary_center_clearance_m"],
        )
        add(
            "forest_planner_detour",
            maximum_line_deviation
            >= float(forest["minimum_line_deviation_m"]),
            maximum_line_deviation,
            forest["minimum_line_deviation_m"],
        )
        add(
            "forest_path_length_excess",
            path_excess >= float(forest["minimum_path_length_excess_m"]),
            path_excess,
            forest["minimum_path_length_excess_m"],
        )
        base_clearances = [
            float(row["base_clearance_m"])
            for row in metrics
            if row.get("base_clearance_m") is not None
        ]
        terrain_heights = [
            float(row["terrain_height_under_root_m"])
            for row in metrics
            if row.get("terrain_height_under_root_m") is not None
        ]
        minimum_base_clearance = min(base_clearances) if base_clearances else 0.0
        terrain_height_range = (
            max(terrain_heights) - min(terrain_heights)
            if terrain_heights
            else 0.0
        )
        add(
            "forest_base_clearance",
            minimum_base_clearance
            >= float(forest["minimum_base_clearance_m"]),
            minimum_base_clearance,
            forest["minimum_base_clearance_m"],
        )
        add(
            "forest_nonflat_terrain",
            terrain_height_range
            >= float(forest["minimum_terrain_height_range_m"]),
            terrain_height_range,
            forest["minimum_terrain_height_range_m"],
        )

    passed = all(value["passed"] for value in checks.values())
    return {
        "schema_version": 1,
        "status": "PASS" if passed else "FAIL",
        "claim": thresholds["claim"],
        "checks": checks,
        "summary": {
            "final_position_world_m": final_position,
            "goal_xy_error_m": goal_xy_error,
            "detour_min_abs_y_m": detour_abs_y,
            "max_nonfoot_contact_n": max_nonfoot,
            "policy_rate_hz": policy_rate,
            "sensor_rate_hz": sensor_rate,
            "command_age_p95_ms": command_age_p95,
            "video_sha256": video_hash,
            "rosbag_bytes": bag_bytes,
            "forest_navigation_enabled": forest is not None,
        },
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--thresholds", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--sensor-metrics", type=Path, required=True)
    parser.add_argument("--isaac-report", type=Path, required=True)
    parser.add_argument("--run-identity", type=Path, required=True)
    parser.add_argument("--ros-summary", type=Path, required=True)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--rosbag", type=Path, required=True)
    parser.add_argument("--foxy-log", type=Path, required=True)
    parser.add_argument("--depth-metrics", type=Path)
    parser.add_argument("--runtime-composition", type=Path)
    parser.add_argument("--depth-artifact-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    thresholds = json.loads(args.thresholds.read_text(encoding="utf-8"))
    report = evaluate_acceptance(
        thresholds,
        _load_jsonl(args.metrics),
        _load_jsonl(args.sensor_metrics),
        json.loads(args.isaac_report.read_text(encoding="utf-8")),
        json.loads(args.run_identity.read_text(encoding="utf-8")),
        json.loads(args.ros_summary.read_text(encoding="utf-8")),
        args.video,
        args.rosbag,
        args.foxy_log.read_text(encoding="utf-8"),
        _sha256(args.thresholds),
        None if args.depth_metrics is None else _load_jsonl(args.depth_metrics),
        (
            None
            if args.runtime_composition is None
            else json.loads(args.runtime_composition.read_text(encoding="utf-8"))
        ),
        args.depth_artifact_root,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(args.output)}))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
