"""Qualify the one allowed V12 model_149999 fallback in its pinned runtime."""

import argparse
import inspect
import json
import math
from pathlib import Path
import time

from .command_state import CommandLimits, LatestCommandState
from .isaac_adapter_core import (
    canonical_config_sha256,
    quaternion_wxyz_to_xyzw,
    schedule_duration,
    schedule_state,
    world_hits_to_sensor_points,
)
from .protocol import (
    MessageType,
    SensorFrameV1,
    StatusFlag,
    StatusV1,
    encode_frame,
    encode_sensor_payload,
    encode_status_payload,
    pack_xyz_points,
)
from .run_isaac_lite3 import (
    AdapterFailure,
    _QualificationSender,
    _TelemetrySink,
    _qualification_report,
    _sha256,
    _tensor_list,
    _write_json,
)
from .transport import CommandReceiverServer, TelemetryPublisherServer


PINNED_SOURCE_COMMIT = "8c3fdffa84b85be0704a10ea5b2533817d543822"
PINNED_CHECKPOINT_SHA256 = (
    "a9d31dce90e6e8c564d955e473d6d3502f893d7ef5a5c1efaf5bb50d6b3d5450"
)
DEFAULT_TASK = "Wave-C-Stairs-V12-Lite3-v0"
POLICY_OBSERVATION_DIMENSION = 450
COMMAND_HISTORY_OFFSET = 60
COMMAND_HISTORY_LENGTH = 10
COURSE_OBSTACLE_CENTER = (2.0, 0.0, 0.4)
COURSE_OBSTACLE_SIZE = (0.6, 1.2, 0.8)
GROUND_MESH_PRIM = "/World/ground"
OBSTACLE_MESH_PRIM = "/World/ground/scan_obstacle"
VIDEO_CAMERA_EYE = (2.0, -5.5, 3.2)
VIDEO_CAMERA_LOOKAT = (2.0, 0.0, 0.25)
VIDEO_RESOLUTION = (1280, 720)


def _rgb_frame(frame):
    import numpy as np

    if frame is None:
        raise AdapterFailure("renderer returned no RGB frame")
    if frame.ndim != 3 or frame.shape[2] not in (3, 4):
        raise AdapterFailure(f"unexpected RGB frame shape: {frame.shape}")
    return np.asarray(frame[:, :, :3], dtype=np.uint8)


def _activate_vendored_rsl_rl(vendored_root: Path) -> Path:
    """Require the complete RSL-RL package recovered from the pinned V12 run."""

    import rsl_rl

    package_dir = vendored_root.resolve() / "rsl_rl"
    package_source = Path(rsl_rl.__file__ or "").resolve()
    required_files = (
        package_dir / "env" / "vec_env.py",
        package_dir / "modules" / "actor_critic_moe_cts.py",
    )
    missing = [path for path in required_files if not path.is_file()]
    if missing:
        raise AdapterFailure(
            "pinned V12 RSL-RL runtime is incomplete: "
            + ", ".join(str(path) for path in missing)
        )
    try:
        package_source.relative_to(package_dir)
    except ValueError as error:
        raise AdapterFailure(
            f"RSL-RL resolved outside the pinned V12 runtime: {package_source}"
        ) from error
    return package_dir


def _load_inference_policy(wrapped_env, agent_cfg, checkpoint: Path, device: str):
    """Construct only the immutable V12 inference network, not its training split."""

    import torch
    from rsl_rl.modules import ActorCriticMoECTS
    from rsl_rl.utils import resolve_obs_groups

    train_cfg = agent_cfg.to_dict()
    observations = wrapped_env.get_observations()
    obs_groups = resolve_obs_groups(
        observations, train_cfg["obs_groups"], ["critic"]
    )
    policy_cfg = dict(train_cfg["policy"])
    class_name = policy_cfg.pop("class_name")
    if class_name != "ActorCriticMoECTS":
        raise AdapterFailure(f"unexpected V12 policy class: {class_name}")
    policy_module = ActorCriticMoECTS(
        observations, obs_groups, wrapped_env.num_actions, **policy_cfg
    ).to(device)
    checkpoint_payload = torch.load(
        checkpoint, weights_only=False, map_location=device
    )
    if "model_state_dict" not in checkpoint_payload:
        raise AdapterFailure("V12 checkpoint has no model_state_dict")
    policy_module.load_state_dict(checkpoint_payload["model_state_dict"], strict=True)
    policy_module.eval()
    source = Path(inspect.getsourcefile(ActorCriticMoECTS) or "").resolve()
    return policy_module.act_inference, policy_module, observations, source


def _configure_environment(env_cfg, args) -> None:
    env_cfg.scene.num_envs = 1
    env_cfg.seed = args.seed
    env_cfg.sim.device = args.device
    env_cfg.observations.policy.enable_corruption = False
    env_cfg.sim.enable_scene_query_support = True
    if args.video_path is not None:
        env_cfg.viewer.origin_type = "world"
        env_cfg.viewer.eye = VIDEO_CAMERA_EYE
        env_cfg.viewer.lookat = VIDEO_CAMERA_LOOKAT
        env_cfg.viewer.resolution = VIDEO_RESOLUTION
    if args.mode == "external":
        env_cfg.episode_length_s = max(
            float(env_cfg.episode_length_s), args.duration_seconds + 5.0
        )

    events = getattr(env_cfg, "events", None)
    if events is not None:
        for name in (
            "randomize_rigid_body_mass_base",
            "randomize_rigid_body_mass_others",
            "randomize_com_positions",
            "randomize_actuator_gains",
            "randomize_motor_zero_offset",
            "randomize_push_robot",
            "randomize_apply_external_force_torque",
            "randomize_rigid_body_material",
        ):
            if hasattr(events, name):
                setattr(events, name, None)
        if getattr(events, "reset_robot_joints", None) is not None:
            events.reset_robot_joints.params["position_range"] = (1.0, 1.0)
            events.reset_robot_joints.params["velocity_range"] = (0.0, 0.0)
        if getattr(events, "reset_base", None) is not None:
            events.reset_base.params["pose_range"] = {
                "x": (0.0, 0.0),
                "y": (0.0, 0.0),
                "z": (0.0, 0.0),
                "yaw": (0.0, 0.0),
            }
            events.reset_base.params["velocity_range"] = {
                axis: (0.0, 0.0)
                for axis in ("x", "y", "z", "roll", "pitch", "yaw")
            }
    curriculum = getattr(env_cfg, "curriculum", None)
    if curriculum is not None:
        for name in (
            "terrain_levels",
            "command_levels_lin_vel",
            "command_levels_ang_vel",
            "base_linear_velocity",
            "base_height_l2",
        ):
            if hasattr(curriculum, name):
                setattr(curriculum, name, None)

    command_cfg = env_cfg.commands.base_velocity
    command_cfg.dynamic_resample_commands = False
    command_cfg.command_range_curriculum = []
    command_cfg.zero_command_curriculum = None
    command_cfg.limit_vel_prob = 0.0
    command_cfg.limit_ang_vel_at_zero_command_prob = 0.0
    command_cfg.resampling_time = 1000.0
    command_cfg.resampling_time_range = (1000.0, 1000.0)
    command_cfg.ranges.lin_vel_x = (0.0, 0.0)
    command_cfg.ranges.lin_vel_y = (0.0, 0.0)
    command_cfg.ranges.ang_vel_yaw = (0.0, 0.0)

    terrain = env_cfg.scene.terrain.terrain_generator
    if terrain is None or "flat" not in terrain.sub_terrains:
        raise AdapterFailure("pinned V12 task has no flat terrain generator")
    terrain.num_rows = 1
    terrain.num_cols = 1
    terrain.curriculum = False
    terrain.difficulty_range = (0.0, 0.0)
    terrain.use_cache = False
    for name, sub_cfg in terrain.sub_terrains.items():
        sub_cfg.proportion = 1.0 if name == "flat" else 0.0
    env_cfg.scene.terrain.max_init_terrain_level = 0

    if args.course == "single_box":
        import isaaclab.sim as sim_utils
        from isaaclab.assets import AssetBaseCfg

        env_cfg.scene.scan_obstacle = AssetBaseCfg(
            prim_path="/World/ground/scan_obstacle",
            spawn=sim_utils.CuboidCfg(
                size=COURSE_OBSTACLE_SIZE,
                collision_props=sim_utils.CollisionPropertiesCfg(),
                visual_material=sim_utils.PreviewSurfaceCfg(
                    diffuse_color=(0.8, 0.1, 0.1)
                ),
            ),
            init_state=AssetBaseCfg.InitialStateCfg(pos=COURSE_OBSTACLE_CENTER),
        )

    from isaaclab.sensors import MultiMeshRayCasterCfg, patterns

    pitch_radians = math.radians(args.sensor_pitch_degrees)
    sensor_rotation_wxyz = (
        math.cos(pitch_radians / 2.0),
        0.0,
        math.sin(pitch_radians / 2.0),
        0.0,
    )
    env_cfg.scene.navigation_lidar = MultiMeshRayCasterCfg(
        prim_path="{ENV_REGEX_NS}/Robot/TORSO",
        update_period=args.sensor_period,
        offset=MultiMeshRayCasterCfg.OffsetCfg(
            pos=tuple(args.sensor_translation), rot=sensor_rotation_wxyz
        ),
        ray_alignment="base",
        pattern_cfg=patterns.LidarPatternCfg(
            channels=args.lidar_channels,
            vertical_fov_range=(args.lidar_vertical_min, args.lidar_vertical_max),
            horizontal_fov_range=(-180.0, 180.0),
            horizontal_res=args.lidar_horizontal_resolution,
        ),
        max_distance=args.lidar_max_range,
        # Keep the obstacle as a distinct target. The terrain height scanner
        # already caches /World/ground before this sensor initializes, so using
        # the parent alone would silently reuse a terrain-only Warp mesh.
        mesh_prim_paths=[GROUND_MESH_PRIM]
        + ([OBSTACLE_MESH_PRIM] if args.course == "single_box" else []),
        update_mesh_ids=False,
        debug_vis=False,
    )


def _policy_command_evidence(observation, command):
    policy_observation = observation["policy"]
    if tuple(policy_observation.shape) != (1, POLICY_OBSERVATION_DIMENSION):
        raise AdapterFailure(
            f"V12 policy observation shape {tuple(policy_observation.shape)} != "
            f"(1, {POLICY_OBSERVATION_DIMENSION})"
        )
    history = policy_observation[
        0,
        COMMAND_HISTORY_OFFSET : COMMAND_HISTORY_OFFSET + COMMAND_HISTORY_LENGTH * 3,
    ].reshape(COMMAND_HISTORY_LENGTH, 3)
    expected = policy_observation.new_tensor(command)
    errors = (history - expected).abs().amax(dim=1)
    best_error, best_index = errors.min(dim=0)
    error = float(best_error.detach().cpu().item())
    if error > 1.0e-6:
        raise AdapterFailure(
            f"V12 command absent from policy observation history: error={error}"
        )
    selected = history[int(best_index.item())]
    return _tensor_list(selected), error, int(best_index.item())


def _sensor_gate(sensor_records):
    checks = {
        "frames_present": bool(sensor_records),
        "nonempty": bool(sensor_records)
        and all(row["point_count"] > 0 for row in sensor_records),
        "finite": bool(sensor_records)
        and all(row["finite_point_count"] == row["point_count"] for row in sensor_records),
        "timestamps_advance": len(sensor_records) >= 2
        and all(
            right["sim_time_seconds"] > left["sim_time_seconds"]
            for left, right in zip(sensor_records, sensor_records[1:])
        ),
        "ground_returns": bool(sensor_records)
        and max(row["ground_hit_count"] for row in sensor_records) > 0,
        "obstacle_returns": bool(sensor_records)
        and max(row["obstacle_surface_hit_count"] for row in sensor_records) > 0,
    }
    pose_displacement = 0.0
    centroid_displacement = 0.0
    if len(sensor_records) >= 2:
        first = sensor_records[0]
        last = sensor_records[-1]
        pose_displacement = math.dist(
            first["sensor_position_w"], last["sensor_position_w"]
        )
        centroid_displacement = math.dist(
            first["centroid_sensor"], last["centroid_sensor"]
        )
    checks["pose_displacement_m_value"] = pose_displacement
    checks["cloud_centroid_displacement_m_value"] = centroid_displacement
    checks["pose_dependent_geometry"] = (
        pose_displacement >= 0.10 and centroid_displacement >= 0.02
    )
    required = (
        "frames_present",
        "nonempty",
        "finite",
        "timestamps_advance",
        "ground_returns",
        "obstacle_returns",
        "pose_dependent_geometry",
    )
    return checks, all(bool(checks[name]) for name in required)


def _run(args) -> int:
    import gymnasium as gym
    import torch
    from isaaclab.utils.math import combine_frame_transforms
    from isaaclab_tasks.utils.parse_cfg import load_cfg_from_registry

    vendored_package_dir = _activate_vendored_rsl_rl(args.vendored_rsl_rl)
    expected_policy_source = vendored_package_dir / "modules" / "actor_critic_moe_cts.py"
    from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper

    if args.source_commit != PINNED_SOURCE_COMMIT:
        raise AdapterFailure("source commit is not the pinned V12 fallback")
    checkpoint_sha256 = _sha256(args.checkpoint)
    if checkpoint_sha256 != PINNED_CHECKPOINT_SHA256:
        raise AdapterFailure("V12 fallback checkpoint hash mismatch")
    if args.command_host != "127.0.0.1" or args.telemetry_host != "127.0.0.1":
        raise AdapterFailure("v1 endpoints must bind to 127.0.0.1")
    if (
        not math.isfinite(args.planner_floor_filter_max_z)
        or args.planner_floor_filter_max_z < 0.0
        or args.planner_floor_filter_max_z > 0.10
    ):
        raise AdapterFailure("planner floor filter must be within [0.0, 0.10] m")
    if args.video_path is not None and (
        args.video_fps <= 0 or args.video_frame_stride <= 0
    ):
        raise AdapterFailure("video fps and frame stride must be positive")
    if (
        not math.isfinite(args.connection_ready_timeout_seconds)
        or args.connection_ready_timeout_seconds <= 0.0
    ):
        raise AdapterFailure("connection ready timeout must be positive and finite")

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    sensor_rotation_wxyz = (
        math.cos(math.radians(args.sensor_pitch_degrees) / 2.0),
        0.0,
        math.sin(math.radians(args.sensor_pitch_degrees) / 2.0),
        0.0,
    )
    identity = {
        "schema_version": 1,
        "candidate": "V12 model_149999 fallback",
        "source_commit": args.source_commit,
        "checkpoint_sha256": checkpoint_sha256,
        "task": args.task,
        "mode": args.mode,
        "seed": args.seed,
        "device": args.device,
        "terrain": "flat at difficulty 0.0",
        "course": {
            "name": args.course,
            "obstacle_center_m": (
                COURSE_OBSTACLE_CENTER if args.course == "single_box" else None
            ),
            "obstacle_size_m": (
                COURSE_OBSTACLE_SIZE if args.course == "single_box" else None
            ),
        },
        "command_limits": [args.max_vx, args.max_vy, args.max_wz],
        "watchdog_seconds": args.watchdog_seconds,
        "acceptance_config_sha256": (
            None if args.acceptance_config is None else _sha256(args.acceptance_config)
        ),
        "video": {
            "enabled": args.video_path is not None,
            "filename": None if args.video_path is None else args.video_path.name,
            "fps": args.video_fps,
            "frame_stride": args.video_frame_stride,
            "camera_eye_world": VIDEO_CAMERA_EYE,
            "camera_lookat_world": VIDEO_CAMERA_LOOKAT,
            "resolution": VIDEO_RESOLUTION,
        },
        "policy_observation_contract": {
            "dimension": POLICY_OBSERVATION_DIMENSION,
            "command_history_offset": COMMAND_HISTORY_OFFSET,
            "command_history_length": COMMAND_HISTORY_LENGTH,
        },
        "inference_policy": {
            "class": "ActorCriticMoECTS",
            "loader": "direct policy-only strict state_dict load",
            "vendored_package": "source/rsl_rl/rsl_rl",
            "source": "modules/actor_critic_moe_cts.py",
            "source_sha256": _sha256(expected_policy_source),
        },
        "sensor": {
            "backend": "IsaacLab MultiMeshRayCaster LidarPatternCfg",
            "truth_pose": True,
            "parent_frame": "TORSO",
            "translation_m": args.sensor_translation,
            "rotation_wxyz": sensor_rotation_wxyz,
            "channels": args.lidar_channels,
            "vertical_fov_degrees": [args.lidar_vertical_min, args.lidar_vertical_max],
            "horizontal_resolution_degrees": args.lidar_horizontal_resolution,
            "minimum_range_m": args.lidar_min_range,
            "maximum_range_m": args.lidar_max_range,
            "period_seconds": args.sensor_period,
            "planner_floor_filter": {
                "frame": "world",
                "remove_hits_at_or_below_z_m": args.planner_floor_filter_max_z,
                "reason": "SCAN occupancy input excludes the traversable flat floor",
            },
            "raycast_targets": [GROUND_MESH_PRIM]
            + ([OBSTACLE_MESH_PRIM] if args.course == "single_box" else []),
            "obstacle_return_classification": (
                "finite hit above floor filter inside the only non-ground mesh bounds"
            ),
        },
    }
    config_sha256 = canonical_config_sha256(identity)
    identity["config_sha256"] = config_sha256.hex()
    _write_json(output_dir / "run_identity.json", identity)

    limits = CommandLimits(args.max_vx, args.max_vy, args.max_wz)
    state = LatestCommandState(
        limits,
        timeout_ns=int(args.watchdog_seconds * 1.0e9),
        max_source_age_ns=int(args.watchdog_seconds * 1.0e9),
        max_future_skew_ns=25_000_000,
    )
    command_server = CommandReceiverServer(state, args.command_host, args.command_port)
    telemetry_server = TelemetryPublisherServer(args.telemetry_host, args.telemetry_port)
    sender = None
    sink = None
    if args.mode in ("qualification", "sensor_qualification"):
        sender = _QualificationSender(args.command_port, 50.0, limits)
        sink = _TelemetrySink(args.telemetry_port, config_sha256)

    wrapped_env = None
    runtime_error = None
    records = []
    sensor_records = []
    telemetry_sequence = 0
    dropped_frames = 0
    video_writer = None
    video_frame_count = 0
    runtime_rates = {}
    try:
        __import__("robot_lab.tasks")
        env_cfg = load_cfg_from_registry(args.task, "env_cfg_entry_point")
        agent_cfg = load_cfg_from_registry(args.task, "rsl_rl_cfg_entry_point")
        _configure_environment(env_cfg, args)
        agent_cfg.seed = args.seed
        agent_cfg.device = args.device
        raw_env = gym.make(
            args.task,
            cfg=env_cfg,
            render_mode="rgb_array" if args.video_path is not None else None,
        )
        base_env = raw_env.unwrapped
        runtime_rates = {
            "physics_hz": 1.0 / float(base_env.physics_dt),
            "policy_hz": 1.0 / float(base_env.step_dt),
            "sensor_hz": 1.0 / args.sensor_period,
        }
        wrapped_env = RslRlVecEnvWrapper(raw_env, clip_actions=agent_cfg.clip_actions)
        policy, policy_state, observation, policy_source = _load_inference_policy(
            wrapped_env, agent_cfg, args.checkpoint, agent_cfg.device
        )
        if policy_source != expected_policy_source:
            raise AdapterFailure(
                f"ActorCriticMoECTS resolved outside the pinned source: {policy_source}"
            )
        robot = base_env.scene["robot"]
        lidar = base_env.scene.sensors["navigation_lidar"]
        contact = base_env.scene.sensors["contact_forces"]
        contact_foot_ids, contact_names = contact.find_bodies(
            ["FL_FOOT", "FR_FOOT", "HL_FOOT", "HR_FOOT"], preserve_order=True
        )
        if len(contact_foot_ids) != 4:
            raise AdapterFailure(f"V12 contact foot binding mismatch: {contact_names}")
        previous_actions = torch.zeros((1, 12), device=base_env.device)
        sensor_translation = torch.tensor(
            [args.sensor_translation], device=base_env.device, dtype=robot.data.root_pos_w.dtype
        )
        sensor_rotation = torch.tensor(
            [sensor_rotation_wxyz], device=base_env.device, dtype=robot.data.root_quat_w.dtype
        )
        sensor_stride = max(1, int(round(args.sensor_period / float(base_env.step_dt))))
        if args.video_path is not None:
            import imageio

            args.video_path.parent.mkdir(parents=True, exist_ok=True)
            for _ in range(8):
                _rgb_frame(raw_env.render())
            video_writer = imageio.get_writer(
                str(args.video_path),
                fps=args.video_fps,
                codec="libx264",
                quality=8,
                macro_block_size=16,
            )
        # Expose the TCP endpoints only after the scene, policy, sensor, and
        # optional renderer are ready. Otherwise a Foxy client can accumulate
        # commands that become stale during simulator initialization.
        command_server.start()
        telemetry_server.start()
        if sink is not None:
            sink.start()
        if sender is not None:
            sender.start()
        connection_deadline = time.monotonic() + args.connection_ready_timeout_seconds
        while time.monotonic() < connection_deadline:
            if sender is not None and sender.error is not None:
                raise AdapterFailure(f"fallback command sender failed: {sender.error}")
            if (
                command_server.stats().accepted_connections > 0
                and telemetry_server.stats().accepted_connections > 0
            ):
                break
            time.sleep(0.01)
        else:
            raise AdapterFailure(
                "command and telemetry clients did not connect before the ready timeout"
            )
        started = time.monotonic()
        next_tick = started
        run_seconds = (
            schedule_duration() + 0.25
            if args.mode in ("qualification", "sensor_qualification")
            else args.duration_seconds
        )
        metrics_path = output_dir / "metrics.jsonl"
        sensor_metrics_path = output_dir / "sensor_metrics.jsonl"
        with metrics_path.open("w", encoding="utf-8") as metrics_file, \
                sensor_metrics_path.open("w", encoding="utf-8") as sensor_metrics_file:
            step = 0
            while time.monotonic() - started < run_seconds:
                tick_started = time.monotonic()
                if sender is not None and sender.error is not None:
                    raise AdapterFailure(f"fallback command sender failed: {sender.error}")
                snapshot = command_server.snapshot(time.monotonic_ns())
                command = (snapshot.command.vx, snapshot.command.vy, snapshot.command.wz)
                command_term = base_env.command_manager.get_term("base_velocity")
                command_term.commands[:, 0] = command[0]
                command_term.commands[:, 1] = command[1]
                command_term.commands[:, 2] = command[2]
                observation, _, dones, _ = wrapped_env.step(previous_actions)
                policy_state.reset(dones)
                actual_command = base_env.command_manager.get_command("base_velocity")
                expected_command = actual_command.new_tensor([command])
                if not torch.allclose(actual_command, expected_command, atol=1.0e-6, rtol=0.0):
                    raise AdapterFailure(
                        f"V12 live command drifted: {actual_command.detach().cpu().tolist()}"
                    )
                observed_command, command_error, command_history_index = _policy_command_evidence(
                    observation, command
                )
                with torch.inference_mode():
                    actions = policy(observation)
                if tuple(actions.shape) != (1, 12):
                    raise AdapterFailure(f"V12 action shape {tuple(actions.shape)} != (1, 12)")
                previous_actions = actions

                force_norm = torch.linalg.vector_norm(contact.data.net_forces_w[0], dim=-1)
                contact_count = int(
                    (force_norm[contact_foot_ids] >= args.contact_force_threshold).sum().item()
                )
                nonfoot_ids = [
                    index for index in range(force_norm.shape[0]) if index not in contact_foot_ids
                ]
                nonfoot_max = float(force_norm[nonfoot_ids].max().item()) if nonfoot_ids else 0.0
                done = bool(dones.any().item())
                finite = bool(
                    all(torch.isfinite(value).all().item() for value in observation.values())
                    and torch.isfinite(actions).all().item()
                    and torch.isfinite(robot.data.root_state_w).all().item()
                )
                now = time.monotonic()
                command_age_ms = (
                    0.0
                    if snapshot.received_monotonic_ns is None
                    else max(
                        0.0,
                        (time.monotonic_ns() - snapshot.received_monotonic_ns) / 1.0e6,
                    )
                )
                schedule_elapsed = 0.0
                if sender is not None and sender.started_monotonic is not None:
                    schedule_elapsed = max(0.0, now - sender.started_monotonic)
                segment, segment_elapsed = schedule_state(schedule_elapsed)
                row = {
                    "step": step,
                    "wall_elapsed_seconds": now - started,
                    "sim_time_seconds": float(base_env.sim.current_time),
                    "schedule_segment": (
                        segment.name if sender is not None else "external"
                    ),
                    "schedule_segment_elapsed_seconds": segment_elapsed,
                    "applied_command": list(command),
                    "command_sequence": snapshot.sequence,
                    "command_reason": snapshot.reason,
                    "command_stale": snapshot.stale,
                    "command_observation": observed_command,
                    "command_observation_history_index": command_history_index,
                    "command_observation_max_error": command_error,
                    "root_pos_w": _tensor_list(robot.data.root_pos_w[0]),
                    "root_quat_wxyz": _tensor_list(robot.data.root_quat_w[0]),
                    "root_lin_vel_w": _tensor_list(robot.data.root_lin_vel_w[0]),
                    "root_ang_vel_w": _tensor_list(robot.data.root_ang_vel_w[0]),
                    "root_lin_vel_b": _tensor_list(robot.data.root_lin_vel_b[0]),
                    "root_ang_vel_b": _tensor_list(robot.data.root_ang_vel_b[0]),
                    "actions": _tensor_list(actions[0]),
                    "joint_position": _tensor_list(robot.data.joint_pos[0]),
                    "joint_velocity": _tensor_list(robot.data.joint_vel[0]),
                    "applied_torque": _tensor_list(robot.data.applied_torque[0]),
                    "contact_count": contact_count,
                    "nonfoot_contact_max_n": nonfoot_max,
                    "done": done,
                    "finite": finite,
                    "watchdog_events": snapshot.watchdog_events,
                    "sequence_gaps": snapshot.sequence_gaps,
                    "command_age_ms": command_age_ms,
                }
                records.append(row)
                metrics_file.write(json.dumps(row, sort_keys=True) + "\n")
                metrics_file.flush()

                if step % sensor_stride == 0:
                    lidar.update(dt=0.0, force_recompute=True)
                    hits_w = lidar.data.ray_hits_w[0]
                    sensor_position, sensor_quaternion_wxyz_tensor = combine_frame_transforms(
                        robot.data.root_pos_w,
                        robot.data.root_quat_w,
                        sensor_translation,
                        sensor_rotation,
                    )
                    sensor_position_values = _tensor_list(sensor_position[0])
                    sensor_quaternion_values = _tensor_list(sensor_quaternion_wxyz_tensor[0])
                    points = world_hits_to_sensor_points(
                        hits_w.detach().cpu().tolist(),
                        sensor_position_values,
                        sensor_quaternion_values,
                        args.lidar_min_range,
                        args.lidar_max_range,
                        minimum_world_z=args.planner_floor_filter_max_z,
                    )
                    point_count, point_bytes = pack_xyz_points(points)
                    finite_hits = torch.isfinite(hits_w).all(dim=-1)
                    floor_filtered_hits = finite_hits & (
                        hits_w[:, 2] <= args.planner_floor_filter_max_z
                    )
                    ground_hits = finite_hits & torch.isclose(
                        hits_w[:, 2], hits_w.new_tensor(0.0), atol=0.03, rtol=0.0
                    )
                    obstacle_hits = torch.zeros_like(finite_hits)
                    if args.course == "single_box":
                        center = hits_w.new_tensor(COURSE_OBSTACLE_CENTER)
                        half_size = 0.5 * hits_w.new_tensor(COURSE_OBSTACLE_SIZE)
                        obstacle_hits = (
                            finite_hits
                            & (hits_w[:, 2] > args.planner_floor_filter_max_z)
                            & (
                                (hits_w >= center - half_size - 0.01)
                                & (hits_w <= center + half_size + 0.01)
                            ).all(dim=-1)
                        )
                    centroid = [0.0, 0.0, 0.0]
                    if points:
                        centroid = [
                            sum(point[axis] for point in points) / len(points)
                            for axis in range(3)
                        ]
                    sensor_row = {
                        "step": step,
                        "sim_time_seconds": float(base_env.sim.current_time),
                        "sensor_position_w": sensor_position_values,
                        "sensor_quaternion_wxyz": sensor_quaternion_values,
                        "point_count": point_count,
                        "finite_point_count": point_count,
                        "raw_finite_hit_count": int(finite_hits.sum().item()),
                        "planner_floor_filtered_hit_count": int(
                            floor_filtered_hits.sum().item()
                        ),
                        "ground_hit_count": int(ground_hits.sum().item()),
                        "obstacle_surface_hit_count": int(obstacle_hits.sum().item()),
                        "unexpected_above_floor_hit_count": int(
                            (
                                finite_hits
                                & (hits_w[:, 2] > args.planner_floor_filter_max_z)
                                & ~obstacle_hits
                            ).sum().item()
                        ),
                        "centroid_sensor": centroid,
                    }
                    sensor_records.append(sensor_row)
                    sensor_metrics_file.write(json.dumps(sensor_row, sort_keys=True) + "\n")
                    sensor_metrics_file.flush()
                    sensor_payload = encode_sensor_payload(
                        SensorFrameV1(
                            body_position=tuple(_tensor_list(robot.data.root_pos_w[0])),
                            body_quaternion_xyzw=quaternion_wxyz_to_xyzw(
                                _tensor_list(robot.data.root_quat_w[0])
                            ),
                            sensor_position=tuple(sensor_position_values),
                            sensor_quaternion_xyzw=quaternion_wxyz_to_xyzw(
                                sensor_quaternion_values
                            ),
                            config_sha256=config_sha256,
                            point_count=point_count,
                            points_xyz_f32_be=point_bytes,
                        )
                    )
                    telemetry_sequence += 1
                    sent_sensor = telemetry_server.publish(
                        encode_frame(
                            MessageType.SENSOR_FRAME_V1,
                            telemetry_sequence,
                            int(float(base_env.sim.current_time) * 1.0e9),
                            sensor_payload,
                        )
                    )
                    dropped_frames += int(not sent_sensor)
                    flags = 0
                    if contact_count >= 2:
                        flags |= int(StatusFlag.CONTACT_SUPPORTED)
                    if nonfoot_max >= args.collision_force_threshold:
                        flags |= int(StatusFlag.COLLISION)
                    if done:
                        flags |= int(StatusFlag.TERMINATED)
                    if not finite:
                        flags |= int(StatusFlag.NAN_DETECTED)
                    telemetry_sequence += 1
                    sent_status = telemetry_server.publish(
                        encode_frame(
                            MessageType.STATUS_V1,
                            telemetry_sequence,
                            int(float(base_env.sim.current_time) * 1.0e9),
                            encode_status_payload(
                                StatusV1(
                                    physics_hz=1.0 / float(base_env.physics_dt),
                                    policy_hz=1.0 / float(base_env.step_dt),
                                    sensor_hz=1.0 / args.sensor_period,
                                    bridge_latency_ms=command_age_ms,
                                    contact_count=contact_count,
                                    dropped_frames=dropped_frames,
                                    watchdog_events=snapshot.watchdog_events,
                                    flags=flags,
                                    termination_code=1 if done else 0,
                                )
                            ),
                        )
                    )
                    dropped_frames += int(not sent_status)
                if video_writer is not None and step % args.video_frame_stride == 0:
                    video_writer.append_data(_rgb_frame(raw_env.render()))
                    video_frame_count += 1
                if done or not finite:
                    raise AdapterFailure("V12 fallback terminated or became non-finite")
                step += 1
                next_tick += float(base_env.step_dt)
                time.sleep(max(0.0, next_tick - time.monotonic()))
                if time.monotonic() - tick_started > args.max_step_wall_seconds:
                    raise AdapterFailure("V12 simulation step exceeded wall-time safety limit")
    except BaseException as error:
        runtime_error = error
    finally:
        if sender is not None:
            sender.stop()
        # End live transport at the simulation boundary. Video encoding and
        # simulator teardown can take longer than the command freshness limit;
        # leaving the receiver active would classify queued shutdown traffic as
        # a stale protocol frame even though no further policy step consumes it.
        command_server.stop()
        telemetry_server.stop()
        if video_writer is not None:
            try:
                video_writer.close()
            except BaseException as error:
                if runtime_error is None:
                    runtime_error = error
        if wrapped_env is not None:
            wrapped_env.close()
        if sink is not None:
            sink.stop()

    if sink is not None and sink.error is not None and runtime_error is None:
        runtime_error = sink.error
    sink_snapshot = sink.snapshot() if sink is not None else {}
    if args.mode == "external":
        external_checks = {
            "records_present": bool(records),
            "no_termination": bool(records) and not any(row["done"] for row in records),
            "finite_policy": bool(records) and all(row["finite"] for row in records),
            "command_connected": command_server.stats().accepted_connections > 0,
            "commands_received": command_server.stats().frames_received > 0,
            "telemetry_connected": telemetry_server.stats().accepted_connections > 0,
            "telemetry_sent": telemetry_server.stats().frames_sent > 0,
        }
        report = {
            "schema_version": 1,
            "status": "PASS" if all(external_checks.values()) else "FAIL",
            "claim": "external bridge runtime only; closed-loop goal result evaluated separately",
            "checks": external_checks,
            "command_transport": command_server.stats().__dict__,
            "telemetry_transport": telemetry_server.stats().__dict__,
            "record_count": len(records),
        }
    else:
        report = _qualification_report(
            records, sink_snapshot, command_server.stats(), telemetry_server.stats()
        )
    sensor_checks, sensor_passed = _sensor_gate(sensor_records)
    report["sensor_checks"] = sensor_checks
    report["runtime_rates"] = runtime_rates
    if args.video_path is not None:
        report["video"] = {
            "path": str(args.video_path),
            "frame_count": video_frame_count,
            "fps": args.video_fps,
            "encoded_duration_seconds": video_frame_count / args.video_fps,
            "bytes": args.video_path.stat().st_size if args.video_path.is_file() else 0,
            "sha256": _sha256(args.video_path) if args.video_path.is_file() else None,
        }
    if args.mode == "sensor_qualification" and not sensor_passed:
        report["status"] = "FAIL"
    report["candidate"] = "V12 model_149999 fallback"
    report["runtime_error"] = None if runtime_error is None else {
        "type": type(runtime_error).__name__,
        "message": str(runtime_error),
    }
    if runtime_error is not None:
        report["status"] = "INSTRUMENTATION_ERROR"
    _write_json(output_dir / "qualification_report.json", report)
    print(json.dumps({"status": report["status"], "output_dir": str(output_dir)}), flush=True)
    return 0 if report["status"] == "PASS" else 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("qualification", "sensor_qualification", "external"),
        default="qualification",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--vendored-rsl-rl", type=Path, required=True)
    parser.add_argument("--source-commit", default=PINNED_SOURCE_COMMIT)
    parser.add_argument("--task", default=DEFAULT_TASK)
    parser.add_argument("--course", choices=("flat", "single_box"), default="flat")
    parser.add_argument("--duration-seconds", type=float, default=30.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--command-host", default="127.0.0.1")
    parser.add_argument("--command-port", type=int, default=46001)
    parser.add_argument("--telemetry-host", default="127.0.0.1")
    parser.add_argument("--telemetry-port", type=int, default=46000)
    parser.add_argument("--max-vx", type=float, default=0.75)
    parser.add_argument("--max-vy", type=float, default=0.35)
    parser.add_argument("--max-wz", type=float, default=1.0)
    parser.add_argument("--watchdog-seconds", type=float, default=0.25)
    parser.add_argument("--sensor-period", type=float, default=0.10)
    parser.add_argument("--sensor-translation", type=float, nargs=3, default=(0.182399336, 0.0, 0.108541081))
    parser.add_argument("--sensor-pitch-degrees", type=float, default=15.0)
    parser.add_argument("--lidar-channels", type=int, default=16)
    parser.add_argument("--lidar-vertical-min", type=float, default=-7.0)
    parser.add_argument("--lidar-vertical-max", type=float, default=52.0)
    parser.add_argument("--lidar-horizontal-resolution", type=float, default=2.0)
    parser.add_argument("--lidar-min-range", type=float, default=0.10)
    parser.add_argument("--lidar-max-range", type=float, default=12.0)
    parser.add_argument("--planner-floor-filter-max-z", type=float, default=0.05)
    parser.add_argument("--video-path", type=Path)
    parser.add_argument("--video-fps", type=int, default=25)
    parser.add_argument("--video-frame-stride", type=int, default=2)
    parser.add_argument("--acceptance-config", type=Path)
    parser.add_argument("--contact-force-threshold", type=float, default=5.0)
    parser.add_argument("--collision-force-threshold", type=float, default=75.0)
    parser.add_argument("--max-step-wall-seconds", type=float, default=5.0)
    parser.add_argument("--connection-ready-timeout-seconds", type=float, default=10.0)
    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    if not args.checkpoint.is_file():
        raise SystemExit(f"required immutable checkpoint is missing: {args.checkpoint}")
    if not (args.vendored_rsl_rl / "rsl_rl" / "env" / "vec_env.py").is_file():
        raise SystemExit(
            f"required complete pinned V12 RSL-RL runtime is missing: {args.vendored_rsl_rl}"
        )
    if args.acceptance_config is not None and not args.acceptance_config.is_file():
        raise SystemExit(
            f"required frozen acceptance config is missing: {args.acceptance_config}"
        )
    from isaaclab.app import AppLauncher

    simulation_app = AppLauncher(
        headless=True,
        enable_cameras=args.video_path is not None,
        device=args.device,
    ).app
    try:
        return _run(args)
    finally:
        simulation_app.close()


if __name__ == "__main__":
    raise SystemExit(main())
