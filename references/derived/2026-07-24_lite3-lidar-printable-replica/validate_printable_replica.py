#!/usr/bin/env python3
"""Validate exported Lite3 printable-replica artifacts after file round-trip."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import sys
from typing import Any

import manifold3d as md
import numpy as np
import trimesh


ROOT = Path(__file__).resolve().parent
BUILD_ROOT = Path(os.environ.get("LITE3_PRINT_BUILD_ROOT", ROOT)).resolve()
PARAMETERS_PATH = Path(
    os.environ.get("LITE3_PRINT_PARAMS", ROOT / "print_parameters.json")
).resolve()
BUILD_REPORT_PATH = BUILD_ROOT / "reports" / "build_report.json"
VALIDATION_REPORT_PATH = BUILD_ROOT / "reports" / "validation_report.json"
MASTER_DIR = BUILD_ROOT / "models" / "master_1_1"
PRINT_DIR = BUILD_ROOT / "models" / "print_1_4"
REFERENCE_DIR = BUILD_ROOT / "models" / "reference"

EXPECTED_MASTER_COMPONENTS = {
    "camera_carrier_plate_master_1_1.stl": 1,
    "camera_fasteners_master_1_1.stl": 8,
    "camera_mount_bracket_master_1_1.stl": 1,
    "d435i_sensor_master_1_1.stl": 1,
    "front_camera_bar_master_1_1.stl": 1,
    "hip_master_1_1.stl": 1,
    "j17a_sensor_carrier_master_1_1.stl": 1,
    "j20a_adapter_master_1_1.stl": 1,
    "mid360_sensor_master_1_1.stl": 1,
    "s410_guard_master_1_1.stl": 1,
    "shank_master_1_1.stl": 1,
    "thigh_master_1_1.stl": 1,
    "torso_master_1_1.stl": 1,
    "upper_lidar_module_master_1_1.stl": 1,
}

EXPECTED_PRINT_COMPONENTS = {
    "ASSEMBLY_PINS.stl": 14,
    "CAMERA_CARRIER_PLATE.stl": 1,
    "CAMERA_FASTENERS.stl": 8,
    "CAMERA_MOUNT_BRACKET.stl": 1,
    "FL_HIP.stl": 1,
    "FL_SHANK.stl": 1,
    "FL_THIGH.stl": 1,
    "FRONT_CAMERA_BAR.stl": 1,
    "FR_HIP.stl": 1,
    "FR_SHANK.stl": 1,
    "FR_THIGH.stl": 1,
    "HL_HIP.stl": 1,
    "HL_SHANK.stl": 1,
    "HL_THIGH.stl": 1,
    "HR_HIP.stl": 1,
    "HR_SHANK.stl": 1,
    "HR_THIGH.stl": 1,
    "FACTORY_INTERFACE.stl": 1,
    "TORSO.stl": 1,
    "UPPER_LIDAR_MODULE.stl": 1,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists() and (candidate / "AGENTS.md").exists():
            return candidate
    raise RuntimeError(f"Could not find repository root above {start}")


def add_check(
    checks: list[dict[str, Any]],
    failures: list[str],
    name: str,
    passed: bool,
    detail: Any,
) -> None:
    checks.append({"name": name, "passed": bool(passed), "detail": detail})
    if not passed:
        failures.append(f"{name}: {detail}")


def mesh_roundtrip_metrics(path: Path) -> dict[str, Any]:
    loaded = trimesh.load_mesh(path, process=True, validate=True)
    if not isinstance(loaded, trimesh.Trimesh):
        raise TypeError(f"{path.name} did not load as one Trimesh")
    mesh = loaded
    edges = mesh.edges_sorted
    _, edge_counts = np.unique(edges, axis=0, return_counts=True)
    components = mesh.split(only_watertight=True)
    manifold = md.Manifold(
        md.Mesh64(
            np.asarray(mesh.vertices, dtype=np.float64),
            np.asarray(mesh.faces, dtype=np.uint64),
        )
    )
    return {
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "components": int(len(components)),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "finite_vertices": bool(np.isfinite(mesh.vertices).all()),
        "boundary_edges": int(np.count_nonzero(edge_counts == 1)),
        "nonmanifold_edges": int(np.count_nonzero(edge_counts > 2)),
        "degenerate_faces": int(np.count_nonzero(mesh.area_faces <= 1.0e-10)),
        "volume_mm3": float(abs(mesh.volume)),
        "bbox_min_mm": mesh.bounds[0].tolist(),
        "bbox_max_mm": mesh.bounds[1].tolist(),
        "bbox_size_mm": mesh.extents.tolist(),
        "manifold_status": str(manifold.status()),
    }


def validate_mesh_group(
    directory: Path,
    expected_components: dict[str, int],
    build_volume: np.ndarray | None,
    checks: list[dict[str, Any]],
    failures: list[str],
) -> dict[str, Any]:
    actual_names = {path.name for path in directory.glob("*.stl")}
    expected_names = set(expected_components)
    add_check(
        checks,
        failures,
        f"{directory.name}.exact_file_set",
        actual_names == expected_names,
        {
            "missing": sorted(expected_names - actual_names),
            "unexpected": sorted(actual_names - expected_names),
        },
    )
    result: dict[str, Any] = {}
    for name in sorted(expected_names):
        path = directory / name
        if not path.is_file():
            continue
        metrics = mesh_roundtrip_metrics(path)
        result[name] = metrics
        required = {
            "watertight": metrics["watertight"],
            "winding_consistent": metrics["winding_consistent"],
            "finite_vertices": metrics["finite_vertices"],
            "boundary_edges_zero": metrics["boundary_edges"] == 0,
            "nonmanifold_edges_zero": metrics["nonmanifold_edges"] == 0,
            "degenerate_faces_zero": metrics["degenerate_faces"] == 0,
            "positive_volume": metrics["volume_mm3"] > 0.0,
            "manifold3d_no_error": metrics["manifold_status"] == "Error.NoError",
            "component_count": (
                metrics["components"] == expected_components[name]
            ),
        }
        if build_volume is not None:
            required["fits_build_volume"] = bool(
                np.all(np.asarray(metrics["bbox_size_mm"]) <= build_volume + 1.0e-6)
            )
            required["rests_on_build_plane"] = (
                abs(float(metrics["bbox_min_mm"][2])) <= 1.0e-5
            )
        add_check(
            checks,
            failures,
            f"{directory.name}.{name}.geometry",
            all(required.values()),
            required,
        )
    return result


def scene_metrics(path: Path) -> dict[str, Any]:
    loaded = trimesh.load(path, force="scene", process=False)
    if not isinstance(loaded, trimesh.Scene):
        loaded = trimesh.Scene(loaded)
    bounds = np.asarray(loaded.bounds, dtype=float)
    if bounds.shape != (2, 3) or not np.isfinite(bounds).all():
        raise ValueError(f"Invalid scene bounds for {path.name}")
    result = {
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
        "geometry_count": int(len(loaded.geometry)),
        "node_names": sorted(loaded.graph.nodes_geometry),
        "bbox_size": (bounds[1] - bounds[0]).tolist(),
    }
    if path.suffix.lower() == ".3mf":
        topology = {}
        for name, mesh in sorted(loaded.geometry.items()):
            edges = mesh.edges_sorted
            _, edge_counts = np.unique(edges, axis=0, return_counts=True)
            topology[name] = {
                "watertight": bool(mesh.is_watertight),
                "winding_consistent": bool(mesh.is_winding_consistent),
                "boundary_edges": int(np.count_nonzero(edge_counts == 1)),
                "nonmanifold_edges": int(np.count_nonzero(edge_counts > 2)),
            }
        result["geometry_topology"] = topology
        result["all_geometries_watertight"] = all(
            item["watertight"]
            and item["winding_consistent"]
            and item["boundary_edges"] == 0
            and item["nonmanifold_edges"] == 0
            for item in topology.values()
        )
    return result


def main() -> int:
    config = load_json(PARAMETERS_PATH)
    build_report = load_json(BUILD_REPORT_PATH)
    repo_root = find_repo_root(ROOT)
    checks: list[dict[str, Any]] = []
    failures: list[str] = []

    add_check(
        checks,
        failures,
        "artifact_label",
        build_report.get("artifact_label") == "printable_static_replica",
        build_report.get("artifact_label"),
    )
    add_check(
        checks,
        failures,
        "parameters_hash",
        build_report.get("parameters_sha256") == sha256(PARAMETERS_PATH),
        {
            "reported": build_report.get("parameters_sha256"),
            "actual": sha256(PARAMETERS_PATH),
        },
    )

    for name, source in config["sources"].items():
        source_path = (repo_root / source["path"]).resolve()
        actual = sha256(source_path) if source_path.is_file() else None
        add_check(
            checks,
            failures,
            f"source_hash.{name}",
            actual == source["sha256"],
            {"expected": source["sha256"], "actual": actual, "path": str(source_path)},
        )

    output_hashes: dict[str, Any] = {}
    for name, output in build_report.get("outputs", {}).items():
        path = Path(output["path"])
        actual = sha256(path) if path.is_file() else None
        output_hashes[name] = {
            "reported": output["sha256"],
            "actual": actual,
            "size_bytes": path.stat().st_size if path.is_file() else None,
        }
        add_check(
            checks,
            failures,
            f"output_hash.{name}",
            actual == output["sha256"],
            output_hashes[name],
        )

    build_volume = np.asarray(config["print_profile"]["build_volume_mm"], dtype=float)
    master_metrics = validate_mesh_group(
        MASTER_DIR,
        EXPECTED_MASTER_COMPONENTS,
        None,
        checks,
        failures,
    )
    print_metrics = validate_mesh_group(
        PRINT_DIR,
        EXPECTED_PRINT_COMPONENTS,
        build_volume,
        checks,
        failures,
    )

    reference_files = {
        "lite3_lidar_1_1_reference.glb": "scene",
        "lite3_lidar_1_1_reference.3mf": "scene",
        "lite3_lidar_1_4_assembled.glb": "scene",
        "lite3_lidar_1_4_print_layout.glb": "scene",
        "lite3_lidar_1_4_assembled_reference.stl": "mesh",
    }
    reference_metrics: dict[str, Any] = {}
    for name, kind in reference_files.items():
        path = REFERENCE_DIR / name
        try:
            if kind == "scene":
                metrics = scene_metrics(path)
                passed = metrics["geometry_count"] > 0
                if path.suffix.lower() == ".3mf":
                    passed = (
                        passed
                        and metrics["all_geometries_watertight"]
                    )
            else:
                metrics = mesh_roundtrip_metrics(path)
                passed = (
                    metrics["watertight"]
                    and metrics["winding_consistent"]
                    and metrics["boundary_edges"] == 0
                    and metrics["nonmanifold_edges"] == 0
                    and metrics["volume_mm3"] > 0.0
                )
            reference_metrics[name] = metrics
            add_check(
                checks,
                failures,
                f"reference_import.{name}",
                passed,
                metrics,
            )
        except Exception as exc:
            add_check(
                checks,
                failures,
                f"reference_import.{name}",
                False,
                f"{type(exc).__name__}: {exc}",
            )

    tracks = build_report.get("body_geometry_tracks", {})
    visual_track = tracks.get("visual_reference", {})
    printable_track = tracks.get("printable_reference", {})
    track_rules = {
        "visual_body_source": visual_track.get("body_source"),
        "visual_output": visual_track.get("output"),
        "visual_print_ready": visual_track.get("print_ready"),
        "visual_ground_error_mm": visual_track.get("ground_error_mm"),
        "printable_body_source": printable_track.get("body_source"),
        "printable_output": printable_track.get("output"),
        "printable_print_ready": printable_track.get("print_ready"),
        "printable_ground_error_mm": printable_track.get("ground_error_mm"),
    }
    track_pass = (
        track_rules["visual_body_source"]
        == "official_high_resolution_urdf_dae"
        and track_rules["visual_output"]
        == "models/reference/lite3_lidar_1_1_reference.glb"
        and track_rules["visual_print_ready"] is False
        and isinstance(track_rules["visual_ground_error_mm"], (int, float))
        and abs(float(track_rules["visual_ground_error_mm"])) <= 1.0e-5
        and track_rules["printable_body_source"]
        == (
            "watertight_voxel_reconstruction_with_bounded_"
            "topology_preserving_smoothing"
        )
        and track_rules["printable_output"]
        == "models/reference/lite3_lidar_1_1_reference.3mf"
        and track_rules["printable_print_ready"] is True
        and isinstance(
            track_rules["printable_ground_error_mm"],
            (int, float),
        )
        and abs(float(track_rules["printable_ground_error_mm"])) <= 1.0e-5
    )
    add_check(
        checks,
        failures,
        "body_geometry.dual_track_contract",
        track_pass,
        track_rules,
    )

    visual_reference_metrics = reference_metrics.get(
        "lite3_lidar_1_1_reference.glb",
        {},
    )
    visual_reference_nodes = visual_reference_metrics.get("node_names", [])
    d435i_source_metrics = build_report.get("source_topology", {}).get(
        "d435i_ros_visual_mesh",
        {},
    )
    d435i_master_metrics = build_report.get(
        "master_reconstruction",
        {},
    ).get("d435i", {})
    d435i_camera_audit = build_report.get(
        "lidar_geometry_audit",
        {},
    ).get("camera_mounting", {})
    d435i_transform = np.asarray(
        d435i_camera_audit.get("source_to_robot_transform", []),
        dtype=float,
    )
    d435i_rules = {
        "visual_node_names": visual_reference_nodes,
        "official_visual_node_present": (
            "D435I_CAMERA" in visual_reference_nodes
        ),
        "print_proxy_absent_from_visual": (
            "FRONT_CAMERA_BAR" not in visual_reference_nodes
        ),
        "bracket_nodes_present": all(
            name in visual_reference_nodes
            for name in (
                "CAMERA_MOUNT_BRACKET",
                "CAMERA_CARRIER_PLATE",
                "CAMERA_RECEIVER_YOKE",
                "CAMERA_FASTENERS",
            )
        ),
        "print_adaptation_nodes_absent": all(
            name not in visual_reference_nodes
            for name in (
                "CAMERA_PRINT_BRACKET",
                "CAMERA_PRINT_CARRIER_PLATE",
                "CAMERA_PRINT_RECEIVER_YOKE",
                "CAMERA_PRINT_FASTENERS",
            )
        ),
        "synthetic_optics_absent": all(
            name not in visual_reference_nodes
            for name in ("D435I_FRONT_BEZEL", "CAMERA_LENSES")
        ),
        "source_bbox_mm": d435i_source_metrics.get("bbox_size_mm"),
        "source_faces": d435i_source_metrics.get("faces"),
        "source_watertight": d435i_source_metrics.get("watertight"),
        "master_voxel_pitch_mm": d435i_master_metrics.get(
            "voxel_pitch_mm"
        ),
        "master_watertight": d435i_master_metrics.get("watertight"),
        "master_connected_components": d435i_master_metrics.get(
            "connected_components"
        ),
        "master_to_source_p99_mm": d435i_master_metrics.get(
            "master_to_source_surface_distance",
            {},
        ).get("p99_mm"),
        "visual_geometry_source": d435i_camera_audit.get(
            "visual_geometry_source"
        ),
        "visual_print_ready": d435i_camera_audit.get(
            "visual_print_ready"
        ),
        "visible_collision_proxy": d435i_camera_audit.get(
            "visible_collision_proxy"
        ),
        "official_visual_to_factory_mounts_clearance_mm": (
            d435i_camera_audit.get(
                "official_visual_to_factory_mounts_clearance",
                {},
            ).get("minimum_mm")
        ),
        "print_camera_to_factory_mounts_intersection_mm3": (
            d435i_camera_audit.get(
                "print_camera_to_factory_mounts_intersection_mm3"
            )
        ),
        "source_to_robot_transform": d435i_camera_audit.get(
            "source_to_robot_transform"
        ),
    }
    d435i_master_p99 = d435i_rules["master_to_source_p99_mm"]
    d435i_pass = (
        d435i_rules["official_visual_node_present"]
        and d435i_rules["print_proxy_absent_from_visual"]
        and d435i_rules["bracket_nodes_present"]
        and d435i_rules["print_adaptation_nodes_absent"]
        and d435i_rules["synthetic_optics_absent"]
        and np.allclose(
            np.asarray(d435i_rules["source_bbox_mm"], dtype=float),
            np.asarray(
                config["lidar_module"]["parameters_mm"][
                    "d435i_ros_source_bbox"
                ]["value"],
                dtype=float,
            ),
            atol=1.0e-6,
            rtol=0.0,
        )
        and isinstance(d435i_rules["source_faces"], int)
        and int(d435i_rules["source_faces"]) > 200000
        and d435i_rules["source_watertight"] is False
        and math.isclose(
            float(d435i_rules["master_voxel_pitch_mm"]),
            float(
                config["official_sensor_reconstruction"][
                    "d435i_voxel_pitch_mm"
                ]
            ),
            abs_tol=1.0e-9,
        )
        and d435i_rules["master_watertight"] is True
        and d435i_rules["master_connected_components"] == 1
        and isinstance(d435i_master_p99, (int, float))
        and 0.0 <= float(d435i_master_p99) <= 0.5
        and d435i_rules["visual_geometry_source"]
        == "official_realsense_ros_d435_mesh_used_by_d435i_urdf"
        and d435i_rules["visual_print_ready"] is False
        and d435i_rules["visible_collision_proxy"]
        == (
            "source_derived_watertight_print_body_for_open_"
            "official_visual_mesh"
        )
        and isinstance(
            d435i_rules[
                "official_visual_to_factory_mounts_clearance_mm"
            ],
            (int, float),
        )
        and float(
            d435i_rules[
                "official_visual_to_factory_mounts_clearance_mm"
            ]
        )
        >= 0.5
        and isinstance(
            d435i_rules[
                "print_camera_to_factory_mounts_intersection_mm3"
            ],
            (int, float),
        )
        and abs(
            float(
                d435i_rules[
                    "print_camera_to_factory_mounts_intersection_mm3"
                ]
            )
        )
        <= 1.0e-3
        and d435i_transform.shape == (4, 4)
        and math.isclose(
            float(np.linalg.det(d435i_transform[:3, :3])),
            1.0,
            abs_tol=1.0e-6,
        )
    )
    add_check(
        checks,
        failures,
        "d435i.official_visual_and_source_derived_print_tracks",
        d435i_pass,
        d435i_rules,
    )

    smoothing_config = config["master_reconstruction"]["smoothing"]
    smoothing_rules = {}
    smoothing_pass = bool(smoothing_config["enabled"])
    for component in ("torso", "hip", "thigh", "shank"):
        smoothing = build_report["master_reconstruction"][component].get(
            "smoothing",
            {},
        )
        smoothing_rules[component] = smoothing
        displacement = smoothing.get("vertex_displacement_mm", {})
        smoothing_pass = (
            smoothing_pass
            and smoothing.get("enabled") is True
            and smoothing.get("method") == "trimesh.filter_taubin"
            and smoothing.get("iterations")
            == int(smoothing_config["iterations"])
            and isinstance(displacement.get("p99"), (int, float))
            and float(displacement["p99"])
            <= float(smoothing_config["maximum_p99_displacement_mm"])
            and isinstance(
                smoothing.get("volume_change_percent"),
                (int, float),
            )
            and abs(float(smoothing["volume_change_percent"]))
            <= float(
                smoothing_config[
                    "maximum_abs_volume_change_percent"
                ]
            )
        )
    add_check(
        checks,
        failures,
        "body_geometry.print_smoothing_bounded",
        smoothing_pass,
        smoothing_rules,
    )

    standing = build_report["standing_reference_1_1"]
    actual_envelope = np.asarray(standing["bbox_size_mm"], dtype=float)
    target_envelope = np.asarray(standing["official_target_mm"], dtype=float)
    tolerance = np.asarray(
        config["assembled_variant_envelope"]["acceptance_tolerance_mm"][
            "value"
        ],
        dtype=float,
    )
    envelope_delta = np.abs(actual_envelope - target_envelope)
    add_check(
        checks,
        failures,
        "standing_reference.envelope",
        bool(np.all(envelope_delta <= tolerance)),
        {
            "actual_mm": actual_envelope.tolist(),
            "target_mm": target_envelope.tolist(),
            "factory_official_target_mm": standing[
                "factory_official_target_mm"
            ],
            "height_target_evidence_class": standing[
                "height_target_evidence_class"
            ],
            "absolute_delta_mm": envelope_delta.tolist(),
            "tolerance_mm": tolerance.tolist(),
        },
    )
    add_check(
        checks,
        failures,
        "standing_reference.ground_alignment",
        abs(float(standing["ground_error_mm"])) <= 1.0e-5,
        standing["ground_error_mm"],
    )

    profile = config["print_profile"]
    sensor_feature_print_thickness = (
        float(
            config["official_sensor_reconstruction"][
                "minimum_declared_structural_feature_master_mm"
            ]
        )
        * float(profile["scale"])
    )
    feature_rules = {
        "official_sensor_feature_thickness_mm": (
            sensor_feature_print_thickness
        ),
        "minimum_feature_mm": float(profile["minimum_feature_mm"]),
        "pin_diameter_mm": float(profile["pin_diameter_mm"]),
        "pin_radial_clearance_mm": float(profile["pin_radial_clearance_mm"]),
        "joint_hole_radius_mm": float(profile["pin_diameter_mm"]) / 2.0
        + float(profile["pin_radial_clearance_mm"]),
    }
    feature_pass = (
        feature_rules["official_sensor_feature_thickness_mm"] + 1.0e-9
        >= feature_rules["minimum_feature_mm"]
        and feature_rules["pin_diameter_mm"] >= 2.4
        and feature_rules["pin_radial_clearance_mm"] >= 0.2
    )
    add_check(
        checks,
        failures,
        "print_profile.minimum_features_and_clearance",
        feature_pass,
        feature_rules,
    )

    lidar_parameters = config["lidar_module"]["parameters_mm"]
    radar_tilt_deg = float(lidar_parameters["j20a_tilt_deg"]["value"])
    camera_optical_axis = np.asarray(
        lidar_parameters["d435i_mount_axis_j17a_source"]["value"],
        dtype=float,
    )
    camera_optical_axis /= np.linalg.norm(camera_optical_axis)
    camera_tilt_deg = math.degrees(
        math.atan2(
            -float(camera_optical_axis[2]),
            float(camera_optical_axis[0]),
        )
    )
    radar_axis = [
        math.sin(math.radians(radar_tilt_deg)),
        0.0,
        math.cos(math.radians(radar_tilt_deg)),
    ]
    placement_rules = {
        "j20a_tilt_deg": radar_tilt_deg,
        "radar_axis": radar_axis,
        "sensor_assembly_origin_x_mm": float(
            lidar_parameters["sensor_assembly_origin"]["value"][0]
        ),
        "interface_center_x_mm": float(
            lidar_parameters["factory_interface_box_center"]["value"][0]
        ),
        "mid360_connector_yaw_deg": float(
            lidar_parameters["mid360_connector_yaw_deg"]["value"]
        ),
        "d435i_mount_tilt_y_deg": camera_tilt_deg,
        "camera_optical_axis": camera_optical_axis.tolist(),
    }
    placement_pass = (
        5.0 <= radar_tilt_deg <= 30.0
        and radar_axis[0] > 0.0
        and radar_axis[2] > 0.0
        and placement_rules["sensor_assembly_origin_x_mm"]
        > placement_rules["interface_center_x_mm"]
        and math.isclose(
            placement_rules["mid360_connector_yaw_deg"],
            180.0,
            abs_tol=1.0e-6,
        )
        and 5.0 <= camera_tilt_deg <= 30.0
        and camera_optical_axis[0] > 0.0
        and camera_optical_axis[2] < 0.0
    )
    add_check(
        checks,
        failures,
        "lidar_placement.front_mounted_and_slanted",
        placement_pass,
        placement_rules,
    )

    geometry_audit = build_report.get("lidar_geometry_audit", {})
    intersections = geometry_audit.get("boolean_intersection_mm3", {})
    visible_component_names = geometry_audit.get(
        "visible_component_names",
        [],
    )
    visible_collision_matrix = geometry_audit.get(
        "visible_collision_matrix_mm3",
        {},
    )
    visible_collision_values = list(visible_collision_matrix.values())
    declared_visible_engagement_pairs = geometry_audit.get(
        "declared_visible_engagement_pairs",
        [],
    )
    undeclared_visible_collision_values = [
        value
        for key, value in visible_collision_matrix.items()
        if key not in declared_visible_engagement_pairs
    ]
    expected_visible_components = [
        "TORSO",
        "FACTORY_INTERFACE",
        "FACTORY_LIDAR_MOUNTS",
        "MID360_ADAPTER",
        "MID360_GUARD",
        "MID360_SENSOR",
        "D435I_CAMERA",
        "CAMERA_MOUNT_BRACKET",
        "CAMERA_CARRIER_PLATE",
        "CAMERA_RECEIVER_YOKE",
    ]
    expected_visible_pair_count = (
        len(expected_visible_components)
        * (len(expected_visible_components) - 1)
        // 2
    )
    surface_clearance = geometry_audit.get("surface_clearance", {})
    guard_clearance = surface_clearance.get("mid360_to_s410", {})
    connector_clearance = surface_clearance.get("connector_to_s410", {})
    hole_edge_clearances = geometry_audit.get(
        "hidden_bridge_to_hole_edge_clearance_mm",
        [],
    )
    lidar_geometry_rules = {
        "mount_normal_offset_mm": geometry_audit.get(
            "mount_normal_offset_mm"
        ),
        "mid360_to_j20a_intersection_mm3": intersections.get(
            "mid360_to_j20a"
        ),
        "factory_mounts_to_j20a_intersection_mm3": intersections.get(
            "factory_mounts_to_j20a"
        ),
        "mid360_to_s410_intersection_mm3": intersections.get(
            "mid360_to_s410"
        ),
        "mid360_to_hidden_bridge_intersection_mm3": intersections.get(
            "mid360_to_hidden_bridge"
        ),
        "j20a_to_hidden_bridge_intersection_mm3": intersections.get(
            "j20a_to_hidden_bridge"
        ),
        "mid360_to_s410_sampled_clearance_mm": guard_clearance.get(
            "minimum_mm"
        ),
        "connector_to_s410_sampled_clearance_mm": connector_clearance.get(
            "minimum_mm"
        ),
        "hidden_bridge_to_hole_edge_clearance_mm": hole_edge_clearances,
        "upper_module_connected_components": geometry_audit.get(
            "upper_module_connected_components"
        ),
        "upper_boolean_removed_negative_internal_shells_mm3": (
            geometry_audit.get(
                "upper_boolean_removed_negative_internal_shells_mm3",
                [],
            )
        ),
        "longitudinal_fov_approximation_deg": geometry_audit.get(
            "longitudinal_fov_approximation_deg"
        ),
        "visible_component_names": visible_component_names,
        "visible_collision_pair_count": len(visible_collision_matrix),
        "visible_collision_matrix_mm3": visible_collision_matrix,
        "declared_visible_engagement_pairs": (
            declared_visible_engagement_pairs
        ),
        "maximum_undeclared_visible_collision_mm3": (
            max(
                float(value)
                for value in undeclared_visible_collision_values
            )
            if undeclared_visible_collision_values
            else None
        ),
    }
    numeric_geometry_values = [
        lidar_geometry_rules["mount_normal_offset_mm"],
        lidar_geometry_rules[
            "factory_mounts_to_j20a_intersection_mm3"
        ],
        lidar_geometry_rules["mid360_to_j20a_intersection_mm3"],
        lidar_geometry_rules["mid360_to_s410_intersection_mm3"],
        lidar_geometry_rules[
            "mid360_to_hidden_bridge_intersection_mm3"
        ],
        lidar_geometry_rules[
            "j20a_to_hidden_bridge_intersection_mm3"
        ],
        lidar_geometry_rules["mid360_to_s410_sampled_clearance_mm"],
        lidar_geometry_rules["connector_to_s410_sampled_clearance_mm"],
    ]
    geometry_pass = (
        all(isinstance(value, (int, float)) for value in numeric_geometry_values)
        and 2.5
        <= float(lidar_geometry_rules["mount_normal_offset_mm"])
        <= 4.0
        and float(
            lidar_geometry_rules[
                "factory_mounts_to_j20a_intersection_mm3"
            ]
        )
        <= 1.0e-3
        and float(
            lidar_geometry_rules["mid360_to_j20a_intersection_mm3"]
        )
        <= 1.0e-3
        and float(
            lidar_geometry_rules["mid360_to_s410_intersection_mm3"]
        )
        <= 1.0e-3
        and float(
            lidar_geometry_rules[
                "mid360_to_hidden_bridge_intersection_mm3"
            ]
        )
        > 1.0
        and float(
            lidar_geometry_rules[
                "j20a_to_hidden_bridge_intersection_mm3"
            ]
        )
        > 1.0
        and float(
            lidar_geometry_rules[
                "mid360_to_s410_sampled_clearance_mm"
            ]
        )
        >= 0.5
        and float(
            lidar_geometry_rules[
                "connector_to_s410_sampled_clearance_mm"
            ]
        )
        >= 5.0
        and len(hole_edge_clearances) == 2
        and min(float(value) for value in hole_edge_clearances)
        >= (
            float(profile["minimum_feature_mm"])
            / float(profile["scale"])
        )
        - 1.0e-6
        and lidar_geometry_rules["upper_module_connected_components"] == 1
        and all(
            isinstance(value, (int, float))
            and 0.0 < float(value) < 500.0
            for value in lidar_geometry_rules[
                "upper_boolean_removed_negative_internal_shells_mm3"
            ]
        )
        and visible_component_names == expected_visible_components
        and len(visible_collision_matrix) == expected_visible_pair_count
        and len(visible_collision_values) == expected_visible_pair_count
        and declared_visible_engagement_pairs
        == ["MID360_GUARD__CAMERA_RECEIVER_YOKE"]
        and float(
            visible_collision_matrix[
                "MID360_GUARD__CAMERA_RECEIVER_YOKE"
            ]
        )
        > 1.0
        and all(
            isinstance(value, (int, float))
            and float(value) <= 1.0e-3
            for value in undeclared_visible_collision_values
        )
    )
    add_check(
        checks,
        failures,
        "lidar_geometry.collision_free_seating_and_print_bridge",
        geometry_pass,
        lidar_geometry_rules,
    )

    payload_base = geometry_audit.get("payload_base", {})
    camera_support = geometry_audit.get("camera_mounting", {})
    arm_guard_clearance = camera_support.get(
        "bracket_to_guard_clearance",
        {},
    )
    base_mount_rules = {
        "architecture": payload_base.get("architecture"),
        "official_hole_pattern_mm": payload_base.get(
            "official_hole_pattern_mm"
        ),
        "open_hole_diameter_mm": payload_base.get(
            "open_hole_diameter_mm"
        ),
        "j17a_hole_pattern_mm": payload_base.get(
            "j17a_hole_pattern_mm"
        ),
        "j17a_open_hole_diameter_mm": payload_base.get(
            "j17a_open_hole_diameter_mm"
        ),
        "hole_probe_intersection_mm3": payload_base.get(
            "hole_probe_intersection_mm3"
        ),
        "j17a_hole_probe_intersection_mm3": payload_base.get(
            "j17a_hole_probe_intersection_mm3"
        ),
        "agx_base_mount_centers_robot_mm": payload_base.get(
            "agx_base_mount_centers_robot_mm"
        ),
        "agx_base_mount_diameters_mm": payload_base.get(
            "agx_base_mount_diameters_mm"
        ),
        "agx_device_mount_centers_robot_mm": payload_base.get(
            "agx_device_mount_centers_robot_mm"
        ),
        "agx_device_mount_diameter_mm": payload_base.get(
            "agx_device_mount_diameter_mm"
        ),
        "agx_device_mount_pattern_center_robot_mm": payload_base.get(
            "agx_device_mount_pattern_center_robot_mm"
        ),
        "agx_compute_crossbar_size_mm": payload_base.get(
            "agx_compute_crossbar_size_mm"
        ),
        "jetson_agx_orin_envelope_mm": payload_base.get(
            "jetson_agx_orin_envelope_mm"
        ),
        "jetson_agx_orin_center_mm": payload_base.get(
            "jetson_agx_orin_center_mm"
        ),
        "agx_base_to_payload_base_intersection_mm3": payload_base.get(
            "agx_base_to_payload_base_intersection_mm3"
        ),
        "jetson_to_agx_base_intersection_mm3": payload_base.get(
            "jetson_to_agx_base_intersection_mm3"
        ),
        "jetson_fan_to_shell_intersection_mm3": payload_base.get(
            "jetson_fan_to_shell_intersection_mm3"
        ),
        "agx_base_hole_probe_intersection_mm3": payload_base.get(
            "agx_base_hole_probe_intersection_mm3"
        ),
        "jetson_blind_mount_depth_mm": payload_base.get(
            "jetson_blind_mount_depth_mm"
        ),
        "jetson_blind_mount_diameter_mm": payload_base.get(
            "jetson_blind_mount_diameter_mm"
        ),
        "jetson_mount_hole_probe_intersection_mm3": payload_base.get(
            "jetson_mount_hole_probe_intersection_mm3"
        ),
        "official_p3701_internal_components": payload_base.get(
            "official_p3701_internal_components"
        ),
        "minimum_payload_to_j17a_hole_ligament_mm": payload_base.get(
            "minimum_payload_to_j17a_hole_ligament_mm"
        ),
        "camera_arm_count": camera_support.get("arm_count"),
        "camera_product": camera_support.get("product"),
        "camera_socket_target": camera_support.get("socket_target"),
        "camera_to_j17a_intersection_mm3": camera_support.get(
            "camera_to_j17a_intersection_mm3"
        ),
        "camera_arm_to_guard_intersection_mm3": camera_support.get(
            "arm_to_guard_intersection_mm3"
        ),
        "camera_arm_to_guard_clearance_mm": arm_guard_clearance.get(
            "minimum_mm"
        ),
    }
    base_numeric_values = [
        base_mount_rules["open_hole_diameter_mm"],
        base_mount_rules["j17a_open_hole_diameter_mm"],
        base_mount_rules["hole_probe_intersection_mm3"],
        base_mount_rules["j17a_hole_probe_intersection_mm3"],
        base_mount_rules["agx_base_to_payload_base_intersection_mm3"],
        base_mount_rules["jetson_to_agx_base_intersection_mm3"],
        base_mount_rules["jetson_fan_to_shell_intersection_mm3"],
        base_mount_rules["agx_base_hole_probe_intersection_mm3"],
        base_mount_rules["agx_device_mount_diameter_mm"],
        base_mount_rules["jetson_blind_mount_depth_mm"],
        base_mount_rules["jetson_blind_mount_diameter_mm"],
        base_mount_rules["jetson_mount_hole_probe_intersection_mm3"],
        base_mount_rules["minimum_payload_to_j17a_hole_ligament_mm"],
        base_mount_rules["camera_to_j17a_intersection_mm3"],
        base_mount_rules["camera_arm_to_guard_intersection_mm3"],
        base_mount_rules["camera_arm_to_guard_clearance_mm"],
    ]
    base_mount_pass = (
        all(isinstance(value, (int, float)) for value in base_numeric_values)
        and base_mount_rules["architecture"]
        == (
            "dual_side_rails_plus_j17a_crossbars_and_"
            "three_point_agx_orin_base_adapter_crossbar"
        )
        and base_mount_rules["official_hole_pattern_mm"] == [74.0, 94.0]
        and base_mount_rules["j17a_hole_pattern_mm"] == [110.0, 86.0]
        and float(base_mount_rules["open_hole_diameter_mm"]) >= 3.5
        and float(base_mount_rules["j17a_open_hole_diameter_mm"]) >= 3.5
        and float(base_mount_rules["hole_probe_intersection_mm3"]) <= 1.0e-3
        and float(base_mount_rules["j17a_hole_probe_intersection_mm3"])
        <= 1.0e-3
        and len(base_mount_rules["agx_base_mount_centers_robot_mm"] or [])
        == 3
        and len(base_mount_rules["agx_base_mount_diameters_mm"] or [])
        == 3
        and len(base_mount_rules["agx_device_mount_centers_robot_mm"] or [])
        == 4
        and float(base_mount_rules["agx_device_mount_diameter_mm"])
        == 2.8
        and np.allclose(
            np.asarray(
                base_mount_rules[
                    "agx_device_mount_pattern_center_robot_mm"
                ],
                dtype=float,
            ),
            np.asarray(
                base_mount_rules["jetson_agx_orin_center_mm"][:2],
                dtype=float,
            ),
            atol=1.0e-6,
        )
        and len(base_mount_rules["agx_compute_crossbar_size_mm"] or [])
        == 3
        and base_mount_rules["jetson_agx_orin_envelope_mm"]
        == [110.0, 110.0, 71.65]
        and len(base_mount_rules["jetson_agx_orin_center_mm"] or []) == 3
        and float(
            base_mount_rules[
                "agx_base_to_payload_base_intersection_mm3"
            ]
        )
        <= 1.0e-3
        and float(
            base_mount_rules["jetson_to_agx_base_intersection_mm3"]
        )
        <= 1.0e-3
        and float(
            base_mount_rules["jetson_fan_to_shell_intersection_mm3"]
        )
        <= 1.0e-3
        and float(
            base_mount_rules["agx_base_hole_probe_intersection_mm3"]
        )
        <= 1.0e-3
        and float(base_mount_rules["jetson_blind_mount_depth_mm"])
        >= 8.0
        and float(base_mount_rules["jetson_blind_mount_diameter_mm"])
        >= float(base_mount_rules["agx_device_mount_diameter_mm"])
        and float(
            base_mount_rules[
                "jetson_mount_hole_probe_intersection_mm3"
            ]
        )
        <= 1.0e-3
        and int(base_mount_rules["official_p3701_internal_components"])
        >= 1
        and float(
            base_mount_rules[
                "minimum_payload_to_j17a_hole_ligament_mm"
            ]
        )
        >= (
            float(profile["minimum_feature_mm"])
            / float(profile["scale"])
        )
        - 1.0e-6
        and base_mount_rules["camera_arm_count"] == 2
        and base_mount_rules["camera_product"]
        == "Intel RealSense D435i"
        and base_mount_rules["camera_socket_target"]
        == "factory_forward_camera_mount"
        and float(base_mount_rules["camera_to_j17a_intersection_mm3"])
        <= 1.0e-3
        and float(
            base_mount_rules["camera_arm_to_guard_intersection_mm3"]
        )
        <= 1.0e-3
        and float(base_mount_rules["camera_arm_to_guard_clearance_mm"])
        >= 0.5
    )
    factory_interface_rules = {
        "architecture": payload_base.get("architecture"),
        "visible_spanning_plate": payload_base.get(
            "visible_spanning_plate"
        ),
        "factory_lidar_mount_count": payload_base.get(
            "factory_lidar_mount_count"
        ),
        "factory_lidar_mount_open_hole_diameter_mm": payload_base.get(
            "factory_lidar_mount_open_hole_diameter_mm"
        ),
        "official_hole_pattern_mm": payload_base.get(
            "official_hole_pattern_mm"
        ),
        "open_hole_diameter_mm": payload_base.get(
            "open_hole_diameter_mm"
        ),
        "j17a_hole_pattern_mm": payload_base.get(
            "j17a_hole_pattern_mm"
        ),
        "j17a_open_hole_diameter_mm": payload_base.get(
            "j17a_open_hole_diameter_mm"
        ),
        "hole_probe_intersection_mm3": payload_base.get(
            "hole_probe_intersection_mm3"
        ),
        "j17a_hole_probe_intersection_mm3": payload_base.get(
            "j17a_hole_probe_intersection_mm3"
        ),
        "visible_component_identity": payload_base.get(
            "visible_component_identity"
        ),
        "ai_computer_identity": payload_base.get(
            "ai_computer_identity"
        ),
        "ai_computer_location": payload_base.get(
            "ai_computer_location"
        ),
        "factory_interface_envelope_mm": payload_base.get(
            "factory_interface_envelope_mm"
        ),
        "factory_interface_center_mm": payload_base.get(
            "factory_interface_center_mm"
        ),
        "factory_interface_mount_pattern_mm": payload_base.get(
            "factory_interface_mount_pattern_mm"
        ),
        "factory_interface_to_payload_base_intersection_mm3": (
            payload_base.get(
                "factory_interface_to_payload_base_intersection_mm3"
            )
        ),
        "factory_interface_to_torso_intersection_mm3": payload_base.get(
            "factory_interface_to_torso_intersection_mm3"
        ),
        "factory_interface_to_mounts_intersection_mm3": payload_base.get(
            "factory_interface_to_mounts_intersection_mm3"
        ),
        "minimum_payload_to_j17a_hole_ligament_mm": payload_base.get(
            "minimum_payload_to_j17a_hole_ligament_mm"
        ),
        "camera_product": camera_support.get("product"),
        "camera_socket_target": camera_support.get("socket_target"),
        "camera_screw_count": camera_support.get("camera_screw_count"),
        "carrier_screw_count": camera_support.get("carrier_screw_count"),
        "side_join_screw_count": camera_support.get(
            "side_join_screw_count"
        ),
        "official_rear_thread_spacing_mm": camera_support.get(
            "official_rear_thread_spacing_mm"
        ),
        "official_maximum_thread_insertion_mm": camera_support.get(
            "official_maximum_thread_insertion_mm"
        ),
        "calculated_camera_thread_insertion_mm": camera_support.get(
            "calculated_camera_thread_insertion_mm"
        ),
        "calculated_carrier_thread_insertion_mm": camera_support.get(
            "calculated_carrier_thread_insertion_mm"
        ),
        "opposing_head_service_gap_mm": camera_support.get(
            "opposing_head_service_gap_mm"
        ),
        "bracket_connected_components": camera_support.get(
            "bracket_connected_components"
        ),
        "carrier_plate_connected_components": camera_support.get(
            "carrier_plate_connected_components"
        ),
        "receiver_yoke_connected_components": camera_support.get(
            "receiver_yoke_connected_components"
        ),
        "receiver_yoke_watertight": camera_support.get(
            "receiver_yoke_watertight"
        ),
        "receiver_count": camera_support.get("receiver_count"),
        "receiver_bore_depth_mm": camera_support.get(
            "receiver_bore_depth_mm"
        ),
        "receiver_minimum_radial_wall_print_mm": camera_support.get(
            "receiver_minimum_radial_wall_print_mm"
        ),
        "receiver_face_gap_mm": camera_support.get(
            "receiver_face_gap_mm"
        ),
        "receiver_yoke_to_guard_engagement_mm3": camera_support.get(
            "receiver_yoke_to_guard_engagement_mm3"
        ),
        "print_receiver_yoke_to_guard_engagement_mm3": (
            camera_support.get(
                "print_receiver_yoke_to_guard_engagement_mm3"
            )
        ),
        "receiver_yoke_to_adapter_intersection_mm3": camera_support.get(
            "receiver_yoke_to_adapter_intersection_mm3"
        ),
        "receiver_yoke_to_carrier_plate_intersection_mm3": (
            camera_support.get(
                "receiver_yoke_to_carrier_plate_intersection_mm3"
            )
        ),
        "print_receiver_yoke_to_print_carrier_plate_intersection_mm3": (
            camera_support.get(
                "print_receiver_yoke_to_print_carrier_plate_intersection_mm3"
            )
        ),
        "receiver_yoke_to_fasteners_intersection_mm3": (
            camera_support.get(
                "receiver_yoke_to_fasteners_intersection_mm3"
            )
        ),
        "print_receiver_yoke_to_print_fasteners_intersection_mm3": (
            camera_support.get(
                "print_receiver_yoke_to_print_fasteners_intersection_mm3"
            )
        ),
        "receiver_yoke_to_factory_mounts_intersection_mm3": (
            camera_support.get(
                "receiver_yoke_to_factory_mounts_intersection_mm3"
            )
        ),
        "receiver_yoke_to_interface_intersection_mm3": (
            camera_support.get(
                "receiver_yoke_to_interface_intersection_mm3"
            )
        ),
        "receiver_yoke_to_torso_intersection_mm3": camera_support.get(
            "receiver_yoke_to_torso_intersection_mm3"
        ),
        "carrier_plate_to_receiver_yoke_clearance_mm": (
            camera_support.get(
                "carrier_plate_to_receiver_yoke_clearance",
                {},
            ).get("minimum_mm")
        ),
        "visual_fastener_connected_components": camera_support.get(
            "visual_fastener_connected_components"
        ),
        "print_fastener_connected_components": camera_support.get(
            "print_fastener_connected_components"
        ),
        "camera_to_factory_mounts_intersection_mm3": camera_support.get(
            "camera_to_factory_mounts_intersection_mm3"
        ),
        "print_camera_to_factory_mounts_intersection_mm3": (
            camera_support.get(
                "print_camera_to_factory_mounts_intersection_mm3"
            )
        ),
        "camera_to_bracket_intersection_mm3": camera_support.get(
            "camera_to_bracket_intersection_mm3"
        ),
        "print_camera_to_print_bracket_intersection_mm3": (
            camera_support.get(
                "print_camera_to_print_bracket_intersection_mm3"
            )
        ),
        "bracket_to_carrier_plate_intersection_mm3": camera_support.get(
            "bracket_to_carrier_plate_intersection_mm3"
        ),
        "print_bracket_to_print_carrier_plate_intersection_mm3": (
            camera_support.get(
                "print_bracket_to_print_carrier_plate_intersection_mm3"
            )
        ),
        "camera_bracket_to_guard_intersection_mm3": camera_support.get(
            "bracket_to_guard_intersection_mm3"
        ),
        "camera_bracket_to_guard_clearance_mm": arm_guard_clearance.get(
            "minimum_mm"
        ),
        "carrier_plate_to_guard_intersection_mm3": camera_support.get(
            "carrier_plate_to_guard_intersection_mm3"
        ),
        "carrier_plate_to_guard_clearance_mm": camera_support.get(
            "carrier_plate_to_guard_clearance",
            {},
        ).get("minimum_mm"),
        "camera_bracket_to_adapter_intersection_mm3": camera_support.get(
            "bracket_to_adapter_intersection_mm3"
        ),
        "carrier_plate_to_adapter_intersection_mm3": camera_support.get(
            "carrier_plate_to_adapter_intersection_mm3"
        ),
    }
    factory_numeric_values = [
        factory_interface_rules["open_hole_diameter_mm"],
        factory_interface_rules["j17a_open_hole_diameter_mm"],
        factory_interface_rules[
            "factory_lidar_mount_open_hole_diameter_mm"
        ],
        factory_interface_rules["hole_probe_intersection_mm3"],
        factory_interface_rules["j17a_hole_probe_intersection_mm3"],
        factory_interface_rules[
            "factory_interface_to_payload_base_intersection_mm3"
        ],
        factory_interface_rules[
            "factory_interface_to_torso_intersection_mm3"
        ],
        factory_interface_rules[
            "factory_interface_to_mounts_intersection_mm3"
        ],
        factory_interface_rules[
            "minimum_payload_to_j17a_hole_ligament_mm"
        ],
        factory_interface_rules[
            "camera_to_factory_mounts_intersection_mm3"
        ],
        factory_interface_rules[
            "print_camera_to_factory_mounts_intersection_mm3"
        ],
        factory_interface_rules["camera_screw_count"],
        factory_interface_rules["carrier_screw_count"],
        factory_interface_rules["side_join_screw_count"],
        factory_interface_rules["official_rear_thread_spacing_mm"],
        factory_interface_rules["official_maximum_thread_insertion_mm"],
        factory_interface_rules[
            "calculated_camera_thread_insertion_mm"
        ],
        factory_interface_rules[
            "calculated_carrier_thread_insertion_mm"
        ],
        factory_interface_rules["opposing_head_service_gap_mm"],
        factory_interface_rules["bracket_connected_components"],
        factory_interface_rules["carrier_plate_connected_components"],
        factory_interface_rules["receiver_yoke_connected_components"],
        factory_interface_rules["receiver_count"],
        factory_interface_rules["receiver_bore_depth_mm"],
        factory_interface_rules[
            "receiver_minimum_radial_wall_print_mm"
        ],
        factory_interface_rules["receiver_face_gap_mm"],
        factory_interface_rules[
            "receiver_yoke_to_guard_engagement_mm3"
        ],
        factory_interface_rules[
            "print_receiver_yoke_to_guard_engagement_mm3"
        ],
        factory_interface_rules[
            "receiver_yoke_to_adapter_intersection_mm3"
        ],
        factory_interface_rules[
            "receiver_yoke_to_carrier_plate_intersection_mm3"
        ],
        factory_interface_rules[
            "print_receiver_yoke_to_print_carrier_plate_intersection_mm3"
        ],
        factory_interface_rules[
            "receiver_yoke_to_fasteners_intersection_mm3"
        ],
        factory_interface_rules[
            "print_receiver_yoke_to_print_fasteners_intersection_mm3"
        ],
        factory_interface_rules[
            "receiver_yoke_to_factory_mounts_intersection_mm3"
        ],
        factory_interface_rules[
            "receiver_yoke_to_interface_intersection_mm3"
        ],
        factory_interface_rules[
            "receiver_yoke_to_torso_intersection_mm3"
        ],
        factory_interface_rules[
            "carrier_plate_to_receiver_yoke_clearance_mm"
        ],
        factory_interface_rules[
            "visual_fastener_connected_components"
        ],
        factory_interface_rules[
            "print_fastener_connected_components"
        ],
        factory_interface_rules["camera_to_bracket_intersection_mm3"],
        factory_interface_rules[
            "print_camera_to_print_bracket_intersection_mm3"
        ],
        factory_interface_rules[
            "bracket_to_carrier_plate_intersection_mm3"
        ],
        factory_interface_rules[
            "print_bracket_to_print_carrier_plate_intersection_mm3"
        ],
        factory_interface_rules[
            "camera_bracket_to_guard_intersection_mm3"
        ],
        factory_interface_rules[
            "camera_bracket_to_guard_clearance_mm"
        ],
        factory_interface_rules[
            "carrier_plate_to_guard_intersection_mm3"
        ],
        factory_interface_rules[
            "carrier_plate_to_guard_clearance_mm"
        ],
        factory_interface_rules[
            "camera_bracket_to_adapter_intersection_mm3"
        ],
        factory_interface_rules[
            "carrier_plate_to_adapter_intersection_mm3"
        ],
    ]
    factory_interface_pass = (
        all(
            isinstance(value, (int, float))
            for value in factory_numeric_values
        )
        and factory_interface_rules["architecture"]
        == (
            "no_visible_spanning_plate_with_local_"
            "interface_feet_and_lidar_mounts"
        )
        and factory_interface_rules["visible_spanning_plate"] is False
        and factory_interface_rules["factory_lidar_mount_count"] == 4
        and float(
            factory_interface_rules[
                "factory_lidar_mount_open_hole_diameter_mm"
            ]
        )
        >= 3.5
        and factory_interface_rules["official_hole_pattern_mm"]
        == [74.0, 94.0]
        and factory_interface_rules["j17a_hole_pattern_mm"]
        == [110.0, 86.0]
        and float(factory_interface_rules["open_hole_diameter_mm"]) >= 3.5
        and float(factory_interface_rules["j17a_open_hole_diameter_mm"])
        >= 3.5
        and abs(
            float(factory_interface_rules["hole_probe_intersection_mm3"])
        )
        <= 1.0e-3
        and abs(
            float(
                factory_interface_rules[
                    "j17a_hole_probe_intersection_mm3"
                ]
            )
        )
        <= 1.0e-3
        and factory_interface_rules["visible_component_identity"]
        == "DEEP Robotics Interface"
        and factory_interface_rules["ai_computer_identity"]
        == "NVIDIA Jetson Xavier NX"
        and factory_interface_rules["ai_computer_location"]
        == "not_published"
        and factory_interface_rules["factory_interface_envelope_mm"]
        == [160.0, 92.0, 46.0]
        and len(
            factory_interface_rules["factory_interface_center_mm"] or []
        )
        == 3
        and len(
            factory_interface_rules[
                "factory_interface_mount_pattern_mm"
            ]
            or []
        )
        == 2
        and all(
            abs(
                float(
                    factory_interface_rules[key]
                )
            )
            <= 1.0e-3
            for key in (
                "factory_interface_to_payload_base_intersection_mm3",
                "factory_interface_to_torso_intersection_mm3",
                "factory_interface_to_mounts_intersection_mm3",
            )
        )
        and float(
            factory_interface_rules[
                "minimum_payload_to_j17a_hole_ligament_mm"
            ]
        )
        >= (
            float(profile["minimum_feature_mm"])
            / float(profile["scale"])
        )
        - 1.0e-6
        and factory_interface_rules["camera_product"]
        == "Intel RealSense D435i"
        and factory_interface_rules["camera_socket_target"]
        == "s410_guard_integrated_camera_receiver_yoke"
        and factory_interface_rules["camera_screw_count"] == 2
        and factory_interface_rules["carrier_screw_count"] == 2
        and factory_interface_rules["side_join_screw_count"] == 4
        and math.isclose(
            float(
                factory_interface_rules[
                    "official_rear_thread_spacing_mm"
                ]
            ),
            45.0,
            abs_tol=1.0e-9,
        )
        and math.isclose(
            float(
                factory_interface_rules[
                    "official_maximum_thread_insertion_mm"
                ]
            ),
            3.0,
            abs_tol=1.0e-9,
        )
        and 0.0
        < float(
            factory_interface_rules[
                "calculated_camera_thread_insertion_mm"
            ]
        )
        <= float(
            factory_interface_rules[
                "official_maximum_thread_insertion_mm"
            ]
        )
        and 0.0
        < float(
            factory_interface_rules[
                "calculated_carrier_thread_insertion_mm"
            ]
        )
        <= float(
            factory_interface_rules[
                "official_maximum_thread_insertion_mm"
            ]
        )
        and float(
            factory_interface_rules["opposing_head_service_gap_mm"]
        )
        >= 3.0
        and factory_interface_rules["bracket_connected_components"] == 1
        and factory_interface_rules[
            "carrier_plate_connected_components"
        ] == 1
        and factory_interface_rules[
            "receiver_yoke_connected_components"
        ] == 2
        and factory_interface_rules["receiver_yoke_watertight"] is True
        and factory_interface_rules["receiver_count"] == 2
        and math.isclose(
            float(factory_interface_rules["receiver_bore_depth_mm"]),
            3.0,
            abs_tol=1.0e-9,
        )
        and float(
            factory_interface_rules[
                "receiver_minimum_radial_wall_print_mm"
            ]
        )
        >= float(config["print_profile"]["minimum_feature_mm"])
        and 0.0
        < float(factory_interface_rules["receiver_face_gap_mm"])
        <= 0.1
        and float(
            factory_interface_rules[
                "receiver_yoke_to_guard_engagement_mm3"
            ]
        )
        > 1.0
        and float(
            factory_interface_rules[
                "print_receiver_yoke_to_guard_engagement_mm3"
            ]
        )
        > 1.0
        and all(
            abs(float(factory_interface_rules[key])) <= 1.0e-3
            for key in (
                "receiver_yoke_to_adapter_intersection_mm3",
                "receiver_yoke_to_carrier_plate_intersection_mm3",
                "print_receiver_yoke_to_print_carrier_plate_intersection_mm3",
                "receiver_yoke_to_fasteners_intersection_mm3",
                "print_receiver_yoke_to_print_fasteners_intersection_mm3",
                "receiver_yoke_to_factory_mounts_intersection_mm3",
                "receiver_yoke_to_interface_intersection_mm3",
                "receiver_yoke_to_torso_intersection_mm3",
            )
        )
        and 0.0
        < float(
            factory_interface_rules[
                "carrier_plate_to_receiver_yoke_clearance_mm"
            ]
        )
        <= 0.1
        and factory_interface_rules[
            "visual_fastener_connected_components"
        ] == 8
        and factory_interface_rules[
            "print_fastener_connected_components"
        ] == 8
        and float(
            factory_interface_rules[
                "camera_to_factory_mounts_intersection_mm3"
            ]
        )
        <= 1.0e-3
        and float(
            factory_interface_rules[
                "print_camera_to_factory_mounts_intersection_mm3"
            ]
        )
        <= 1.0e-3
        and all(
            abs(float(factory_interface_rules[key])) <= 1.0e-3
            for key in (
                "camera_to_bracket_intersection_mm3",
                "print_camera_to_print_bracket_intersection_mm3",
                "bracket_to_carrier_plate_intersection_mm3",
                "print_bracket_to_print_carrier_plate_intersection_mm3",
                "camera_bracket_to_guard_intersection_mm3",
                "carrier_plate_to_guard_intersection_mm3",
                "camera_bracket_to_adapter_intersection_mm3",
                "carrier_plate_to_adapter_intersection_mm3",
            )
        )
        and float(
            factory_interface_rules[
                "camera_bracket_to_guard_clearance_mm"
            ]
        )
        >= 0.5
        and float(
            factory_interface_rules[
                "carrier_plate_to_guard_clearance_mm"
            ]
        )
        >= 0.5
    )
    add_check(
        checks,
        failures,
        "payload_base.factory_interface_and_camera_mounting",
        factory_interface_pass,
        factory_interface_rules,
    )

    mounts = config["assembly_mounts"]
    build_mounts = build_report.get("assembly_mounts", {})
    upper_mount = mounts["upper_module"]
    camera_mount = mounts["camera_mount_bracket"]
    built_camera_mount = build_mounts.get("camera_mount_bracket", {})
    mount_rules = {
        "upper_integrated_pin_count": len(
            build_mounts.get("upper_module", {}).get("pins", [])
        ),
        "camera_fastener_count": built_camera_mount.get(
            "camera_fasteners"
        ),
        "carrier_fastener_count": built_camera_mount.get(
            "carrier_fasteners"
        ),
        "side_join_fastener_count": built_camera_mount.get(
            "side_join_fasteners"
        ),
        "upper_radial_clearance_mm": (
            float(upper_mount["socket_radius_print_mm"])
            - float(upper_mount["pin_radius_print_mm"])
        ),
        "camera_radial_clearance_mm": built_camera_mount.get(
            "print_radial_clearance_mm"
        ),
        "camera_socket_target": built_camera_mount.get("socket_target"),
        "camera_hole_spacing_mm": built_camera_mount.get(
            "official_camera_hole_spacing_mm"
        ),
        "carrier_hole_spacing_mm": built_camera_mount.get(
            "carrier_side_hole_spacing_mm"
        ),
        "carrier_axis_source": built_camera_mount.get(
            "carrier_side_axis_source"
        ),
        "receiver_geometry_node": built_camera_mount.get(
            "receiver_geometry_node"
        ),
        "receiver_boss_count": built_camera_mount.get(
            "receiver_boss_count"
        ),
        "receiver_bore_depth_mm": built_camera_mount.get(
            "receiver_bore_depth_mm"
        ),
        "receiver_guard_engagement": built_camera_mount.get(
            "receiver_guard_engagement"
        ),
        "print_screw_shaft_mm": (
            float(
                camera_mount[
                    "print_equivalent_screw_shaft_diameter_master_mm"
                ]
            )
            * float(config["print_profile"]["scale"])
        ),
        "print_screw_head_height_mm": (
            float(
                camera_mount[
                    "print_equivalent_screw_head_height_master_mm"
                ]
            )
            * float(config["print_profile"]["scale"])
        ),
        "deck_pocket_xy_clearance_mm": float(
            upper_mount["deck_pocket_xy_clearance_print_mm"]
        ),
        "deck_pocket_vertical_clearance_mm": float(
            upper_mount["deck_pocket_vertical_clearance_print_mm"]
        ),
    }
    mount_pass = (
        mount_rules["upper_integrated_pin_count"] == 2
        and mount_rules["camera_fastener_count"] == 2
        and mount_rules["carrier_fastener_count"] == 2
        and mount_rules["side_join_fastener_count"] == 4
        and mount_rules["camera_socket_target"]
        == "s410_guard_integrated_camera_receiver_yoke"
        and math.isclose(
            float(mount_rules["camera_hole_spacing_mm"]),
            45.0,
            abs_tol=1.0e-9,
        )
        and math.isclose(
            float(mount_rules["carrier_hole_spacing_mm"]),
            45.0,
            abs_tol=1.0e-9,
        )
        and mount_rules["carrier_axis_source"]
        == "pinned_J17A_source_model"
        and mount_rules["receiver_geometry_node"]
        == "CAMERA_RECEIVER_YOKE"
        and mount_rules["receiver_boss_count"] == 2
        and math.isclose(
            float(mount_rules["receiver_bore_depth_mm"]),
            3.0,
            abs_tol=1.0e-9,
        )
        and mount_rules["receiver_guard_engagement"]
        == "integrated_into_S410_guard"
        and mount_rules["upper_radial_clearance_mm"] >= 0.2 - 1.0e-9
        and mount_rules["camera_radial_clearance_mm"] >= 0.2 - 1.0e-9
        and mount_rules["print_screw_shaft_mm"]
        >= float(config["print_profile"]["minimum_feature_mm"])
        and mount_rules["print_screw_head_height_mm"]
        >= float(config["print_profile"]["minimum_feature_mm"])
        and mount_rules["deck_pocket_xy_clearance_mm"] >= 0.2
        and mount_rules["deck_pocket_vertical_clearance_mm"] >= 0.2
    )
    add_check(
        checks,
        failures,
        "assembly_mounts.camera_bracket_fasteners_and_clearance",
        mount_pass,
        mount_rules,
    )

    report = {
        "schema_version": 1,
        "artifact_label": "printable_static_replica",
        "passed": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "checks": checks,
        "master_roundtrip": master_metrics,
        "print_roundtrip": print_metrics,
        "reference_imports": reference_metrics,
        "reported_output_hashes": output_hashes,
        "claim_boundary": build_report["claim_boundary"],
    }
    VALIDATION_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with VALIDATION_REPORT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"passed={report['passed']}", flush=True)
    print(f"failure_count={report['failure_count']}", flush=True)
    print(f"report={VALIDATION_REPORT_PATH}", flush=True)
    for failure in failures:
        print(f"FAIL {failure}", flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
