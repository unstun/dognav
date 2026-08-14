"""Qualify the one allowed V12 model_149999 fallback in its pinned runtime."""

import argparse
import inspect
import json
import math
from pathlib import Path
import time
import xml.etree.ElementTree as ET

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
PINNED_SENSOR_RIG_CANONICAL_SHA256 = (
    "d0a1be09f018c0ab31df26f69ad8e700bd88ec06ae5b0f4dfbcc4fddf21cec80"
)
PINNED_SENSOR_RIG_ISAAC_SHA256 = (
    "803d552703bcc4f72ce15f38b95bc3f62e3e4ada0b42bf3ecf71b32b6590bb9d"
)
PINNED_V12_ROBOT_ASSET_SHA256 = (
    "178428b97e7d0820e93c200b333f39f0b3b60a81f97d99cd06559d8957c58865"
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
MID360_FRAME = "mid360_scan_frame"
D435I_FRAME = "d435i_depth_optical_frame"
SENSOR_RIG_REQUIRED_LINKS = (
    "TORSO",
    "pro_interface_link",
    "sensor_carrier_link",
    "s410_guard_link",
    "mid360_body_link",
    MID360_FRAME,
    "d435i_body_link",
    D435I_FRAME,
)
# The sensor's own housing is deliberately omitted from its ray-cast targets:
# the optical origin is inside that geometry. These are the surrounding bodies
# that can physically occlude each sensor in the pinned assembly.
MID360_SELF_OCCLUSION_LINKS = (
    "TORSO",
    "pro_interface_link",
    "sensor_carrier_link",
    "s410_guard_link",
    "d435i_body_link",
)
D435I_SELF_OCCLUSION_LINKS = (
    "TORSO",
    "pro_interface_link",
    "sensor_carrier_link",
    "s410_guard_link",
    "mid360_body_link",
)


def _rgb_frame(frame):
    import numpy as np

    if frame is None:
        raise AdapterFailure("renderer returned no RGB frame")
    if frame.ndim != 3 or frame.shape[2] not in (3, 4):
        raise AdapterFailure(f"unexpected RGB frame shape: {frame.shape}")
    return np.asarray(frame[:, :, :3], dtype=np.uint8)


def _write_depth_artifacts(output_dir, frame, metadata, maximum_range):
    import imageio.v2 as imageio
    import numpy as np

    depth_m = np.asarray(frame.numpy(), dtype=np.float32)
    npy_path = output_dir / "d435i_depth_frame_m.npy"
    millimetres_path = output_dir / "d435i_depth_frame_mm.png"
    preview_path = output_dir / "d435i_depth_preview.png"
    np.save(npy_path, depth_m, allow_pickle=False)
    depth_mm = np.rint(np.clip(depth_m, 0.0, maximum_range) * 1000.0).astype(
        np.uint16
    )
    imageio.imwrite(millimetres_path, depth_mm)
    valid = np.isfinite(depth_m) & (depth_m < maximum_range)
    preview = np.zeros(depth_m.shape, dtype=np.uint8)
    if np.any(valid):
        scaled = 1.0 - np.clip(depth_m[valid] / maximum_range, 0.0, 1.0)
        preview[valid] = np.rint(32.0 + 223.0 * scaled).astype(np.uint8)
    imageio.imwrite(preview_path, preview)
    artifact_metadata = dict(metadata)
    artifact_metadata["artifacts"] = {
        "depth_metres_npy": {
            "path": npy_path.name,
            "sha256": _sha256(npy_path),
            "bytes": npy_path.stat().st_size,
        },
        "depth_millimetres_png": {
            "path": millimetres_path.name,
            "sha256": _sha256(millimetres_path),
            "bytes": millimetres_path.stat().st_size,
            "invalid_or_clipped_value_mm": int(round(maximum_range * 1000.0)),
        },
        "human_preview_png": {
            "path": preview_path.name,
            "sha256": _sha256(preview_path),
            "bytes": preview_path.stat().st_size,
            "display_rule": "nearer valid depth is brighter; invalid is black",
        },
    }
    metadata_path = output_dir / "d435i_depth_frame_metadata.json"
    _write_json(metadata_path, artifact_metadata)
    return artifact_metadata


def _sensor_rig_enabled(args) -> bool:
    return args.robot_asset is not None


def _urdf_contract(path: Path):
    root = ET.parse(path).getroot()
    links = root.findall("link")
    joints = root.findall("joint")
    mass_by_link = {}
    inertia_by_link = {}
    collision_count_by_link = {}
    mesh_files = {}
    links_without_inertial = []
    for link in links:
        name = link.attrib["name"]
        inertial = link.find("inertial")
        if inertial is None or inertial.find("mass") is None:
            links_without_inertial.append(name)
        else:
            mass_by_link[name] = float(inertial.find("mass").attrib["value"])
            inertia = inertial.find("inertia")
            if inertia is not None:
                inertia_by_link[name] = {
                    key: float(inertia.attrib[key])
                    for key in ("ixx", "ixy", "ixz", "iyy", "iyz", "izz")
                }
        collision_count_by_link[name] = len(link.findall("collision"))
        for mesh in link.findall(".//mesh"):
            filename = mesh.attrib["filename"]
            mesh_path = (path.parent / filename).resolve()
            if not mesh_path.is_file():
                raise AdapterFailure(f"URDF mesh is missing: {mesh_path}")
            mesh_files[filename] = {
                "sha256": _sha256(mesh_path),
                "bytes": mesh_path.stat().st_size,
            }
    movable_joint_count = sum(
        joint.attrib.get("type") not in ("fixed", "floating") for joint in joints
    )
    return {
        "robot_name": root.attrib.get("name"),
        "link_count": len(links),
        "joint_count": len(joints),
        "movable_joint_count": movable_joint_count,
        "fixed_joint_count": sum(
            joint.attrib.get("type") == "fixed" for joint in joints
        ),
        "total_declared_mass_kg": sum(mass_by_link.values()),
        "mass_by_link_kg": mass_by_link,
        "inertia_by_link_kg_m2": inertia_by_link,
        "collision_count": sum(collision_count_by_link.values()),
        "collision_count_by_link": collision_count_by_link,
        "links_without_inertial": links_without_inertial,
        "referenced_meshes": mesh_files,
    }


def _candidate_name(args) -> str:
    if _sensor_rig_enabled(args):
        return "V12 model_149999 on Lite3 Pro sensor rig v3"
    return "V12 model_149999 fallback"


def _asset_identity(args):
    if not _sensor_rig_enabled(args):
        return {
            "mode": "legacy_v12_task_asset",
            "asset_path": None,
            "asset_sha256": None,
            "canonical_asset_path": None,
            "canonical_asset_sha256": None,
        }
    canonical_contract = _urdf_contract(args.canonical_robot_asset.resolve())
    isaac_contract = _urdf_contract(args.robot_asset.resolve())
    expected_topology = (24, 23, 12)
    for label, contract in (
        ("canonical", canonical_contract),
        ("Isaac-safe", isaac_contract),
    ):
        observed_topology = (
            contract["link_count"],
            contract["joint_count"],
            contract["movable_joint_count"],
        )
        if observed_topology != expected_topology:
            raise AdapterFailure(
                f"{label} sensor-rig topology mismatch: {observed_topology}"
            )
        if contract["collision_count"] != 29:
            raise AdapterFailure(
                f"{label} sensor-rig collision count mismatch: "
                f"{contract['collision_count']}"
            )
    if isaac_contract["links_without_inertial"]:
        raise AdapterFailure("Isaac-safe sensor-rig still has inertial-less links")
    return {
        "mode": "v12_policy_on_pinned_sensor_rig",
        "asset_path": str(args.robot_asset.resolve()),
        "asset_sha256": _sha256(args.robot_asset),
        "canonical_asset_path": str(args.canonical_robot_asset.resolve()),
        "canonical_asset_sha256": _sha256(args.canonical_robot_asset),
        "merge_fixed_joints": False,
        "required_links": list(SENSOR_RIG_REQUIRED_LINKS),
        "canonical_urdf_contract": canonical_contract,
        "isaac_urdf_contract": isaac_contract,
        "composition_boundary": (
            "Only the V12 robot spawn asset and fixed-joint preservation are "
            "changed; checkpoint, policy loader, observations, actions, "
            "actuators, default pose, command schedule, and controller remain V12."
        ),
    }


def _depth_gate(depth_records):
    checks = {
        "frames_present": bool(depth_records),
        "timestamps_advance": len(depth_records) >= 2
        and all(
            right["sim_time_seconds"] > left["sim_time_seconds"]
            for left, right in zip(depth_records, depth_records[1:])
        ),
        "finite_depth": bool(depth_records)
        and all(row["nonfinite_depth_count"] == 0 for row in depth_records),
        "valid_depth_returns": bool(depth_records)
        and max(row["valid_depth_pixel_count"] for row in depth_records) > 0,
        "obstacle_returns": bool(depth_records)
        and max(row["obstacle_surface_pixel_count"] for row in depth_records) > 0,
        "intrinsics_present": bool(depth_records)
        and all(len(row["intrinsic_matrix"]) == 3 for row in depth_records),
    }
    pose_displacement = 0.0
    if len(depth_records) >= 2:
        pose_displacement = math.dist(
            depth_records[0]["sensor_position_w"],
            depth_records[-1]["sensor_position_w"],
        )
    checks["pose_displacement_m_value"] = pose_displacement
    checks["pose_dependent_frame"] = pose_displacement >= 0.10
    required = (
        "frames_present",
        "timestamps_advance",
        "finite_depth",
        "valid_depth_returns",
        "obstacle_returns",
        "intrinsics_present",
        "pose_dependent_frame",
    )
    return checks, all(bool(checks[name]) for name in required)


def _capture_v12_task_contract(env_cfg):
    """Fail closed unless the registry still resolves the pinned V12 controller."""

    robot_cfg = env_cfg.scene.robot
    original_asset = Path(robot_cfg.spawn.asset_path).resolve()
    if not original_asset.is_file():
        raise AdapterFailure(f"pinned V12 task asset is missing: {original_asset}")
    original_asset_sha256 = _sha256(original_asset)
    if original_asset_sha256 != PINNED_V12_ROBOT_ASSET_SHA256:
        raise AdapterFailure("pinned V12 task asset hash mismatch before composition")
    expected_joint_pos = {
        ".*HipX_joint": 0.0,
        ".*HipY_joint": -0.8,
        ".*Knee_joint": 1.6,
    }
    actual_joint_pos = dict(robot_cfg.init_state.joint_pos)
    if tuple(robot_cfg.init_state.pos) != (0.0, 0.0, 0.35):
        raise AdapterFailure("V12 default base pose changed before composition")
    if actual_joint_pos != expected_joint_pos:
        raise AdapterFailure("V12 default joint pose changed before composition")
    actuator_contract = {}
    for name, expected_effort, expected_velocity in (
        ("Hip", 24.0, 26.2),
        ("Knee", 36.0, 17.3),
    ):
        if name not in robot_cfg.actuators:
            raise AdapterFailure(f"V12 actuator group is missing: {name}")
        actuator = robot_cfg.actuators[name]
        observed = {
            "class": type(actuator).__name__,
            "effort_limit": float(actuator.effort_limit),
            "velocity_limit": float(actuator.velocity_limit),
            "stiffness": float(actuator.stiffness),
            "damping": float(actuator.damping),
            "min_delay": int(actuator.min_delay),
            "max_delay": int(actuator.max_delay),
        }
        if observed["class"] != "Lite3ActuatorCfg":
            raise AdapterFailure(f"V12 actuator class changed for {name}")
        if (
            observed["effort_limit"] != expected_effort
            or observed["velocity_limit"] != expected_velocity
            or observed["stiffness"] != 20.0
            or observed["damping"] != 0.5
            or observed["min_delay"] != 0
            or observed["max_delay"] != 4
        ):
            raise AdapterFailure(f"V12 actuator contract changed for {name}")
        actuator_contract[name] = observed
    return {
        "registry_task": DEFAULT_TASK,
        "original_robot_asset_path": str(original_asset),
        "original_robot_asset_sha256": original_asset_sha256,
        "default_base_position_m": [0.0, 0.0, 0.35],
        "default_joint_position_by_regex": expected_joint_pos,
        "actuators": actuator_contract,
        "policy_observation_dimension": POLICY_OBSERVATION_DIMENSION,
        "action_dimension": 12,
    }


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
    if _sensor_rig_enabled(args):
        # V3 is a cross-composition test, not a new policy bundle. Preserve the
        # complete V12 task configuration and replace only the physical URDF.
        env_cfg.scene.robot.spawn.asset_path = str(args.robot_asset.resolve())
        env_cfg.scene.robot.spawn.merge_fixed_joints = False
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
    from isaaclab.sensors.ray_caster import MultiMeshRayCasterCameraCfg

    pitch_radians = math.radians(args.sensor_pitch_degrees)
    sensor_rotation_wxyz = (
        math.cos(pitch_radians / 2.0),
        0.0,
        math.sin(pitch_radians / 2.0),
        0.0,
    )
    sensor_rig = _sensor_rig_enabled(args)
    environment_targets = [GROUND_MESH_PRIM]
    if args.course == "single_box":
        environment_targets.append(OBSTACLE_MESH_PRIM)
    lidar_targets = list(environment_targets)
    if sensor_rig:
        lidar_targets.extend(
            MultiMeshRayCasterCfg.RaycastTargetCfg(
                prim_expr=f"{{ENV_REGEX_NS}}/Robot/{link}/visuals",
                merge_prim_meshes=True,
                track_mesh_transforms=True,
            )
            for link in MID360_SELF_OCCLUSION_LINKS
        )
    env_cfg.scene.navigation_lidar = MultiMeshRayCasterCfg(
        prim_path=(
            f"{{ENV_REGEX_NS}}/Robot/{MID360_FRAME}"
            if sensor_rig
            else "{ENV_REGEX_NS}/Robot/TORSO"
        ),
        update_period=args.sensor_period,
        offset=MultiMeshRayCasterCfg.OffsetCfg(
            pos=(0.0, 0.0, 0.0) if sensor_rig else tuple(args.sensor_translation),
            rot=(1.0, 0.0, 0.0, 0.0) if sensor_rig else sensor_rotation_wxyz,
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
        mesh_prim_paths=lidar_targets,
        update_mesh_ids=False,
        debug_vis=False,
    )
    if sensor_rig:
        depth_targets = list(environment_targets)
        depth_targets.extend(
            MultiMeshRayCasterCfg.RaycastTargetCfg(
                prim_expr=f"{{ENV_REGEX_NS}}/Robot/{link}/visuals",
                merge_prim_meshes=True,
                track_mesh_transforms=True,
            )
            for link in D435I_SELF_OCCLUSION_LINKS
        )
        env_cfg.scene.navigation_depth_camera = MultiMeshRayCasterCameraCfg(
            prim_path=f"{{ENV_REGEX_NS}}/Robot/{D435I_FRAME}",
            update_period=args.depth_period,
            offset=MultiMeshRayCasterCameraCfg.OffsetCfg(
                pos=(0.0, 0.0, 0.0),
                rot=(1.0, 0.0, 0.0, 0.0),
                convention="ros",
            ),
            data_types=["distance_to_image_plane"],
            depth_clipping_behavior="max",
            pattern_cfg=patterns.PinholeCameraPatternCfg(
                focal_length=args.depth_focal_length,
                horizontal_aperture=args.depth_horizontal_aperture,
                width=args.depth_width,
                height=args.depth_height,
            ),
            mesh_prim_paths=depth_targets,
            update_mesh_ids=False,
            max_distance=args.depth_max_range,
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
    from isaaclab_tasks.utils.parse_cfg import load_cfg_from_registry

    vendored_package_dir = _activate_vendored_rsl_rl(args.vendored_rsl_rl)
    expected_policy_source = vendored_package_dir / "modules" / "actor_critic_moe_cts.py"
    from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper

    if args.source_commit != PINNED_SOURCE_COMMIT:
        raise AdapterFailure("source commit is not the pinned V12 fallback")
    checkpoint_sha256 = _sha256(args.checkpoint)
    if checkpoint_sha256 != PINNED_CHECKPOINT_SHA256:
        raise AdapterFailure("V12 fallback checkpoint hash mismatch")
    asset_identity = _asset_identity(args)
    if _sensor_rig_enabled(args):
        if asset_identity["asset_sha256"] != PINNED_SENSOR_RIG_ISAAC_SHA256:
            raise AdapterFailure("Isaac-safe Lite3 sensor-rig URDF hash mismatch")
        if (
            asset_identity["canonical_asset_sha256"]
            != PINNED_SENSOR_RIG_CANONICAL_SHA256
        ):
            raise AdapterFailure("canonical Lite3 sensor-rig URDF hash mismatch")
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
    sensor_rig = _sensor_rig_enabled(args)
    lidar_translation = (0.0, 0.0, 0.0) if sensor_rig else args.sensor_translation
    lidar_rotation = (1.0, 0.0, 0.0, 0.0) if sensor_rig else sensor_rotation_wxyz
    raycast_targets = [GROUND_MESH_PRIM]
    if args.course == "single_box":
        raycast_targets.append(OBSTACLE_MESH_PRIM)
    identity = {
        "schema_version": 2 if sensor_rig else 1,
        "candidate": _candidate_name(args),
        "source_commit": args.source_commit,
        "checkpoint_sha256": checkpoint_sha256,
        "robot_asset": asset_identity,
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
            "declared_device": "MID-360-like geometric ray model" if sensor_rig else None,
            "parent_frame": MID360_FRAME if sensor_rig else "TORSO",
            "translation_m": lidar_translation,
            "rotation_wxyz": lidar_rotation,
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
            "raycast_targets": raycast_targets,
            "self_occlusion_links": (
                list(MID360_SELF_OCCLUSION_LINKS) if sensor_rig else []
            ),
            "self_occlusion_treatment": (
                "Ray-cast against moving rig geometry; discard a blocking self hit "
                "inside the declared minimum range without allowing the ray to pass "
                "through to environment geometry."
                if sensor_rig
                else "not modelled by the legacy V12 sensor"
            ),
            "obstacle_return_classification": (
                "finite hit above floor filter inside the only non-ground mesh bounds"
            ),
        },
    }
    if sensor_rig:
        identity["depth_camera"] = {
            "backend": "IsaacLab MultiMeshRayCasterCameraCfg",
            "declared_device": "D435i-like provisional ray-cast depth",
            "parent_frame": D435I_FRAME,
            "translation_m": [0.0, 0.0, 0.0],
            "rotation_wxyz": [1.0, 0.0, 0.0, 0.0],
            "orientation_convention": "ros optical frame",
            "width": args.depth_width,
            "height": args.depth_height,
            "focal_length": args.depth_focal_length,
            "horizontal_aperture": args.depth_horizontal_aperture,
            "minimum_range_m": args.depth_min_range,
            "maximum_range_m": args.depth_max_range,
            "period_seconds": args.depth_period,
            "raycast_targets": raycast_targets,
            "self_occlusion_links": list(D435I_SELF_OCCLUSION_LINKS),
            "self_occlusion_treatment": (
                "Ray-cast against moving rig geometry; replace blocking near-self "
                "pixels with the maximum-depth invalid sentinel."
            ),
            "intrinsics_status": (
                "provisional; no live D435i depth CameraInfo is available. The "
                "recorded color CameraInfo is intentionally not reused."
            ),
            "navigation_use": (
                "generated and logged concurrently; not fused into SCAN in v3"
            ),
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
    depth_records = []
    best_depth_frame = None
    best_depth_metadata = None
    telemetry_sequence = 0
    dropped_frames = 0
    video_writer = None
    video_frame_count = 0
    runtime_rates = {}
    try:
        __import__("robot_lab.tasks")
        env_cfg = load_cfg_from_registry(args.task, "env_cfg_entry_point")
        agent_cfg = load_cfg_from_registry(args.task, "rsl_rl_cfg_entry_point")
        v12_task_contract = _capture_v12_task_contract(env_cfg)
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
        depth_camera = (
            base_env.scene.sensors["navigation_depth_camera"]
            if sensor_rig
            else None
        )
        contact = base_env.scene.sensors["contact_forces"]
        contact_foot_ids, contact_names = contact.find_bodies(
            ["FL_FOOT", "FR_FOOT", "HL_FOOT", "HR_FOOT"], preserve_order=True
        )
        if len(contact_foot_ids) != 4:
            raise AdapterFailure(f"V12 contact foot binding mismatch: {contact_names}")
        missing_rig_links = []
        if sensor_rig:
            missing_rig_links = [
                name for name in SENSOR_RIG_REQUIRED_LINKS if name not in robot.body_names
            ]
            if missing_rig_links:
                raise AdapterFailure(
                    f"sensor-rig links absent after Isaac import: {missing_rig_links}"
                )
        default_joint_position = {
            name: float(robot.data.default_joint_pos[0, index].item())
            for index, name in enumerate(robot.joint_names)
        }
        for name, position in default_joint_position.items():
            expected = 0.0 if "HipX" in name else (-0.8 if "HipY" in name else 1.6)
            if abs(position - expected) > 1.0e-6:
                raise AdapterFailure(
                    f"V12 runtime default joint pose changed for {name}: {position}"
                )
        runtime_mass_by_link = {
            name: float(robot.data.default_mass[0, index].item())
            for index, name in enumerate(robot.body_names)
        }
        runtime_inertia_by_link = {
            name: _tensor_list(robot.data.default_inertia[0, index])
            for index, name in enumerate(robot.body_names)
        }
        imported_prim_paths = []
        imported_collision_prim_paths = []
        imported_joint_prim_paths = []
        imported_fixed_joint_prim_paths = []
        imported_movable_joint_prim_paths = []
        imported_geometry_prim_records = []
        if sensor_rig:
            import omni.usd
            from pxr import Usd, UsdPhysics

            stage = omni.usd.get_context().get_stage()
            robot_prim_prefix = "/World/envs/env_0/Robot"
            robot_prim = stage.GetPrimAtPath(robot_prim_prefix)
            if not robot_prim.IsValid():
                raise AdapterFailure("imported sensor-rig robot prim is missing")
            for prim in Usd.PrimRange(robot_prim, Usd.TraverseInstanceProxies()):
                prim_path = str(prim.GetPath())
                imported_prim_paths.append(prim_path)
                if prim.HasAPI(UsdPhysics.CollisionAPI):
                    imported_collision_prim_paths.append(prim_path)
                if prim.GetTypeName() in (
                    "Capsule",
                    "Cone",
                    "Cube",
                    "Cylinder",
                    "Mesh",
                    "Sphere",
                ):
                    imported_geometry_prim_records.append(
                        {
                            "path": prim_path,
                            "type": prim.GetTypeName(),
                            "applied_schemas": list(prim.GetAppliedSchemas()),
                        }
                    )
                if prim.IsA(UsdPhysics.Joint):
                    imported_joint_prim_paths.append(prim_path)
                    if prim.IsA(UsdPhysics.FixedJoint):
                        imported_fixed_joint_prim_paths.append(prim_path)
                    else:
                        imported_movable_joint_prim_paths.append(prim_path)
            expected_runtime_mass = asset_identity["isaac_urdf_contract"][
                "total_declared_mass_kg"
            ]
            observed_runtime_mass = sum(runtime_mass_by_link.values())
            if len(robot.body_names) != 24:
                raise AdapterFailure(
                    f"sensor-rig runtime body count is {len(robot.body_names)}, not 24"
                )
            if len(imported_joint_prim_paths) != 23:
                raise AdapterFailure(
                    "sensor-rig runtime USD joint count is "
                    f"{len(imported_joint_prim_paths)}, not 23"
                )
            if len(imported_fixed_joint_prim_paths) != 11:
                raise AdapterFailure(
                    "sensor-rig runtime USD fixed-joint count is "
                    f"{len(imported_fixed_joint_prim_paths)}, not 11"
                )
            if len(imported_movable_joint_prim_paths) != 12:
                raise AdapterFailure(
                    "sensor-rig runtime USD movable-joint count is "
                    f"{len(imported_movable_joint_prim_paths)}, not 12"
                )
            if len(imported_collision_prim_paths) != 29:
                raise AdapterFailure(
                    "sensor-rig runtime collision-prim count is "
                    f"{len(imported_collision_prim_paths)}, not 29"
                )
            if abs(observed_runtime_mass - expected_runtime_mass) > 1.0e-5:
                raise AdapterFailure(
                    "sensor-rig runtime mass differs from the Isaac URDF: "
                    f"{observed_runtime_mass} != {expected_runtime_mass}"
                )
            for frame_name in (MID360_FRAME, D435I_FRAME):
                if abs(runtime_mass_by_link[frame_name] - 1.0e-6) > 1.0e-8:
                    raise AdapterFailure(
                        f"{frame_name} received an unexpected runtime mass: "
                        f"{runtime_mass_by_link[frame_name]}"
                    )
        runtime_composition = {
            "schema_version": 1,
            "candidate": _candidate_name(args),
            "v12_task_contract": v12_task_contract,
            "configured_robot_asset": asset_identity,
            "runtime_body_names": list(robot.body_names),
            "runtime_joint_names": list(robot.joint_names),
            "runtime_default_joint_position": default_joint_position,
            "runtime_mass_by_link_kg": runtime_mass_by_link,
            "runtime_total_mass_kg": sum(runtime_mass_by_link.values()),
            "runtime_inertia_by_link_kg_m2_row_major": runtime_inertia_by_link,
            "missing_required_sensor_rig_links": missing_rig_links,
            "imported_prim_paths": imported_prim_paths,
            "imported_collision_prim_paths": imported_collision_prim_paths,
            "imported_joint_prim_paths": imported_joint_prim_paths,
            "imported_fixed_joint_prim_paths": imported_fixed_joint_prim_paths,
            "imported_movable_joint_prim_paths": imported_movable_joint_prim_paths,
            "imported_geometry_prim_records": imported_geometry_prim_records,
            "silent_default_mass_check": {
                "mid360_scan_frame_mass_kg": runtime_mass_by_link.get(MID360_FRAME),
                "d435i_depth_optical_frame_mass_kg": runtime_mass_by_link.get(
                    D435I_FRAME
                ),
                "expected_frame_mass_kg": 1.0e-6,
                "status": "pass" if sensor_rig else "not_applicable",
            },
            "navigation_lidar_prim_path": lidar.cfg.prim_path,
            "navigation_depth_camera_prim_path": (
                None if depth_camera is None else depth_camera.cfg.prim_path
            ),
        }
        _write_json(output_dir / "runtime_composition.json", runtime_composition)
        previous_actions = torch.zeros((1, 12), device=base_env.device)
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
        depth_metrics_path = output_dir / "depth_metrics.jsonl"
        with metrics_path.open("w", encoding="utf-8") as metrics_file, \
                sensor_metrics_path.open("w", encoding="utf-8") as sensor_metrics_file, \
                depth_metrics_path.open("w", encoding="utf-8") as depth_metrics_file:
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
                    sensor_position = lidar.data.pos_w[0]
                    sensor_quaternion_wxyz_tensor = lidar.data.quat_w[0]
                    sensor_position_values = _tensor_list(sensor_position)
                    sensor_quaternion_values = _tensor_list(
                        sensor_quaternion_wxyz_tensor
                    )
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
                    hit_ranges = torch.linalg.vector_norm(
                        hits_w - sensor_position.unsqueeze(0), dim=-1
                    )
                    self_occluded_hits = finite_hits & (
                        hit_ranges < args.lidar_min_range
                    )
                    floor_filtered_hits = finite_hits & (
                        hits_w[:, 2] <= args.planner_floor_filter_max_z
                    )
                    ground_hits = finite_hits & ~self_occluded_hits & torch.isclose(
                        hits_w[:, 2], hits_w.new_tensor(0.0), atol=0.03, rtol=0.0
                    )
                    obstacle_hits = torch.zeros_like(finite_hits)
                    if args.course == "single_box":
                        center = hits_w.new_tensor(COURSE_OBSTACLE_CENTER)
                        half_size = 0.5 * hits_w.new_tensor(COURSE_OBSTACLE_SIZE)
                        obstacle_hits = (
                            finite_hits
                            & ~self_occluded_hits
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
                        "self_occluded_hit_count": int(
                            self_occluded_hits.sum().item()
                        ),
                        "planner_floor_filtered_hit_count": int(
                            floor_filtered_hits.sum().item()
                        ),
                        "ground_hit_count": int(ground_hits.sum().item()),
                        "obstacle_surface_hit_count": int(obstacle_hits.sum().item()),
                        "unexpected_above_floor_hit_count": int(
                            (
                                finite_hits
                                & ~self_occluded_hits
                                & (hits_w[:, 2] > args.planner_floor_filter_max_z)
                                & ~obstacle_hits
                            ).sum().item()
                        ),
                        "centroid_sensor": centroid,
                    }
                    sensor_records.append(sensor_row)
                    sensor_metrics_file.write(json.dumps(sensor_row, sort_keys=True) + "\n")
                    sensor_metrics_file.flush()
                    if depth_camera is not None:
                        depth_camera.update(dt=0.0, force_recompute=True)
                        depth_data = depth_camera.data
                        raw_depth = depth_data.output["distance_to_image_plane"][
                            0, ..., 0
                        ].clone()
                        camera_hits_w = depth_camera.ray_hits_w[0].reshape(-1, 3)
                        camera_position = depth_data.pos_w[0]
                        camera_ranges = torch.linalg.vector_norm(
                            camera_hits_w - camera_position.unsqueeze(0), dim=-1
                        )
                        finite_camera_hits = torch.isfinite(camera_hits_w).all(dim=-1)
                        self_occluded_pixels = finite_camera_hits & (
                            camera_ranges < args.depth_min_range
                        )
                        depth_flat = raw_depth.reshape(-1)
                        depth_flat[self_occluded_pixels] = args.depth_max_range
                        finite_depth = torch.isfinite(depth_flat)
                        valid_depth = (
                            finite_depth
                            & (depth_flat >= args.depth_min_range)
                            & (depth_flat < args.depth_max_range)
                        )
                        obstacle_pixels = torch.zeros_like(finite_camera_hits)
                        if args.course == "single_box":
                            center = camera_hits_w.new_tensor(COURSE_OBSTACLE_CENTER)
                            half_size = 0.5 * camera_hits_w.new_tensor(
                                COURSE_OBSTACLE_SIZE
                            )
                            obstacle_pixels = (
                                finite_camera_hits
                                & ~self_occluded_pixels
                                & (
                                    (camera_hits_w >= center - half_size - 0.01)
                                    & (camera_hits_w <= center + half_size + 0.01)
                                ).all(dim=-1)
                            )
                        valid_values = depth_flat[valid_depth]
                        depth_row = {
                            "step": step,
                            "sim_time_seconds": float(base_env.sim.current_time),
                            "sensor_position_w": _tensor_list(camera_position),
                            "sensor_quaternion_wxyz_ros": _tensor_list(
                                depth_data.quat_w_ros[0]
                            ),
                            "width": args.depth_width,
                            "height": args.depth_height,
                            "intrinsic_matrix": depth_data.intrinsic_matrices[0]
                            .detach()
                            .cpu()
                            .tolist(),
                            "pixel_count": int(depth_flat.numel()),
                            "nonfinite_depth_count": int(
                                (~finite_depth).sum().item()
                            ),
                            "valid_depth_pixel_count": int(valid_depth.sum().item()),
                            "self_occluded_pixel_count": int(
                                self_occluded_pixels.sum().item()
                            ),
                            "obstacle_surface_pixel_count": int(
                                obstacle_pixels.sum().item()
                            ),
                            "minimum_valid_depth_m": (
                                None
                                if valid_values.numel() == 0
                                else float(valid_values.min().item())
                            ),
                            "maximum_valid_depth_m": (
                                None
                                if valid_values.numel() == 0
                                else float(valid_values.max().item())
                            ),
                            "mean_valid_depth_m": (
                                None
                                if valid_values.numel() == 0
                                else float(valid_values.mean().item())
                            ),
                        }
                        depth_records.append(depth_row)
                        depth_metrics_file.write(
                            json.dumps(depth_row, sort_keys=True) + "\n"
                        )
                        depth_metrics_file.flush()
                        best_obstacle_count = (
                            -1
                            if best_depth_metadata is None
                            else best_depth_metadata["obstacle_surface_pixel_count"]
                        )
                        if (
                            depth_row["obstacle_surface_pixel_count"]
                            > best_obstacle_count
                        ):
                            best_depth_frame = raw_depth.detach().cpu().clone()
                            best_depth_metadata = dict(depth_row)
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
        # Signal the qualification client before closing its server-side stream.
        # Otherwise the client can correctly observe EOF during normal shutdown
        # but race with its stop event and misclassify teardown as a run error.
        if sink is not None:
            sink.stop()
        telemetry_server.stop()
        if video_writer is not None:
            try:
                video_writer.close()
            except BaseException as error:
                if runtime_error is None:
                    runtime_error = error
        if wrapped_env is not None:
            wrapped_env.close()

    if sink is not None and sink.error is not None and runtime_error is None:
        runtime_error = sink.error
    depth_artifact_metadata = None
    if sensor_rig and best_depth_frame is not None and best_depth_metadata is not None:
        try:
            depth_artifact_metadata = _write_depth_artifacts(
                output_dir,
                best_depth_frame,
                best_depth_metadata,
                args.depth_max_range,
            )
        except BaseException as error:
            if runtime_error is None:
                runtime_error = error
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
    depth_checks, depth_passed = _depth_gate(depth_records)
    report["depth_checks"] = depth_checks
    report["depth_artifact"] = depth_artifact_metadata
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
    if sensor_rig and (not sensor_passed or not depth_passed):
        report["status"] = "FAIL"
    report["candidate"] = _candidate_name(args)
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
    parser.add_argument(
        "--robot-asset",
        type=Path,
        help="Pinned Isaac-safe Lite3 Pro sensor-rig URDF for the v3 composition",
    )
    parser.add_argument(
        "--canonical-robot-asset",
        type=Path,
        help="Canonical pre-Isaac sensor-rig URDF used to prove asset lineage",
    )
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
    parser.add_argument("--depth-period", type=float, default=0.10)
    parser.add_argument("--depth-width", type=int, default=87)
    parser.add_argument("--depth-height", type=int, default=58)
    parser.add_argument("--depth-focal-length", type=float, default=24.0)
    parser.add_argument("--depth-horizontal-aperture", type=float, default=45.55)
    parser.add_argument("--depth-min-range", type=float, default=0.10)
    parser.add_argument("--depth-max-range", type=float, default=5.0)
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
    if (args.robot_asset is None) != (args.canonical_robot_asset is None):
        raise SystemExit(
            "--robot-asset and --canonical-robot-asset must be supplied together"
        )
    if _sensor_rig_enabled(args):
        if args.task != DEFAULT_TASK:
            raise SystemExit("the v3 sensor-rig composition requires the pinned V12 task")
        if not args.robot_asset.is_file():
            raise SystemExit(f"sensor-rig Isaac asset is missing: {args.robot_asset}")
        if not args.canonical_robot_asset.is_file():
            raise SystemExit(
                f"canonical sensor-rig asset is missing: {args.canonical_robot_asset}"
            )
        if _sha256(args.robot_asset) != PINNED_SENSOR_RIG_ISAAC_SHA256:
            raise SystemExit("sensor-rig Isaac asset hash mismatch")
        if (
            _sha256(args.canonical_robot_asset)
            != PINNED_SENSOR_RIG_CANONICAL_SHA256
        ):
            raise SystemExit("canonical sensor-rig asset hash mismatch")
        if abs(args.depth_period - args.sensor_period) > 1.0e-9:
            raise SystemExit("v3 lidar and depth periods must match")
        if args.depth_width <= 0 or args.depth_height <= 0:
            raise SystemExit("depth dimensions must be positive")
        if (
            args.depth_min_range < 0.0
            or args.depth_max_range <= args.depth_min_range
            or not all(
                math.isfinite(value)
                for value in (
                    args.depth_period,
                    args.depth_focal_length,
                    args.depth_horizontal_aperture,
                    args.depth_min_range,
                    args.depth_max_range,
                )
            )
        ):
            raise SystemExit("depth sensor parameters are invalid")
    from isaaclab.app import AppLauncher

    simulation_app = AppLauncher(
        headless=True,
        enable_cameras=args.video_path is not None or _sensor_rig_enabled(args),
        device=args.device,
    ).app
    try:
        return _run(args)
    finally:
        simulation_app.close()


if __name__ == "__main__":
    raise SystemExit(main())
