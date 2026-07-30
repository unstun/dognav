#!/usr/bin/env python3
"""Build a watertight Lite3 LiDAR static print replica from official visuals."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import sys
from typing import Any
import xml.etree.ElementTree as ET

import manifold3d as md
import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
import trimesh


ROOT = Path(__file__).resolve().parent
PARAMETERS_PATH = Path(
    os.environ.get("LITE3_PRINT_PARAMS", ROOT / "print_parameters.json")
).resolve()
BUILD_ROOT = Path(os.environ.get("LITE3_PRINT_BUILD_ROOT", ROOT)).resolve()

MASTER_DIR = BUILD_ROOT / "models" / "master_1_1"
PRINT_DIR = BUILD_ROOT / "models" / "print_1_4"
REFERENCE_DIR = BUILD_ROOT / "models" / "reference"
REPORT_DIR = BUILD_ROOT / "reports"

COMPONENT_FILES = {
    "torso": "torso_dae",
    "hip": "hip_dae",
    "thigh": "thigh_dae",
    "shank": "shank_dae",
}

COLORS = {
    "TORSO": [218, 221, 226, 255],
    "HIP": [238, 239, 241, 255],
    "THIGH": [205, 209, 215, 255],
    "SHANK": [95, 101, 110, 255],
    "UPPER_LIDAR_MODULE": [120, 126, 132, 255],
    "UPPER_DECK_INTERFACE": [170, 174, 178, 255],
    "MID360_SENSOR": [176, 182, 188, 255],
    "MID360_OPTICAL_WINDOW": [19, 83, 143, 255],
    "MID360_BODY": [186, 190, 194, 255],
    "MID360_HOUSING_EXTERIOR": [202, 204, 206, 255],
    "MID360_CONNECTOR": [33, 37, 43, 255],
    "J17A_SENSOR_CARRIER": [112, 118, 124, 255],
    "FACTORY_LIDAR_MOUNTS": [130, 136, 142, 255],
    "MID360_ADAPTER": [154, 158, 162, 255],
    "MID360_GUARD": [41, 44, 48, 255],
    "FACTORY_INTERFACE": [92, 96, 101, 255],
    "FACTORY_INTERFACE_CONNECTORS": [29, 32, 36, 255],
    "FACTORY_INTERFACE_VENTS": [42, 45, 49, 255],
    "FRONT_CAMERA_BAR": [175, 180, 186, 255],
    "D435I_CAMERA": [176, 180, 184, 255],
    "CAMERA_MOUNT_BRACKET": [73, 78, 85, 255],
    "CAMERA_CARRIER_PLATE": [96, 102, 110, 255],
    "CAMERA_RECEIVER_YOKE": [55, 60, 66, 255],
    "CAMERA_FASTENERS": [43, 47, 53, 255],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists() and (candidate / "AGENTS.md").exists():
            return candidate
    raise RuntimeError(f"Could not find repository root above {start}")


def load_parameters() -> dict[str, Any]:
    with PARAMETERS_PATH.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    if config.get("schema_version") != 1:
        raise ValueError("Unsupported parameter schema")
    if config.get("artifact_label") != "printable_static_replica":
        raise ValueError("Unexpected artifact label")
    if config.get("coordinate_system", {}).get("unit") != "millimetre":
        raise ValueError("Authoring unit must be millimetre")
    return config


def resolve_sources(
    config: dict[str, Any],
    repo_root: Path,
) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for name, source in config["sources"].items():
        path = (repo_root / source["path"]).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        actual_hash = sha256(path)
        if actual_hash != source["sha256"]:
            raise ValueError(
                f"Source hash mismatch for {name}: "
                f"expected {source['sha256']}, got {actual_hash}"
            )
        result[name] = path
    return result


def parse_vector(
    value: str | None,
    default: tuple[float, float, float],
) -> np.ndarray:
    if not value:
        return np.asarray(default, dtype=float)
    result = np.fromstring(value, sep=" ", dtype=float)
    if result.shape != (3,):
        raise ValueError(f"Expected three values, got {value!r}")
    return result


def origin_transform(origin: ET.Element | None) -> np.ndarray:
    xyz = parse_vector(origin.get("xyz") if origin is not None else None, (0, 0, 0))
    rpy = parse_vector(origin.get("rpy") if origin is not None else None, (0, 0, 0))
    matrix = np.eye(4)
    matrix[:3, :3] = Rotation.from_euler("xyz", rpy).as_matrix()
    matrix[:3, 3] = xyz
    return matrix


def source_mesh(path: Path) -> trimesh.Trimesh:
    loaded = trimesh.load(path, force="scene", process=False)
    meshes: list[trimesh.Trimesh] = []
    for node_name in loaded.graph.nodes_geometry:
        transform, geometry_name = loaded.graph[node_name]
        mesh = loaded.geometry[geometry_name].copy()
        mesh.apply_transform(transform)
        meshes.append(mesh)
    if not meshes:
        raise ValueError(f"No mesh geometry found in {path}")
    mesh = trimesh.util.concatenate(meshes)
    mesh.process(validate=True)
    return mesh


def tessellated_step_mesh(path: Path) -> trimesh.Trimesh:
    """Load a FreeCAD-tessellated STEP exterior and convert mm to metres."""
    loaded = trimesh.load(path, force="mesh", process=False)
    if isinstance(loaded, trimesh.Scene):
        meshes = [
            loaded.geometry[name].copy()
            for name in sorted(loaded.geometry)
        ]
        if not meshes:
            raise ValueError(f"No tessellated geometry found in {path}")
        loaded = trimesh.util.concatenate(meshes)
    if not isinstance(loaded, trimesh.Trimesh) or len(loaded.faces) == 0:
        raise ValueError(f"No tessellated geometry found in {path}")
    mesh = loaded.copy()
    mesh.apply_scale(0.001)
    mesh.remove_unreferenced_vertices()
    return mesh


def topology_metrics(mesh: trimesh.Trimesh) -> dict[str, Any]:
    edges = mesh.edges_sorted
    _, counts = np.unique(edges, axis=0, return_counts=True)
    components = mesh.split(only_watertight=False)
    return {
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "components": int(len(components)),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "boundary_edges": int(np.count_nonzero(counts == 1)),
        "nonmanifold_edges": int(np.count_nonzero(counts > 2)),
        "bbox_size_mm": ((mesh.bounds[1] - mesh.bounds[0]) * 1000.0).tolist(),
    }


def mesh_to_manifold(mesh: trimesh.Trimesh) -> md.Manifold:
    manifold = md.Manifold(
        md.Mesh64(
            np.array(
                mesh.vertices,
                dtype=np.float64,
                order="C",
                copy=True,
            ),
            np.array(
                mesh.faces,
                dtype=np.uint64,
                order="C",
                copy=True,
            ),
        )
    )
    if manifold.status() != md.Error.NoError:
        raise ValueError(f"Manifold conversion failed: {manifold.status()}")
    return manifold


def manifold_to_mesh(manifold: md.Manifold) -> trimesh.Trimesh:
    if manifold.status() != md.Error.NoError:
        raise ValueError(f"Invalid manifold: {manifold.status()}")
    output = manifold.to_mesh64()
    mesh = trimesh.Trimesh(
        vertices=np.asarray(output.vert_properties)[:, :3],
        faces=np.asarray(output.tri_verts),
        process=False,
    )
    # Manifold3D already guarantees topology. Trimesh's validate pass can
    # delete coincident-but-required triangles from a simplified manifold and
    # thereby introduce artificial boundary edges.
    mesh.remove_unreferenced_vertices()
    if not mesh.is_watertight or not mesh.is_winding_consistent:
        raise ValueError("Manifold output is not a closed consistently oriented mesh")
    return mesh


def manifold_box(
    size: np.ndarray | list[float] | tuple[float, float, float],
    center: np.ndarray | list[float] | tuple[float, float, float],
) -> md.Manifold:
    return md.Manifold.cube(np.asarray(size, dtype=float), center=True).translate(
        np.asarray(center, dtype=float)
    )


def reconstruct_master(
    name: str,
    raw: trimesh.Trimesh,
    settings: dict[str, Any],
    smoothing_settings: dict[str, Any],
    sample_count: int,
) -> tuple[trimesh.Trimesh, dict[str, Any]]:
    pitch_m = float(settings["voxel_pitch_mm"]) / 1000.0
    voxel_inputs = [raw]
    for bridge in settings.get("bridge_boxes_mm", []):
        bridge_mesh = trimesh.creation.box(
            extents=np.asarray(bridge["size"], dtype=float) / 1000.0
        )
        bridge_mesh.apply_translation(
            np.asarray(bridge["center"], dtype=float) / 1000.0
        )
        voxel_inputs.append(bridge_mesh)
    voxel_input = (
        raw if len(voxel_inputs) == 1 else trimesh.util.concatenate(voxel_inputs)
    )
    voxel = voxel_input.voxelized(pitch_m, method="subdivide")
    surface_voxels = int(len(voxel.sparse_indices))
    voxel.fill()
    filled_voxels = int(len(voxel.sparse_indices))
    reconstructed = voxel.marching_cubes
    reconstructed.apply_transform(voxel.transform)
    reconstructed.remove_unreferenced_vertices()

    minimum_volume_m3 = (
        float(settings["minimum_component_volume_mm3"]) / 1_000_000_000.0
    )
    components = [
        component
        for component in reconstructed.split(only_watertight=True)
        if abs(float(component.volume)) >= minimum_volume_m3
    ]
    if not components:
        raise ValueError(f"{name} reconstruction lost every component")
    if len(components) != 1:
        raise ValueError(
            f"{name} master remains disconnected after voxel bridge/filter: "
            f"{len(components)} components"
        )
    # Keep the indexed marching-cubes topology intact. Both Manifold3D and
    # triangle simplifiers were tested here, but their STL round-trip merged
    # coincident vertices into non-manifold edges. The raw voxel surface is
    # heavier but survives export/re-import as a closed printable solid.
    master = components[0].copy()
    master.remove_unreferenced_vertices()
    if not master.is_watertight or not master.is_winding_consistent:
        raise ValueError(f"{name} voxel master is not a closed oriented solid")
    if mesh_to_manifold(master).status() != md.Error.NoError:
        raise ValueError(f"{name} voxel master fails Manifold3D validation")

    smoothing_report: dict[str, Any] = {
        "enabled": bool(smoothing_settings.get("enabled", False))
    }
    if smoothing_report["enabled"]:
        before_vertices = np.asarray(master.vertices).copy()
        before_volume = abs(float(master.volume))
        trimesh.smoothing.filter_taubin(
            master,
            lamb=float(smoothing_settings["lambda"]),
            nu=float(smoothing_settings["nu"]),
            iterations=int(smoothing_settings["iterations"]),
        )
        master.remove_unreferenced_vertices()
        if len(master.vertices) != len(before_vertices):
            raise ValueError(f"{name} smoothing changed vertex topology")
        displacement_mm = (
            np.linalg.norm(master.vertices - before_vertices, axis=1) * 1000.0
        )
        after_volume = abs(float(master.volume))
        volume_change_percent = (
            (after_volume - before_volume) / before_volume * 100.0
        )
        smoothing_report.update(
            {
                "method": "trimesh.filter_taubin",
                "lambda": float(smoothing_settings["lambda"]),
                "nu": float(smoothing_settings["nu"]),
                "iterations": int(smoothing_settings["iterations"]),
                "vertex_displacement_mm": {
                    "median": float(np.median(displacement_mm)),
                    "p95": float(np.quantile(displacement_mm, 0.95)),
                    "p99": float(np.quantile(displacement_mm, 0.99)),
                    "max": float(np.max(displacement_mm)),
                },
                "volume_change_percent": float(volume_change_percent),
            }
        )
        if (
            smoothing_report["vertex_displacement_mm"]["p99"]
            > float(smoothing_settings["maximum_p99_displacement_mm"])
        ):
            raise ValueError(f"{name} smoothing exceeds p99 displacement limit")
        if abs(volume_change_percent) > float(
            smoothing_settings["maximum_abs_volume_change_percent"]
        ):
            raise ValueError(f"{name} smoothing exceeds volume-change limit")
        if not master.is_watertight or not master.is_winding_consistent:
            raise ValueError(f"{name} smoothing invalidated the closed solid")
        if len(master.split(only_watertight=True)) != 1:
            raise ValueError(f"{name} smoothing disconnected the print master")
        if mesh_to_manifold(master).status() != md.Error.NoError:
            raise ValueError(f"{name} smoothed master fails Manifold3D validation")

    rng_state = np.random.get_state()
    np.random.seed(107)
    raw_points, _ = trimesh.sample.sample_surface(raw, sample_count)
    master_points, _ = trimesh.sample.sample_surface(master, sample_count)
    np.random.set_state(rng_state)
    _, source_to_master, _ = trimesh.proximity.closest_point(master, raw_points)
    _, master_to_source, _ = trimesh.proximity.closest_point(raw, master_points)

    def summarize_distances(values: np.ndarray) -> dict[str, float]:
        values_mm = np.asarray(values) * 1000.0
        return {
            "median_mm": float(np.median(values_mm)),
            "p95_mm": float(np.quantile(values_mm, 0.95)),
            "p99_mm": float(np.quantile(values_mm, 0.99)),
            "max_mm": float(np.max(values_mm)),
        }

    report = {
        "voxel_pitch_mm": float(settings["voxel_pitch_mm"]),
        "simplify_tolerance_mm": 0.0,
        "bridge_boxes_mm": settings.get("bridge_boxes_mm", []),
        "smoothing": smoothing_report,
        "surface_voxels": surface_voxels,
        "filled_voxels": filled_voxels,
        "retained_voxel_components": len(components),
        "vertices": int(len(master.vertices)),
        "faces": int(len(master.faces)),
        "watertight": bool(master.is_watertight),
        "winding_consistent": bool(master.is_winding_consistent),
        "connected_components": len(master.split(only_watertight=True)),
        "volume_mm3": float(master.volume * 1_000_000_000.0),
        "bbox_size_mm": ((master.bounds[1] - master.bounds[0]) * 1000.0).tolist(),
        "source_to_master_surface_distance": summarize_distances(source_to_master),
        "master_to_source_surface_distance": summarize_distances(master_to_source),
    }
    return master, report


def resolve_urdf_transforms(
    urdf_path: Path,
    hip_y_angle: float,
    knee_angle: float,
    foot_radius_m: float,
) -> tuple[
    ET.Element,
    dict[str, np.ndarray],
    dict[str, dict[str, Any]],
]:
    robot = ET.parse(urdf_path).getroot()
    child_joints: dict[str, tuple[str, np.ndarray, ET.Element]] = {}
    for joint in robot.findall("joint"):
        parent = joint.find("parent")
        child = joint.find("child")
        if parent is None or child is None:
            raise ValueError("URDF joint lacks parent or child")
        angle = 0.0
        joint_name = joint.get("name", "")
        if joint_name.endswith("_HipY_joint"):
            angle = hip_y_angle
        elif joint_name.endswith("_Knee_joint"):
            angle = knee_angle
        axis_node = joint.find("axis")
        axis = parse_vector(
            axis_node.get("xyz") if axis_node is not None else None,
            (1, 0, 0),
        )
        joint_rotation = np.eye(4)
        joint_rotation[:3, :3] = Rotation.from_rotvec(axis * angle).as_matrix()
        child_joints[child.get("link")] = (
            parent.get("link"),
            origin_transform(joint.find("origin")) @ joint_rotation,
            joint,
        )

    links = [link.get("name") for link in robot.findall("link")]
    roots = [name for name in links if name not in child_joints]
    if len(roots) != 1:
        raise ValueError(f"Expected one URDF root, found {roots}")
    transforms: dict[str, np.ndarray] = {roots[0]: np.eye(4)}

    def resolve(name: str) -> np.ndarray:
        if name in transforms:
            return transforms[name]
        parent_name, joint_transform, _ = child_joints[name]
        transforms[name] = resolve(parent_name) @ joint_transform
        return transforms[name]

    for name in links:
        resolve(name)

    foot_names = ("FL_FOOT", "FR_FOOT", "HL_FOOT", "HR_FOOT")
    foot_z = np.asarray([transforms[name][2, 3] for name in foot_names])
    if np.ptp(foot_z) > 1.0e-8:
        raise ValueError("Factory pose does not place all feet at one height")
    root_shift = np.eye(4)
    root_shift[2, 3] = foot_radius_m - float(np.mean(foot_z))
    transforms = {name: root_shift @ matrix for name, matrix in transforms.items()}

    joints: dict[str, dict[str, Any]] = {}
    for child_name, (parent_name, _, joint) in child_joints.items():
        if joint.get("type") != "revolute":
            continue
        joint_frame = transforms[parent_name] @ origin_transform(joint.find("origin"))
        axis_node = joint.find("axis")
        axis_local = parse_vector(
            axis_node.get("xyz") if axis_node is not None else None,
            (1, 0, 0),
        )
        axis_world = joint_frame[:3, :3] @ axis_local
        axis_world /= np.linalg.norm(axis_world)
        joints[joint.get("name", child_name)] = {
            "parent": parent_name,
            "child": child_name,
            "center_m": joint_frame[:3, 3],
            "axis": axis_world,
        }
    return robot, transforms, joints


def build_world_links(
    robot: ET.Element,
    transforms: dict[str, np.ndarray],
    masters: dict[str, trimesh.Trimesh],
) -> dict[str, trimesh.Trimesh]:
    result: dict[str, trimesh.Trimesh] = {}
    for link in robot.findall("link"):
        link_name = link.get("name")
        visuals = link.findall("visual")
        if not visuals:
            continue
        if len(visuals) != 1:
            raise ValueError(f"Expected one visual on {link_name}")
        mesh_node = visuals[0].find("./geometry/mesh")
        if mesh_node is None:
            continue
        component_name = Path(mesh_node.get("filename")).stem.lower()
        if component_name not in masters:
            raise ValueError(f"Unexpected mesh component {component_name}")
        scale = parse_vector(mesh_node.get("scale"), (1, 1, 1))
        scale_matrix = np.eye(4)
        scale_matrix[0, 0] = scale[0]
        scale_matrix[1, 1] = scale[1]
        scale_matrix[2, 2] = scale[2]
        world_transform = (
            transforms[link_name]
            @ origin_transform(visuals[0].find("origin"))
            @ scale_matrix
        )
        mesh = masters[component_name].copy()
        mesh.apply_transform(world_transform)
        if np.linalg.det(world_transform[:3, :3]) < 0:
            mesh.invert()
        mesh.remove_unreferenced_vertices()
        result[link_name] = mesh
    return result


def trimesh_cylinder_between(
    start: np.ndarray,
    end: np.ndarray,
    radius: float,
    sections: int = 32,
) -> trimesh.Trimesh:
    direction = np.asarray(end, dtype=float) - np.asarray(start, dtype=float)
    length = float(np.linalg.norm(direction))
    if length <= 0:
        raise ValueError("Cylinder endpoints must differ")
    transform = trimesh.geometry.align_vectors([0, 0, 1], direction)
    transform[:3, 3] = (np.asarray(start) + np.asarray(end)) / 2.0
    return trimesh.creation.cylinder(
        radius=radius,
        height=length,
        sections=sections,
        transform=transform,
    )


def oriented_box_mesh(
    size: np.ndarray,
    center: np.ndarray,
    rotation: np.ndarray,
) -> trimesh.Trimesh:
    size = np.asarray(size, dtype=float)
    center = np.asarray(center, dtype=float)
    rotation = np.asarray(rotation, dtype=float)
    if size.shape != (3,) or center.shape != (3,) or rotation.shape != (3, 3):
        raise ValueError("Oriented box expects size[3], center[3], rotation[3,3]")
    if not np.allclose(rotation.T @ rotation, np.eye(3), atol=1.0e-7):
        raise ValueError("Oriented box rotation must be orthonormal")
    if not math.isclose(float(np.linalg.det(rotation)), 1.0, abs_tol=1.0e-7):
        raise ValueError("Oriented box rotation must be right-handed")
    transform = np.eye(4)
    transform[:3, :3] = rotation
    transform[:3, 3] = center
    return trimesh.creation.box(extents=size, transform=transform)


def rectangular_beam_between(
    start: np.ndarray,
    end: np.ndarray,
    width_axis: np.ndarray,
    width: float,
    thickness: float,
) -> trimesh.Trimesh:
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    direction = end - start
    length = float(np.linalg.norm(direction))
    if length <= 0:
        raise ValueError("Beam endpoints must differ")
    direction /= length
    # Copy before orthogonalization. Mutating a caller-owned axis here shifts
    # every later hole, plate, and fastener that reuses the same frame vector.
    width_direction = np.array(width_axis, dtype=float, copy=True)
    width_direction -= direction * float(np.dot(width_direction, direction))
    width_norm = float(np.linalg.norm(width_direction))
    if width_norm <= 1.0e-8:
        raise ValueError("Beam width axis must not be parallel to its length")
    width_direction /= width_norm
    thickness_direction = np.cross(direction, width_direction)
    thickness_direction /= np.linalg.norm(thickness_direction)
    rotation = np.column_stack(
        [width_direction, thickness_direction, direction]
    )
    return oriented_box_mesh(
        np.asarray([width, thickness, length], dtype=float),
        (start + end) / 2.0,
        rotation,
    )


def socket_head_screw_mesh(
    under_head_center: np.ndarray,
    insertion_direction: np.ndarray,
    shaft_length: float,
    shaft_diameter: float,
    head_diameter: float,
    head_height: float,
    hex_flat: float,
    hex_depth: float,
) -> trimesh.Trimesh:
    under_head_center = np.asarray(under_head_center, dtype=float)
    direction = np.asarray(insertion_direction, dtype=float)
    direction /= np.linalg.norm(direction)
    overlap = 0.00005
    shaft = trimesh_cylinder_between(
        under_head_center - direction * overlap,
        under_head_center + direction * shaft_length,
        shaft_diameter / 2.0,
        40,
    )
    head = trimesh_cylinder_between(
        under_head_center - direction * head_height,
        under_head_center + direction * overlap,
        head_diameter / 2.0,
        48,
    )
    screw = md.Manifold.batch_boolean(
        [mesh_to_manifold(shaft), mesh_to_manifold(head)],
        md.OpType.Add,
    )
    if hex_depth > 0:
        hex_radius = hex_flat / (2.0 * math.cos(math.pi / 6.0))
        outward_face = under_head_center - direction * head_height
        hex_cutter = trimesh_cylinder_between(
            outward_face - direction * 0.00005,
            outward_face + direction * hex_depth,
            hex_radius,
            6,
        )
        screw = screw - mesh_to_manifold(hex_cutter)
    return manifold_to_mesh(screw.simplify(1.0e-7))


def annular_sleeve_between(
    start: np.ndarray,
    end: np.ndarray,
    outer_radius: float,
    inner_radius: float,
    sections: int = 40,
) -> md.Manifold:
    if inner_radius <= 0 or outer_radius <= inner_radius:
        raise ValueError("Annular sleeve radii must satisfy outer > inner > 0")
    outer = mesh_to_manifold(
        trimesh_cylinder_between(start, end, outer_radius, sections)
    )
    inner = mesh_to_manifold(
        trimesh_cylinder_between(start, end, inner_radius, sections)
    )
    return outer - inner


def rounded_box_xy_mm(
    size_mm: tuple[float, float, float],
    center_mm: tuple[float, float, float],
    radius_mm: float,
) -> md.Manifold:
    length, width, height = np.asarray(size_mm, dtype=float) / 1000.0
    center = np.asarray(center_mm, dtype=float) / 1000.0
    radius = radius_mm / 1000.0
    parts = [
        manifold_box([length - 2 * radius, width, height], center),
        manifold_box([length, width - 2 * radius, height], center),
    ]
    for x_sign in (-1.0, 1.0):
        for y_sign in (-1.0, 1.0):
            cylinder = md.Manifold.cylinder(
                height,
                radius,
                radius,
                48,
                center=True,
            ).translate(
                [
                    center[0] + x_sign * (length / 2 - radius),
                    center[1] + y_sign * (width / 2 - radius),
                    center[2],
                ]
            )
            parts.append(cylinder)
    return md.Manifold.batch_boolean(parts, md.OpType.Add)


def rigid_transform_y_mm(
    angle_deg: float,
    pivot_mm: np.ndarray | list[float] | tuple[float, float, float],
    translation_mm: np.ndarray | list[float] | tuple[float, float, float] = (
        0.0,
        0.0,
        0.0,
    ),
) -> np.ndarray:
    rotation = Rotation.from_euler("y", angle_deg, degrees=True).as_matrix()
    pivot_m = np.asarray(pivot_mm, dtype=float) / 1000.0
    translation_m = np.asarray(translation_mm, dtype=float) / 1000.0
    matrix = np.eye(4)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = pivot_m + translation_m - rotation @ pivot_m
    return matrix


def transform_manifold(
    manifold: md.Manifold,
    matrix: np.ndarray,
) -> md.Manifold:
    mesh = manifold_to_mesh(manifold)
    mesh.apply_transform(matrix)
    return mesh_to_manifold(mesh)


def transform_point_mm(
    point_mm: np.ndarray | list[float] | tuple[float, float, float],
    matrix: np.ndarray,
) -> np.ndarray:
    point_m = np.append(np.asarray(point_mm, dtype=float) / 1000.0, 1.0)
    return (matrix @ point_m)[:3] * 1000.0


def transform_from_rotation_translation_mm(
    rotation: np.ndarray,
    translation_mm: np.ndarray | list[float] | tuple[float, float, float],
) -> np.ndarray:
    matrix = np.eye(4)
    matrix[:3, :3] = np.asarray(rotation, dtype=float)
    matrix[:3, 3] = np.asarray(translation_mm, dtype=float) / 1000.0
    return matrix


def source_assembly_to_robot_transform(
    origin_mm: np.ndarray | list[float] | tuple[float, float, float],
) -> np.ndarray:
    # Official sensor-part source frame: +X forward, +Y up, +Z right.
    # Replica frame: +X forward, +Y left, +Z up.
    rotation = np.asarray(
        [
            [1.0, 0.0, 0.0],
            [0.0, 0.0, -1.0],
            [0.0, 1.0, 0.0],
        ],
        dtype=float,
    )
    if not math.isclose(float(np.linalg.det(rotation)), 1.0, abs_tol=1.0e-9):
        raise ValueError("Sensor source-to-robot transform must be a rotation")
    return transform_from_rotation_translation_mm(rotation, origin_mm)


def build_lidar_geometry(
    config: dict[str, Any],
    sensor_masters: dict[str, trimesh.Trimesh],
) -> dict[str, trimesh.Trimesh]:
    parameters = config["lidar_module"]["parameters_mm"]

    def value(name: str) -> Any:
        return parameters[name]["value"]

    deck_center = tuple(float(v) for v in value("deck_center"))
    deck_size = tuple(float(v) for v in value("deck_size"))
    rail_size = np.asarray(value("base_side_rail_size"), dtype=float)
    rail_center_x = float(value("base_side_rail_center_x"))
    rail_center_y = float(value("base_side_rail_center_y"))
    crossbar_x = np.asarray(value("base_sensor_crossbar_x"), dtype=float)
    crossbar_size = np.asarray(
        value("base_sensor_crossbar_size"),
        dtype=float,
    )
    deck_parts = [
        rounded_box_xy_mm(
            rail_size,
            [rail_center_x, y_sign * rail_center_y, deck_center[2]],
            4.0,
        )
        for y_sign in (-1.0, 1.0)
    ]
    deck_parts.extend(
        [
            rounded_box_xy_mm(
                np.asarray(value("base_rear_pad_size"), dtype=float),
                [
                    float(value("base_rear_pad_center_x")),
                    deck_center[1],
                    deck_center[2],
                ],
                4.0,
            ),
            rounded_box_xy_mm(
                np.asarray(value("base_center_bridge_size"), dtype=float),
                [62.0, deck_center[1], deck_center[2]],
                4.0,
            ),
        ]
    )
    deck_parts.extend(
        rounded_box_xy_mm(
            crossbar_size,
            [x, deck_center[1], deck_center[2]],
            4.0,
        )
        for x in crossbar_x
    )
    agx_orin_base_rotation = np.asarray(
        [
            [1.0, 0.0, 0.0],
            [0.0, 0.0, -1.0],
            [0.0, 1.0, 0.0],
        ],
        dtype=float,
    )
    agx_orin_base_to_robot = transform_from_rotation_translation_mm(
        agx_orin_base_rotation,
        value("agx_orin_base_translation"),
    )
    agx_mount_centers_source = np.asarray(
        value("agx_orin_base_deck_mount_centers_source"),
        dtype=float,
    )
    agx_mount_centers_robot = np.asarray(
        [
            (
                agx_orin_base_to_robot
                @ np.append(center_source / 1000.0, 1.0)
            )[:3]
            * 1000.0
            for center_source in agx_mount_centers_source
        ]
    )
    agx_device_mount_centers_source = np.asarray(
        value("agx_orin_base_device_mount_centers_source"),
        dtype=float,
    )
    agx_device_mount_centers_robot = np.asarray(
        [
            transform_point_mm(
                center_source,
                agx_orin_base_to_robot,
            )
            for center_source in agx_device_mount_centers_source
        ]
    )
    compute_crossbar_size = np.asarray(
        value("agx_orin_compute_crossbar_size"),
        dtype=float,
    )
    deck_parts.append(
        rounded_box_xy_mm(
            compute_crossbar_size,
            [
                float(agx_mount_centers_robot[2, 0]),
                deck_center[1],
                deck_center[2],
            ],
            4.0,
        )
    )
    deck = md.Manifold.batch_boolean(deck_parts, md.OpType.Add)
    payload_hole_pattern = np.asarray(
        value("lite3_payload_hole_pattern"),
        dtype=float,
    )
    payload_hole_diameter = float(value("lite3_payload_hole_diameter"))
    holes = []
    for x_sign in (-1.0, 1.0):
        for y_sign in (-1.0, 1.0):
            center = np.asarray(
                [
                    deck_center[0]
                    + x_sign * payload_hole_pattern[0] / 2.0,
                    deck_center[1]
                    + y_sign * payload_hole_pattern[1] / 2.0,
                    deck_center[2],
                ]
            ) / 1000.0
            holes.append(
                md.Manifold.cylinder(
                    max(
                        rail_size[2],
                        crossbar_size[2],
                        compute_crossbar_size[2],
                    )
                    / 1000.0
                    + 0.006,
                    payload_hole_diameter / 2000.0,
                    payload_hole_diameter / 2000.0,
                    32,
                    center=True,
                ).translate(center)
            )
    j17a_hole_pattern = np.asarray(
        value("j17a_mount_hole_pattern"),
        dtype=float,
    )
    j17a_hole_diameter = float(value("j17a_mount_hole_diameter"))
    for x in crossbar_x:
        for y_sign in (-1.0, 1.0):
            center = np.asarray(
                [
                    x,
                    y_sign * j17a_hole_pattern[1] / 2.0,
                    deck_center[2],
                ]
            ) / 1000.0
            holes.append(
                md.Manifold.cylinder(
                    max(crossbar_size[2], compute_crossbar_size[2]) / 1000.0
                    + 0.006,
                    j17a_hole_diameter / 2000.0,
                    j17a_hole_diameter / 2000.0,
                    32,
                    center=True,
                ).translate(center)
            )
    agx_mount_diameters = np.asarray(
        value("agx_orin_base_deck_mount_diameters"),
        dtype=float,
    )
    for mount_center, diameter in zip(
        agx_mount_centers_robot,
        agx_mount_diameters,
        strict=True,
    ):
        holes.append(
            md.Manifold.cylinder(
                max(rail_size[2], compute_crossbar_size[2]) / 1000.0
                + 0.006,
                float(diameter) / 2000.0,
                float(diameter) / 2000.0,
                40,
                center=True,
            ).translate(
                np.asarray(
                    [
                        mount_center[0],
                        mount_center[1],
                        deck_center[2],
                    ]
                )
                / 1000.0
            )
        )
    deck = deck - md.Manifold.batch_boolean(
        holes,
        md.OpType.Add,
    )

    agx_orin_base_mesh = transform_mesh(
        sensor_masters["agx_orin_base"],
        agx_orin_base_to_robot,
    )
    jetson_center = np.asarray(
        value("jetson_agx_orin_center"),
        dtype=float,
    )
    jetson_size = np.asarray(
        value("jetson_agx_orin_envelope"),
        dtype=float,
    )
    jetson_bottom_z = jetson_center[2] - jetson_size[2] / 2.0
    jetson_top_z = jetson_center[2] + jetson_size[2] / 2.0
    lower_tray_height = 24.0
    lower_tray = rounded_box_xy_mm(
        tuple(jetson_size[[0, 1]].tolist() + [lower_tray_height]),
        (
            float(jetson_center[0]),
            float(jetson_center[1]),
            float(jetson_bottom_z + lower_tray_height / 2.0),
        ),
        3.0,
    )
    port_depth = float(value("jetson_agx_orin_port_cut_depth"))
    port_z = jetson_bottom_z + 11.0
    side_port_specs = (
        (-100.0, 15.0, 7.0),
        (-84.0, 8.0, 5.0),
        (-70.0, 10.0, 5.0),
        (-51.0, 16.0, 13.0),
        (-26.0, 22.0, 14.0),
    )
    port_cuts = [
        manifold_box(
            np.asarray([width, port_depth, height]) / 1000.0,
            np.asarray(
                [
                    x,
                    jetson_center[1] - jetson_size[1] / 2.0,
                    port_z,
                ]
            )
            / 1000.0,
        )
        for x, width, height in side_port_specs
    ]
    rear_port_specs = (
        (-17.0, 18.0, 13.0),
        (17.0, 18.0, 13.0),
        (38.0, 10.0, 5.0),
    )
    port_cuts.extend(
        manifold_box(
            np.asarray([port_depth, width, height]) / 1000.0,
            np.asarray(
                [
                    jetson_center[0] - jetson_size[0] / 2.0,
                    y,
                    port_z,
                ]
            )
            / 1000.0,
        )
        for y, width, height in rear_port_specs
    )
    dc_port = mesh_to_manifold(
        trimesh_cylinder_between(
            np.asarray(
                [
                    jetson_center[0] - 6.0,
                    jetson_center[1] - jetson_size[1] / 2.0
                    - port_depth,
                    port_z,
                ]
            )
            / 1000.0,
            np.asarray(
                [
                    jetson_center[0] - 6.0,
                    jetson_center[1] - jetson_size[1] / 2.0
                    + port_depth,
                    port_z,
                ]
            )
            / 1000.0,
            4.2 / 1000.0,
            40,
        )
    )
    lower_tray = lower_tray - md.Manifold.batch_boolean(
        [*port_cuts, dc_port],
        md.OpType.Add,
    )
    blind_mount_depth = float(value("jetson_agx_orin_blind_mount_depth"))
    jetson_blind_mount_diameter = float(
        value("jetson_agx_orin_blind_mount_diameter")
    )
    jetson_mount_holes = []
    for mount_center in agx_device_mount_centers_robot:
        jetson_mount_holes.append(
            mesh_to_manifold(
                trimesh_cylinder_between(
                    np.asarray(
                        [
                            mount_center[0],
                            mount_center[1],
                            jetson_bottom_z - 1.0,
                        ]
                    )
                    / 1000.0,
                    np.asarray(
                        [
                            mount_center[0],
                            mount_center[1],
                            jetson_bottom_z + blind_mount_depth,
                        ]
                    )
                    / 1000.0,
                    jetson_blind_mount_diameter / 2000.0,
                    32,
                )
            )
        )
    lower_tray = lower_tray - md.Manifold.batch_boolean(
        jetson_mount_holes,
        md.OpType.Add,
    )
    connector_parts = [
        manifold_box(
            np.asarray(
                [
                    max(2.0, width - 1.2),
                    1.0,
                    max(2.0, height - 1.2),
                ]
            )
            / 1000.0,
            np.asarray(
                [
                    x,
                    jetson_center[1] - jetson_size[1] / 2.0 + 2.5,
                    port_z,
                ]
            )
            / 1000.0,
        )
        for x, width, height in side_port_specs
    ]
    connector_parts.extend(
        manifold_box(
            np.asarray(
                [
                    1.0,
                    max(2.0, width - 1.2),
                    max(2.0, height - 1.2),
                ]
            )
            / 1000.0,
            np.asarray(
                [
                    jetson_center[0] - jetson_size[0] / 2.0 + 2.5,
                    y,
                    port_z,
                ]
            )
            / 1000.0,
        )
        for y, width, height in rear_port_specs
    )
    connector_parts.append(
        mesh_to_manifold(
            trimesh_cylinder_between(
                np.asarray(
                    [
                        jetson_center[0] - 6.0,
                        jetson_center[1] - jetson_size[1] / 2.0 + 2.0,
                        port_z,
                    ]
                )
                / 1000.0,
                np.asarray(
                    [
                        jetson_center[0] - 6.0,
                        jetson_center[1] - jetson_size[1] / 2.0 + 3.0,
                        port_z,
                    ]
                )
                / 1000.0,
                3.5 / 1000.0,
                40,
            )
        )
    )
    jetson_connectors = md.Manifold.batch_boolean(
        connector_parts,
        md.OpType.Add,
    )

    heatsink_bottom_z = jetson_bottom_z + 22.0
    heatsink_footprint = 100.0
    heatsink_parts = [
        manifold_box(
            np.asarray([heatsink_footprint, heatsink_footprint, 5.0])
            / 1000.0,
            np.asarray(
                [
                    jetson_center[0],
                    jetson_center[1],
                    heatsink_bottom_z + 2.5,
                ]
            )
            / 1000.0,
        )
    ]
    cage_bottom_z = jetson_bottom_z + 22.0
    cage_height = jetson_top_z - cage_bottom_z
    for x_sign in (-1.0, 1.0):
        for y_sign in (-1.0, 1.0):
            heatsink_parts.append(
                manifold_box(
                    np.asarray([6.0, 6.0, cage_height]) / 1000.0,
                    np.asarray(
                        [
                            jetson_center[0]
                            + x_sign * (heatsink_footprint / 2.0 - 3.0),
                            jetson_center[1]
                            + y_sign * (heatsink_footprint / 2.0 - 3.0),
                            cage_bottom_z + cage_height / 2.0,
                        ]
                    )
                    / 1000.0,
                )
            )
    top_frame_z = jetson_top_z - 1.75
    heatsink_parts.extend(
        [
            manifold_box(
                np.asarray([heatsink_footprint, 6.0, 3.5]) / 1000.0,
                np.asarray(
                    [
                        jetson_center[0],
                        jetson_center[1] + y_sign * 47.0,
                        top_frame_z,
                    ]
                )
                / 1000.0,
            )
            for y_sign in (-1.0, 1.0)
        ]
    )
    heatsink_parts.extend(
        [
            manifold_box(
                np.asarray([6.0, heatsink_footprint, 3.5]) / 1000.0,
                np.asarray(
                    [
                        jetson_center[0] + x_sign * 47.0,
                        jetson_center[1],
                        top_frame_z,
                    ]
                )
                / 1000.0,
            )
            for x_sign in (-1.0, 1.0)
        ]
    )
    for x_offset in np.arange(-42.0, 42.1, 6.0):
        heatsink_parts.append(
            manifold_box(
                np.asarray([2.4, 94.0, 3.5]) / 1000.0,
                np.asarray(
                    [
                        jetson_center[0] + x_offset,
                        jetson_center[1],
                        top_frame_z,
                    ]
                )
                / 1000.0,
            )
        )
    side_panel_height = cage_height - 3.5
    side_panel_center_z = cage_bottom_z + side_panel_height / 2.0
    heatsink_parts.extend(
        [
            manifold_box(
                np.asarray([4.0, 94.0, side_panel_height]) / 1000.0,
                np.asarray(
                    [
                        jetson_center[0] + 48.0,
                        jetson_center[1],
                        side_panel_center_z,
                    ]
                )
                / 1000.0,
            ),
            manifold_box(
                np.asarray([94.0, 4.0, side_panel_height]) / 1000.0,
                np.asarray(
                    [
                        jetson_center[0],
                        jetson_center[1] + 48.0,
                        side_panel_center_z,
                    ]
                )
                / 1000.0,
            ),
        ]
    )
    for z in np.linspace(cage_bottom_z + 4.5, jetson_top_z - 6.0, 9):
        heatsink_parts.extend(
            [
                manifold_box(
                    np.asarray([4.0, 94.0, 2.0]) / 1000.0,
                    np.asarray(
                        [
                            jetson_center[0] - 48.0,
                            jetson_center[1],
                            z,
                        ]
                    )
                    / 1000.0,
                ),
                manifold_box(
                    np.asarray([94.0, 4.0, 2.0]) / 1000.0,
                    np.asarray(
                        [
                            jetson_center[0],
                            jetson_center[1] - 48.0,
                            z,
                        ]
                    )
                    / 1000.0,
                ),
            ]
        )
    heatsink = md.Manifold.batch_boolean(
        heatsink_parts,
        md.OpType.Add,
    )
    button_parts = []
    for y in (-18.0, -6.0, 6.0):
        button_parts.append(
            mesh_to_manifold(
                trimesh_cylinder_between(
                    np.asarray(
                        [
                            jetson_center[0] + jetson_size[0] / 2.0 - 2.5,
                            jetson_center[1] + y,
                            port_z,
                        ]
                    )
                    / 1000.0,
                    np.asarray(
                        [
                            jetson_center[0] + jetson_size[0] / 2.0,
                            jetson_center[1] + y,
                            port_z,
                        ]
                    )
                    / 1000.0,
                    2.2 / 1000.0,
                    32,
                )
            )
        )
    jetson_outer = md.Manifold.batch_boolean(
        [lower_tray, heatsink, *button_parts],
        md.OpType.Add,
    )
    jetson_carrier_visual = md.Manifold.batch_boolean(
        [lower_tray, *button_parts],
        md.OpType.Add,
    )
    fan_z = jetson_top_z - 6.0
    fan_outer = md.Manifold.cylinder(
        3.0 / 1000.0,
        34.0 / 1000.0,
        34.0 / 1000.0,
        64,
        center=True,
    ).translate(
        [
            jetson_center[0] / 1000.0,
            jetson_center[1] / 1000.0,
            fan_z / 1000.0,
        ]
    )
    fan_inner = md.Manifold.cylinder(
        5.0 / 1000.0,
        25.0 / 1000.0,
        25.0 / 1000.0,
        64,
        center=True,
    ).translate(
        [
            jetson_center[0] / 1000.0,
            jetson_center[1] / 1000.0,
            fan_z / 1000.0,
        ]
    )
    fan_ring = fan_outer - fan_inner
    fan_hub = md.Manifold.cylinder(
        3.0 / 1000.0,
        9.0 / 1000.0,
        9.0 / 1000.0,
        48,
        center=True,
    ).translate(
        [
            jetson_center[0] / 1000.0,
            jetson_center[1] / 1000.0,
            fan_z / 1000.0,
        ]
    )
    fan_arms = [
        manifold_box(
            np.asarray(size_mm) / 1000.0,
            np.asarray([jetson_center[0], jetson_center[1], fan_z])
            / 1000.0,
        )
        for size_mm in ([68.0, 4.0, 3.0], [4.0, 68.0, 3.0])
    ]
    jetson_fan = md.Manifold.batch_boolean(
        [fan_ring, fan_hub, *fan_arms],
        md.OpType.Add,
    )
    module = sensor_masters["jetson_agx_orin_module"]
    module_center_source = np.mean(module.bounds, axis=0)
    module_bottom_source = float(module.bounds[0, 2])
    module_translation_mm = np.asarray(
        [
            jetson_center[0] - module_center_source[0] * 1000.0,
            jetson_center[1] - module_center_source[1] * 1000.0,
            float(value("jetson_agx_orin_module_bottom_z"))
            - module_bottom_source * 1000.0,
        ]
    )
    jetson_module_mesh = transform_mesh(
        module,
        transform_from_rotation_translation_mm(
            np.eye(3),
            module_translation_mm,
        ),
    )

    assembly_to_robot = source_assembly_to_robot_transform(
        value("sensor_assembly_origin")
    )
    tilt_deg = float(value("j20a_tilt_deg"))
    source_tilt = Rotation.from_euler(
        "z",
        -tilt_deg,
        degrees=True,
    ).as_matrix()
    mount_normal_source = source_tilt @ np.asarray([0.0, 1.0, 0.0])

    j20a_mesh = transform_mesh(
        sensor_masters["j20a"],
        assembly_to_robot,
    )
    j20a_pattern_center_robot = (
        assembly_to_robot
        @ np.append(
            np.asarray(
                value("j20a_mid360_pattern_center_source"),
                dtype=float,
            )
            / 1000.0,
            1.0,
        )
    )[:3]
    j17a_rotation = np.asarray(
        [
            [1.0, 0.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )
    j17a_ring_center = np.asarray(
        value("j17a_ring_center_source"),
        dtype=float,
    )
    j17a_translation = (
        j20a_pattern_center_robot * 1000.0
        - j17a_rotation @ j17a_ring_center
    )
    j17a_translation += np.asarray(
        [
            float(value("j17a_j20a_hole_axis_x_correction")),
            0.0,
            float(value("j17a_j20a_seating_clearance_z")),
        ],
        dtype=float,
    )
    j17a_to_robot = transform_from_rotation_translation_mm(
        j17a_rotation,
        j17a_translation,
    )
    j17a_mesh = transform_mesh(
        sensor_masters["j17a"],
        j17a_to_robot,
    )

    s410_source_transform = transform_from_rotation_translation_mm(
        Rotation.from_euler(
            "z",
            float(value("s410_rotation_source_z_deg")),
            degrees=True,
        ).as_matrix(),
        np.asarray(value("s410_translation_source"), dtype=float)
        + mount_normal_source
        * float(value("s410_mount_normal_clearance")),
    )
    s410_mesh = transform_mesh(
        sensor_masters["s410"],
        assembly_to_robot @ s410_source_transform,
    )

    mid360_rotation = (
        source_tilt
        @ Rotation.from_euler(
            "y",
            float(value("mid360_connector_yaw_deg")),
            degrees=True,
        ).as_matrix()
    )
    mid360_mount_center = np.asarray(
        value("mid360_mount_plane_center_source"),
        dtype=float,
    )
    j20a_pattern_center = np.asarray(
        value("j20a_mid360_pattern_center_source"),
        dtype=float,
    )
    mid360_translation = (
        j20a_pattern_center - mid360_rotation @ mid360_mount_center
        + mount_normal_source * float(value("mid360_mount_normal_offset"))
    )
    mid360_source_transform = transform_from_rotation_translation_mm(
        mid360_rotation,
        mid360_translation,
    )
    mid360_mesh = transform_mesh(
        sensor_masters["mid360"],
        assembly_to_robot @ mid360_source_transform,
    )
    mid360_optical_window = transform_mesh(
        sensor_masters["mid360_optical_window"],
        assembly_to_robot @ mid360_source_transform,
    )
    mid360_body = transform_mesh(
        sensor_masters["mid360_body"],
        assembly_to_robot @ mid360_source_transform,
    )
    mid360_housing_exterior = transform_mesh(
        sensor_masters["mid360_housing_exterior"],
        assembly_to_robot @ mid360_source_transform,
    )
    mid360_connector = transform_mesh(
        sensor_masters["mid360_connector"],
        assembly_to_robot @ mid360_source_transform,
    )

    adapter_bridge_source = trimesh.creation.box(
        extents=np.asarray(
            value("mid360_adapter_bridge_size"),
            dtype=float,
        )
        / 1000.0
    )
    adapter_bridge_transform = transform_from_rotation_translation_mm(
        source_tilt,
        j20a_pattern_center
        + mount_normal_source
        * float(value("mid360_adapter_bridge_normal_offset")),
    )
    adapter_bridge_source.apply_transform(adapter_bridge_transform)
    adapter_bridge = transform_mesh(
        adapter_bridge_source,
        assembly_to_robot,
    )

    connector_outer_radius = (
        float(value("sensor_connector_sleeve_outer_diameter")) / 2000.0
    )
    connector_inner_radius = (
        float(value("sensor_connector_sleeve_inner_diameter")) / 2000.0
    )
    connector_half_length = (
        float(value("sensor_connector_sleeve_length")) / 2000.0
    )
    assembly_rotation = assembly_to_robot[:3, :3]
    vertical_axis_robot = assembly_rotation @ np.asarray([0.0, 1.0, 0.0])
    guard_axis_robot = assembly_rotation @ mount_normal_source
    connector_sleeves = []
    for point_source in value("j17a_j20a_connector_lines_source"):
        point_robot = (
            assembly_to_robot
            @ np.append(np.asarray(point_source, dtype=float) / 1000.0, 1.0)
        )[:3]
        connector_sleeves.append(
            annular_sleeve_between(
                point_robot - vertical_axis_robot * connector_half_length,
                point_robot + vertical_axis_robot * connector_half_length,
                connector_outer_radius,
                connector_inner_radius,
            )
        )
    for point_source in value("j20a_s410_connector_lines_source"):
        point_robot = (
            assembly_to_robot
            @ np.append(np.asarray(point_source, dtype=float) / 1000.0, 1.0)
        )[:3]
        connector_sleeves.append(
            annular_sleeve_between(
                point_robot - guard_axis_robot * connector_half_length,
                point_robot + guard_axis_robot * connector_half_length,
                connector_outer_radius,
                connector_inner_radius,
            )
        )
    sensor_connector_sleeves = md.Manifold.batch_boolean(
        connector_sleeves,
        md.OpType.Add,
    )

    spacer_overlap = float(value("j17a_base_spacer_overlap"))
    spacer_bottom_z = (
        deck_center[2] + rail_size[2] / 2.0 - spacer_overlap
    )
    spacer_top_z = (
        float(j17a_translation[2])
        + float(value("j17a_mount_plane_source_z"))
        + spacer_overlap
    )
    spacer_height = spacer_top_z - spacer_bottom_z
    if spacer_height <= 0:
        raise ValueError("J17A base spacer height must be positive")
    spacer_outer_radius = (
        float(value("j17a_base_spacer_outer_diameter")) / 2000.0
    )
    spacer_inner_radius = (
        float(value("j17a_mount_hole_diameter")) / 2000.0
    )
    j17a_base_spacers = []
    for x in crossbar_x:
        for y_sign in (-1.0, 1.0):
            center = np.asarray(
                [
                    x,
                    y_sign * j17a_hole_pattern[1] / 2.0,
                    (spacer_bottom_z + spacer_top_z) / 2.0,
                ],
                dtype=float,
            ) / 1000.0
            outer = md.Manifold.cylinder(
                spacer_height / 1000.0,
                spacer_outer_radius,
                spacer_outer_radius,
                40,
                center=True,
            ).translate(center)
            inner = md.Manifold.cylinder(
                spacer_height / 1000.0 + 0.002,
                spacer_inner_radius,
                spacer_inner_radius,
                40,
                center=True,
            ).translate(center)
            j17a_base_spacers.append(outer - inner)
    j17a_base_spacer_union = md.Manifold.batch_boolean(
        j17a_base_spacers,
        md.OpType.Add,
    )

    # The official exterior does not show a plate beneath the LiDAR assembly.
    # J17A remains only a source-coordinate reference; the factory-replica
    # track exposes four local annular mounts and keeps all print-only
    # connectivity inside the upper-module Boolean.
    factory_mount_parts = []
    factory_mount_bottom_z = float(value("factory_lidar_mount_bottom_z"))
    factory_mount_top_z = float(value("factory_lidar_mount_top_z"))
    factory_mount_height = factory_mount_top_z - factory_mount_bottom_z
    factory_mount_outer_radius = (
        float(value("factory_lidar_mount_outer_diameter")) / 2000.0
    )
    factory_mount_inner_radius = (
        float(value("factory_lidar_mount_hole_diameter")) / 2000.0
    )
    for post_x in value("factory_lidar_mount_x"):
        for post_y in value("factory_lidar_mount_y"):
            post_center = np.asarray(
                [
                    float(post_x),
                    float(post_y),
                    (factory_mount_bottom_z + factory_mount_top_z) / 2.0,
                ]
            )
            outer = md.Manifold.cylinder(
                factory_mount_height / 1000.0,
                factory_mount_outer_radius,
                factory_mount_outer_radius,
                40,
                center=True,
            ).translate(post_center / 1000.0)
            inner = md.Manifold.cylinder(
                factory_mount_height / 1000.0 + 0.002,
                factory_mount_inner_radius,
                factory_mount_inner_radius,
                32,
                center=True,
            ).translate(post_center / 1000.0)
            factory_mount_parts.append(outer - inner)
    factory_lidar_mounts = md.Manifold.batch_boolean(
        factory_mount_parts,
        md.OpType.Add,
    )
    factory_lidar_mounts_mesh = manifold_to_mesh(
        factory_lidar_mounts.simplify(1.0e-7)
    )
    # Two narrow print-only webs connect the rear local mounts to the front
    # mounts already engaged by the sensor assembly.  They stay below the
    # adapter and are deliberately omitted from the official visual track.
    factory_mount_x = np.asarray(value("factory_lidar_mount_x"), dtype=float)
    print_web_length = float(np.ptp(factory_mount_x)) + 4.0
    print_web_center_x = float(np.mean(factory_mount_x))
    print_web_center_z = factory_mount_top_z - 2.0
    factory_mount_print_webs = md.Manifold.batch_boolean(
        [
            manifold_box(
                np.asarray([print_web_length, 4.0, 4.0]) / 1000.0,
                np.asarray(
                    [
                        print_web_center_x,
                        float(post_y) + math.copysign(4.0, float(post_y)),
                        print_web_center_z,
                    ]
                )
                / 1000.0,
            )
            for post_y in value("factory_lidar_mount_y")
        ],
        md.OpType.Add,
    )

    sensor_cluster = md.Manifold.batch_boolean(
        [
            factory_lidar_mounts,
            factory_mount_print_webs,
            mesh_to_manifold(j20a_mesh),
            mesh_to_manifold(s410_mesh),
            mesh_to_manifold(mid360_mesh),
            mesh_to_manifold(adapter_bridge),
            sensor_connector_sleeves,
        ],
        md.OpType.Add,
    )

    upper = md.Manifold.batch_boolean(
        [
            deck,
            sensor_cluster,
        ],
        md.OpType.Add,
    )
    # Remove Boolean-generated collinear triangles below 0.0001 mm. They are
    # topologically harmless in Manifold3D but collapse in float32 STL and
    # otherwise create a three-edge round-trip hole.
    # J17A contains many sub-0.01 mm tessellation slivers which are valid in
    # float64 but collapse when the print master is written as float32 STL.
    # A 0.01 mm simplification is far below the 0.20 mm layer height and keeps
    # the source-backed holes while making the exported union round-trip clean.
    upper_mesh = manifold_to_mesh(upper.simplify(1.0e-5))

    d435i_size = np.asarray(value("d435i_nominal_size"), dtype=float)
    camera_mount_center_source = np.asarray(
        value("d435i_mount_center_j17a_source"),
        dtype=float,
    )
    camera_mount_center_robot = (
        j17a_to_robot
        @ np.append(camera_mount_center_source / 1000.0, 1.0)
    )[:3]
    camera_forward = (
        j17a_rotation
        @ np.asarray(
            value("d435i_mount_axis_j17a_source"),
            dtype=float,
        )
    )
    camera_forward /= np.linalg.norm(camera_forward)
    camera_width_axis = np.asarray([0.0, 1.0, 0.0])
    camera_up = np.cross(camera_forward, camera_width_axis)
    camera_up /= np.linalg.norm(camera_up)
    camera_local_rotation = np.column_stack(
        [camera_forward, camera_width_axis, camera_up]
    )
    if not math.isclose(
        float(np.linalg.det(camera_local_rotation)),
        1.0,
        abs_tol=1.0e-6,
    ):
        raise ValueError("D435i camera transform must be right-handed")
    camera_standoff = float(value("d435i_mount_standoff"))
    camera_body_mount_center_robot = (
        camera_mount_center_robot + camera_forward * camera_standoff / 1000.0
    )
    # RealSense's pinned ROS D435i description reuses the official d435.dae
    # aluminum-case mesh. In that source, X is width, Y is camera-up and +Z
    # points from the rear enclosure toward the front optical plate. Keep the
    # exact open visual mesh and a separately reconstructed printable solid on
    # one source-to-robot transform; do not redraw the camera as a rounded box.
    d435i_visual_source = sensor_masters["d435i_visual"]
    d435i_print_source = sensor_masters["d435i"]
    camera_source_rotation = np.column_stack(
        [camera_width_axis, camera_up, camera_forward]
    )
    if not math.isclose(
        float(np.linalg.det(camera_source_rotation)),
        1.0,
        abs_tol=1.0e-6,
    ):
        raise ValueError("D435i source transform must be right-handed")
    source_front_z = float(d435i_visual_source.bounds[1, 2])
    source_rear_z = float(d435i_visual_source.bounds[0, 2])
    source_depth_m = source_front_z - source_rear_z
    nominal_depth_m = float(d435i_size[0]) / 1000.0
    if not math.isclose(
        source_depth_m,
        nominal_depth_m,
        abs_tol=0.00015,
    ):
        raise ValueError(
            "Official D435i ROS mesh depth disagrees with the datasheet: "
            f"{source_depth_m * 1000.0:.6f} mm"
        )
    camera_front_center_robot = (
        camera_body_mount_center_robot + camera_forward * source_depth_m
    )
    camera_source_transform = np.eye(4)
    camera_source_transform[:3, :3] = camera_source_rotation
    camera_source_transform[:3, 3] = (
        camera_front_center_robot
        - camera_source_rotation
        @ np.asarray([0.0, 0.0, source_front_z])
    )
    camera_visual_mesh = transform_mesh(
        d435i_visual_source,
        camera_source_transform,
    )
    camera_visual_mesh.metadata.update(
        {
            "source_model": "official_realsense_ros_d435_mesh_for_d435i",
            "source_to_robot_transform": camera_source_transform.tolist(),
            "source_bbox_mm": (
                d435i_visual_source.extents * 1000.0
            ).tolist(),
            "print_ready": False,
        }
    )
    camera_print_body_mesh = transform_mesh(
        d435i_print_source,
        camera_source_transform,
    )
    mounting_contract = config["d435i_mounting_contract"]
    camera_mount_config = config["assembly_mounts"][
        "camera_mount_bracket"
    ]
    hole_spacing = float(value("d435i_mount_hole_spacing"))
    camera_hole_centers = [
        (
            camera_body_mount_center_robot
            + camera_width_axis * y_sign * hole_spacing / 2000.0
        )
        for y_sign in (-1.0, 1.0)
    ]

    # The source-derived voxel print proxy expands roughly half a voxel beyond
    # the official rear plane. Trim only that reconstruction overgrowth so the
    # separate bracket pads can seat on the declared D435i rear mounting plane.
    crop_depth_m = source_depth_m + 0.020
    camera_crop = oriented_box_mesh(
        np.asarray([crop_depth_m, 0.200, 0.200]),
        camera_body_mount_center_robot
        + camera_forward * crop_depth_m / 2.0,
        camera_local_rotation,
    )
    camera_print_body = (
        mesh_to_manifold(camera_print_body_mesh)
        ^ mesh_to_manifold(camera_crop)
    )
    print_clearance_hole_diameter_m = float(
        camera_mount_config[
            "print_clearance_hole_diameter_master_mm"
        ]
    ) / 1000.0
    camera_thread_depth_m = float(
        mounting_contract["official_maximum_thread_insertion_mm"]
    ) / 1000.0
    camera_print_hole_cutters = [
        mesh_to_manifold(
            trimesh_cylinder_between(
                hole_center - camera_forward * 0.0001,
                hole_center
                + camera_forward * (camera_thread_depth_m + 0.0001),
                print_clearance_hole_diameter_m / 2.0,
                40,
            )
        )
        for hole_center in camera_hole_centers
    ]
    camera_print_body = camera_print_body - md.Manifold.batch_boolean(
        camera_print_hole_cutters,
        md.OpType.Add,
    )
    camera_print_mesh = manifold_to_mesh(
        camera_print_body.simplify(1.0e-7)
    )

    plate_width_m = float(
        mounting_contract["bracket_plate_width_mm"]
    ) / 1000.0
    carrier_plate_width_m = float(
        mounting_contract["bracket_carrier_plate_width_mm"]
    ) / 1000.0
    plate_height_m = float(
        mounting_contract["bracket_plate_height_mm"]
    ) / 1000.0
    plate_thickness_m = float(
        mounting_contract["bracket_plate_thickness_mm"]
    ) / 1000.0
    mating_clearance_m = float(
        mounting_contract["bracket_main_face_clearance_mm"]
    ) / 1000.0
    pad_outer_radius_m = float(
        mounting_contract["bracket_mating_pad_outer_diameter_mm"]
    ) / 2000.0
    central_access_radius_m = float(
        mounting_contract[
            "bracket_central_quarter_twenty_access_diameter_mm"
        ]
    ) / 2000.0
    plate_front_center = (
        camera_body_mount_center_robot
        - camera_forward * mating_clearance_m
    )
    plate_center = (
        plate_front_center - camera_forward * plate_thickness_m / 2.0
    )
    plate_back_center = (
        plate_front_center - camera_forward * plate_thickness_m
    )
    carrier_mount_center_robot = camera_mount_center_robot
    carrier_hole_centers = [
        (
            carrier_mount_center_robot
            + camera_width_axis * y_sign * hole_spacing / 2000.0
        )
        for y_sign in (-1.0, 1.0)
    ]
    carrier_plate_back_center = (
        carrier_mount_center_robot + camera_forward * mating_clearance_m
    )
    carrier_plate_center = (
        carrier_plate_back_center
        + camera_forward * plate_thickness_m / 2.0
    )
    carrier_plate_front_center = (
        carrier_plate_back_center + camera_forward * plate_thickness_m
    )
    bracket_arm_width_m = float(
        mounting_contract["bracket_arm_width_mm"]
    ) / 1000.0
    bracket_arm_thickness_m = float(
        mounting_contract["bracket_arm_thickness_mm"]
    ) / 1000.0
    side_join_vertical_offset_m = float(
        mounting_contract["side_join_vertical_offset_mm"]
    ) / 1000.0

    def build_camera_bracket(
        camera_hole_diameter_m: float,
        side_hole_diameter_m: float,
    ) -> trimesh.Trimesh:
        parts = [
            mesh_to_manifold(
                oriented_box_mesh(
                    np.asarray(
                        [
                            plate_thickness_m,
                            plate_width_m,
                            plate_height_m,
                        ]
                    ),
                    plate_center,
                    camera_local_rotation,
                )
            ),
        ]
        for camera_hole_center in camera_hole_centers:
            pad_offset = (
                camera_hole_center - camera_body_mount_center_robot
            )
            parts.append(
                annular_sleeve_between(
                    plate_front_center
                    + pad_offset
                    - camera_forward * 0.00005,
                    camera_body_mount_center_robot + pad_offset,
                    pad_outer_radius_m,
                    camera_hole_diameter_m / 2.0,
                    40,
                )
            )
        for y_sign in (-1.0, 1.0):
            camera_width_offset = camera_width_axis * y_sign * (
                plate_width_m / 2.0 - bracket_arm_width_m / 2.0
            )
            carrier_width_offset = camera_width_axis * y_sign * (
                carrier_plate_width_m / 2.0 + bracket_arm_width_m / 2.0
            )
            for up_sign in (-1.0, 1.0):
                height_offset = (
                    camera_up * up_sign * side_join_vertical_offset_m
                )
                parts.append(
                    mesh_to_manifold(
                        rectangular_beam_between(
                            carrier_plate_center
                            + carrier_width_offset
                            + height_offset,
                            plate_center
                            + camera_width_offset
                            + height_offset,
                            camera_width_axis,
                            bracket_arm_width_m,
                            bracket_arm_thickness_m,
                        )
                    )
                )
        bracket = md.Manifold.batch_boolean(parts, md.OpType.Add)
        camera_hole_cutters = [
            mesh_to_manifold(
                trimesh_cylinder_between(
                    plate_back_center - camera_forward * 0.0002,
                    camera_body_mount_center_robot
                    + camera_forward * 0.0002,
                    camera_hole_diameter_m / 2.0,
                    40,
                )
            )
            for hole_center in camera_hole_centers
        ]
        # Recenter the two cutters on their respective official M3 axes.
        for cutter_index, hole_center in enumerate(camera_hole_centers):
            shift = hole_center - camera_body_mount_center_robot
            camera_hole_cutters[cutter_index] = (
                camera_hole_cutters[cutter_index].translate(shift)
            )
        central_access_mesh = trimesh_cylinder_between(
            plate_back_center - camera_forward * 0.0002,
            plate_front_center + camera_forward * 0.0002,
            central_access_radius_m,
            48,
        )
        central_access_mesh.apply_transform(
            trimesh.transformations.rotation_matrix(
                math.radians(3.75),
                camera_forward,
                point=plate_center,
            )
        )
        central_access = mesh_to_manifold(central_access_mesh)
        side_hole_cutters = []
        for y_sign in (-1.0, 1.0):
            insertion_direction = -y_sign * camera_width_axis
            rail_outer_center = (
                carrier_plate_center
                + camera_width_axis
                * y_sign
                * (
                    carrier_plate_width_m / 2.0
                    + bracket_arm_width_m
                )
            )
            for up_sign in (-1.0, 1.0):
                hole_center = (
                    rail_outer_center
                    + camera_up * up_sign * side_join_vertical_offset_m
                )
                side_hole_cutters.append(
                    mesh_to_manifold(
                        trimesh_cylinder_between(
                            hole_center - insertion_direction * 0.0002,
                            hole_center
                            + insertion_direction
                            * (bracket_arm_width_m + 0.0004),
                            side_hole_diameter_m / 2.0,
                            40,
                        )
                    )
                )
        cutters = md.Manifold.batch_boolean(
            [
                *camera_hole_cutters,
                central_access,
                *side_hole_cutters,
            ],
            md.OpType.Add,
        )
        # A 0.01 mm simplification removes a float32 STL seam at the central
        # access bore without changing the 0.8 mm minimum print feature.
        return manifold_to_mesh((bracket - cutters).simplify(1.0e-5))

    def build_camera_carrier_plate(
        carrier_hole_diameter_m: float,
        side_hole_diameter_m: float,
    ) -> trimesh.Trimesh:
        parts = [
            mesh_to_manifold(
                oriented_box_mesh(
                    np.asarray(
                        [
                            plate_thickness_m,
                            carrier_plate_width_m,
                            plate_height_m,
                        ]
                    ),
                    carrier_plate_center,
                    camera_local_rotation,
                )
            )
        ]
        for carrier_hole_center in carrier_hole_centers:
            pad_offset = (
                carrier_hole_center - carrier_mount_center_robot
            )
            parts.append(
                annular_sleeve_between(
                    carrier_mount_center_robot + pad_offset,
                    carrier_plate_back_center
                    + pad_offset
                    + camera_forward * 0.00005,
                    pad_outer_radius_m,
                    carrier_hole_diameter_m / 2.0,
                    40,
                )
            )
        carrier_plate = md.Manifold.batch_boolean(parts, md.OpType.Add)
        carrier_hole_cutters = [
            mesh_to_manifold(
                trimesh_cylinder_between(
                    carrier_hole_center - camera_forward * 0.0002,
                    carrier_plate_front_center
                    + camera_forward * 0.0002,
                    carrier_hole_diameter_m / 2.0,
                    40,
                )
            )
            for carrier_hole_center in carrier_hole_centers
        ]
        carrier_central_access_mesh = trimesh_cylinder_between(
            carrier_mount_center_robot - camera_forward * 0.0002,
            carrier_plate_front_center + camera_forward * 0.0002,
            central_access_radius_m,
            48,
        )
        carrier_central_access_mesh.apply_transform(
            trimesh.transformations.rotation_matrix(
                math.radians(3.75),
                camera_forward,
                point=carrier_plate_center,
            )
        )
        carrier_central_access = mesh_to_manifold(
            carrier_central_access_mesh
        )
        side_hole_cutters = []
        side_hole_depth_m = 0.005
        for y_sign in (-1.0, 1.0):
            insertion_direction = -y_sign * camera_width_axis
            side_surface_center = (
                carrier_plate_center
                + camera_width_axis
                * y_sign
                * (carrier_plate_width_m / 2.0)
            )
            for up_sign in (-1.0, 1.0):
                hole_center = (
                    side_surface_center
                    + camera_up * up_sign * side_join_vertical_offset_m
                )
                side_hole_cutters.append(
                    mesh_to_manifold(
                        trimesh_cylinder_between(
                            hole_center - insertion_direction * 0.0002,
                            hole_center
                            + insertion_direction
                            * (side_hole_depth_m + 0.0002),
                            side_hole_diameter_m / 2.0,
                            40,
                        )
                    )
                )
        cutters = md.Manifold.batch_boolean(
            [
                *carrier_hole_cutters,
                carrier_central_access,
                *side_hole_cutters,
            ],
            md.OpType.Add,
        )
        return manifold_to_mesh(
            (carrier_plate - cutters).simplify(1.0e-5)
        )

    official_camera_hole_diameter_m = (
        float(mounting_contract["camera_screw_shaft_diameter_mm"])
        + 0.4
    ) / 1000.0
    camera_mount_bracket_mesh = build_camera_bracket(
        official_camera_hole_diameter_m,
        official_camera_hole_diameter_m,
    )
    camera_print_bracket_mesh = build_camera_bracket(
        print_clearance_hole_diameter_m,
        print_clearance_hole_diameter_m,
    )
    camera_carrier_plate_mesh = build_camera_carrier_plate(
        official_camera_hole_diameter_m,
        float(mounting_contract["camera_screw_shaft_diameter_mm"])
        / 1000.0,
    )
    camera_print_carrier_plate_mesh = build_camera_carrier_plate(
        print_clearance_hole_diameter_m,
        print_clearance_hole_diameter_m,
    )

    receiver_outer_radius_m = float(
        mounting_contract["receiver_boss_outer_diameter_mm"]
    ) / 2000.0
    receiver_depth_m = float(
        mounting_contract["receiver_boss_depth_mm"]
    ) / 1000.0
    receiver_bore_depth_m = float(
        mounting_contract["receiver_bore_depth_mm"]
    ) / 1000.0
    receiver_face_gap_m = float(
        mounting_contract["receiver_face_gap_mm"]
    ) / 1000.0
    receiver_guard_engagement_m = float(
        mounting_contract["receiver_guard_engagement_mm"]
    ) / 1000.0
    receiver_strut_width_m = float(
        mounting_contract["receiver_strut_width_mm"]
    ) / 1000.0
    receiver_strut_thickness_m = float(
        mounting_contract["receiver_strut_thickness_mm"]
    ) / 1000.0
    guard_tree = cKDTree(np.asarray(s410_mesh.vertices))
    _, guard_anchor_indices = guard_tree.query(
        np.asarray(carrier_hole_centers)
    )
    guard_surface_anchors = np.asarray(s410_mesh.vertices)[
        np.asarray(guard_anchor_indices, dtype=int)
    ]
    receiver_guard_anchors = []

    def build_camera_receiver_yoke(
        receiver_hole_diameter_m: float,
    ) -> trimesh.Trimesh:
        parts: list[md.Manifold] = []
        hole_cutters: list[md.Manifold] = []
        local_guard_anchors = []
        for hole_center, guard_surface_anchor in zip(
            carrier_hole_centers,
            guard_surface_anchors,
            strict=True,
        ):
            receiver_face = (
                hole_center - camera_forward * receiver_face_gap_m
            )
            receiver_back = (
                receiver_face - camera_forward * receiver_depth_m
            )
            anchor_direction = receiver_back - guard_surface_anchor
            anchor_direction /= np.linalg.norm(anchor_direction)
            guard_anchor = (
                guard_surface_anchor
                - anchor_direction * receiver_guard_engagement_m
            )
            local_guard_anchors.append(guard_anchor)
            parts.extend(
                [
                    mesh_to_manifold(
                        trimesh_cylinder_between(
                            receiver_back - camera_forward * 0.0002,
                            receiver_face,
                            receiver_outer_radius_m,
                            48,
                        )
                    ),
                    mesh_to_manifold(
                        rectangular_beam_between(
                            guard_anchor,
                            receiver_back,
                            camera_width_axis,
                            receiver_strut_width_m,
                            receiver_strut_thickness_m,
                        )
                    ),
                ]
            )
            hole_cutters.append(
                mesh_to_manifold(
                    trimesh_cylinder_between(
                        receiver_face + camera_forward * 0.0001,
                        receiver_face
                        - camera_forward
                        * (receiver_bore_depth_m + 0.0001),
                        receiver_hole_diameter_m / 2.0,
                        40,
                    )
                )
            )
        if not receiver_guard_anchors:
            receiver_guard_anchors.extend(local_guard_anchors)
        yoke = md.Manifold.batch_boolean(parts, md.OpType.Add)
        bores = md.Manifold.batch_boolean(hole_cutters, md.OpType.Add)
        return manifold_to_mesh((yoke - bores).simplify(1.0e-5))

    camera_receiver_yoke_mesh = build_camera_receiver_yoke(
        official_camera_hole_diameter_m
    )
    camera_print_receiver_yoke_mesh = build_camera_receiver_yoke(
        print_clearance_hole_diameter_m
    )
    camera_receiver_yoke_mesh.metadata.update(
        {
            "evidence_class": "print_adaptation",
            "receiver_count": 2,
            "receiver_axis_source": "pinned_J17A_source_model",
            "guard_anchor_source": "nearest_pinned_S410_source_vertices",
            "guard_surface_anchor_mm": (
                guard_surface_anchors * 1000.0
            ).tolist(),
            "guard_engaged_anchor_mm": (
                np.asarray(receiver_guard_anchors) * 1000.0
            ).tolist(),
        }
    )

    # The receiver yoke is visibly separate from the official S410 source
    # geometry, but the print-only upper module deliberately unions its two
    # struts into that guard so the carrier screws terminate in real material.
    sensor_cluster = md.Manifold.batch_boolean(
        [
            factory_lidar_mounts,
            factory_mount_print_webs,
            mesh_to_manifold(j20a_mesh),
            mesh_to_manifold(s410_mesh),
            mesh_to_manifold(mid360_mesh),
            mesh_to_manifold(adapter_bridge),
            sensor_connector_sleeves,
            mesh_to_manifold(camera_print_receiver_yoke_mesh),
        ],
        md.OpType.Add,
    )
    upper = md.Manifold.batch_boolean(
        [
            deck,
            sensor_cluster,
        ],
        md.OpType.Add,
    )
    upper_mesh = manifold_to_mesh(upper.simplify(1.0e-5))
    upper_components = upper_mesh.split(only_watertight=True)
    positive_upper_components = [
        component
        for component in upper_components
        if float(component.volume) > 0.0
    ]
    removed_negative_shells_mm3 = [
        abs(float(component.volume)) * 1_000_000_000.0
        for component in upper_components
        if float(component.volume) <= 0.0
    ]
    if len(positive_upper_components) != 1:
        raise ValueError(
            "Camera-receiver upper Boolean must contain one positive exterior "
            f"component, found {len(positive_upper_components)}"
        )
    upper_mesh = positive_upper_components[0].copy()
    upper_mesh.metadata["removed_negative_internal_shells_mm3"] = (
        removed_negative_shells_mm3
    )

    camera_screw_length_m = float(
        mounting_contract["camera_screw_length_mm"]
    ) / 1000.0
    camera_screw_shaft_m = float(
        mounting_contract["camera_screw_shaft_diameter_mm"]
    ) / 1000.0
    camera_screw_head_diameter_m = float(
        mounting_contract["camera_screw_head_diameter_mm"]
    ) / 1000.0
    camera_screw_head_height_m = float(
        mounting_contract["camera_screw_head_height_mm"]
    ) / 1000.0
    camera_screw_hex_flat_m = float(
        mounting_contract["camera_screw_hex_flat_mm"]
    ) / 1000.0
    camera_screw_hex_depth_m = float(
        mounting_contract["camera_screw_hex_depth_mm"]
    ) / 1000.0
    carrier_screw_length_m = float(
        mounting_contract["carrier_screw_length_mm"]
    ) / 1000.0
    side_join_screw_length_m = float(
        mounting_contract["side_join_screw_length_mm"]
    ) / 1000.0
    actual_fasteners = []
    print_fasteners = []
    print_shaft_diameter_m = float(
        camera_mount_config[
            "print_equivalent_screw_shaft_diameter_master_mm"
        ]
    ) / 1000.0
    print_head_height_m = float(
        camera_mount_config[
            "print_equivalent_screw_head_height_master_mm"
        ]
    ) / 1000.0
    for hole_center in camera_hole_centers:
        under_head_center = (
            hole_center
            - camera_forward
            * (mating_clearance_m + plate_thickness_m)
        )
        actual_fasteners.append(
            socket_head_screw_mesh(
                under_head_center,
                camera_forward,
                camera_screw_length_m,
                camera_screw_shaft_m,
                camera_screw_head_diameter_m,
                camera_screw_head_height_m,
                camera_screw_hex_flat_m,
                camera_screw_hex_depth_m,
            )
        )
        print_fasteners.append(
            socket_head_screw_mesh(
                under_head_center,
                camera_forward,
                camera_screw_length_m,
                print_shaft_diameter_m,
                camera_screw_head_diameter_m,
                print_head_height_m,
                camera_screw_hex_flat_m,
                0.0,
            )
        )
    for carrier_hole_center in carrier_hole_centers:
        under_head_center = (
            carrier_hole_center
            + camera_forward
            * (mating_clearance_m + plate_thickness_m)
        )
        actual_fasteners.append(
            socket_head_screw_mesh(
                under_head_center,
                -camera_forward,
                carrier_screw_length_m,
                camera_screw_shaft_m,
                camera_screw_head_diameter_m,
                camera_screw_head_height_m,
                camera_screw_hex_flat_m,
                camera_screw_hex_depth_m,
            )
        )
        print_fasteners.append(
            socket_head_screw_mesh(
                under_head_center,
                -camera_forward,
                carrier_screw_length_m,
                print_shaft_diameter_m,
                camera_screw_head_diameter_m,
                print_head_height_m,
                camera_screw_hex_flat_m,
                0.0,
            )
        )
    for y_sign in (-1.0, 1.0):
        insertion_direction = -y_sign * camera_width_axis
        rail_outer_center = (
            carrier_plate_center
            + camera_width_axis
            * y_sign
            * (carrier_plate_width_m / 2.0 + bracket_arm_width_m)
        )
        for up_sign in (-1.0, 1.0):
            under_head_center = (
                rail_outer_center
                + camera_up * up_sign * side_join_vertical_offset_m
            )
            actual_fasteners.append(
                socket_head_screw_mesh(
                    under_head_center,
                    insertion_direction,
                    side_join_screw_length_m,
                    camera_screw_shaft_m,
                    camera_screw_head_diameter_m,
                    camera_screw_head_height_m,
                    camera_screw_hex_flat_m,
                    camera_screw_hex_depth_m,
                )
            )
            print_fasteners.append(
                socket_head_screw_mesh(
                    under_head_center,
                    insertion_direction,
                    side_join_screw_length_m,
                    print_shaft_diameter_m,
                    camera_screw_head_diameter_m,
                    print_head_height_m,
                    camera_screw_hex_flat_m,
                    0.0,
                )
            )
    camera_fasteners_mesh = trimesh.util.concatenate(actual_fasteners)
    camera_print_fasteners_mesh = trimesh.util.concatenate(print_fasteners)
    camera_fasteners_mesh.metadata.update(
        {
            "camera_fastener_count": 2,
            "carrier_fastener_count": 2,
            "side_join_fastener_count": 4,
            "camera_screw": mounting_contract["camera_screw"],
            "carrier_screw": mounting_contract["carrier_screw"],
            "side_join_screw": mounting_contract["side_join_screw"],
        }
    )

    interface_center = np.asarray(
        value("factory_interface_box_center"),
        dtype=float,
    )
    interface_size = np.asarray(
        value("factory_interface_box_envelope"),
        dtype=float,
    )
    interface_radius = float(value("factory_interface_box_corner_radius"))
    interface_shell = rounded_box_xy_mm(
        interface_size,
        interface_center,
        interface_radius,
    )
    foot_height = float(value("factory_interface_box_mount_foot_height"))
    foot_pattern = np.asarray(
        value("factory_interface_box_mount_pattern"),
        dtype=float,
    )
    foot_parts = []
    foot_holes = []
    interface_bottom_z = interface_center[2] - interface_size[2] / 2.0
    for x_sign in (-1.0, 1.0):
        for y_sign in (-1.0, 1.0):
            foot_center = np.asarray(
                [
                    interface_center[0] + x_sign * foot_pattern[0] / 2.0,
                    interface_center[1] + y_sign * foot_pattern[1] / 2.0,
                    interface_bottom_z - foot_height / 2.0 + 0.2,
                ]
            )
            foot_parts.append(
                md.Manifold.cylinder(
                    foot_height / 1000.0,
                    6.0 / 1000.0,
                    6.0 / 1000.0,
                    40,
                    center=True,
                ).translate(foot_center / 1000.0)
            )
            foot_holes.append(
                md.Manifold.cylinder(
                    (foot_height + 4.0) / 1000.0,
                    float(value("factory_interface_box_mount_hole_diameter"))
                    / 2000.0,
                    float(value("factory_interface_box_mount_hole_diameter"))
                    / 2000.0,
                    32,
                    center=True,
                ).translate(foot_center / 1000.0)
            )
    interface_shell = md.Manifold.batch_boolean(
        [interface_shell, *foot_parts],
        md.OpType.Add,
    )

    port_face_y = float(value("factory_interface_box_port_face_y"))
    recess_depth = float(
        value("factory_interface_box_panel_recess_depth")
    )
    port_z = interface_center[2] - 5.0
    # Official manual groups: 24V, 12V, 5V, Power, Ethernet, USB3.0, HDMI.
    port_specs = (
        (-68.0, 10.0, 12.0),
        (-51.0, 10.0, 12.0),
        (-34.0, 10.0, 12.0),
        (-14.0, 13.0, 14.0),
        (19.0, 17.0, 15.0),
        (44.0, 10.0, 16.0),
        (63.0, 10.0, 17.0),
    )
    port_cuts = []
    connector_inserts = []
    for x_offset, width, height in port_specs:
        port_center = np.asarray(
            [
                interface_center[0] + x_offset,
                port_face_y,
                port_z,
            ]
        )
        port_cuts.append(
            manifold_box(
                np.asarray([width, recess_depth + 2.0, height]) / 1000.0,
                port_center / 1000.0,
            )
        )
        connector_center = port_center.copy()
        connector_center[1] += 0.7
        connector_inserts.append(
            manifold_box(
                np.asarray(
                    [max(3.0, width - 2.0), 0.8, max(3.0, height - 2.0)]
                )
                / 1000.0,
                connector_center / 1000.0,
            )
        )
    interface_shell = interface_shell - md.Manifold.batch_boolean(
        [*port_cuts, *foot_holes],
        md.OpType.Add,
    )

    vent_inserts = []
    vent_face_y = interface_center[1] + interface_size[1] / 2.0
    for x_offset in np.linspace(-58.0, 58.0, 8):
        vent_inserts.append(
            manifold_box(
                np.asarray([10.0, 0.8, 2.2]) / 1000.0,
                np.asarray(
                    [
                        interface_center[0] + x_offset,
                        vent_face_y - 0.4,
                        interface_center[2] + 6.0,
                    ]
                )
                / 1000.0,
            )
        )
    interface_mesh = manifold_to_mesh(interface_shell.simplify(1.0e-7))
    interface_connectors_mesh = manifold_to_mesh(
        md.Manifold.batch_boolean(
            connector_inserts,
            md.OpType.Add,
        ).simplify(1.0e-7)
    )
    interface_vents_mesh = manifold_to_mesh(
        md.Manifold.batch_boolean(
            vent_inserts,
            md.OpType.Add,
        ).simplify(1.0e-7)
    )
    deck_mesh = manifold_to_mesh(deck.simplify(1.0e-7))
    return {
        "UPPER_LIDAR_MODULE": upper_mesh,
        "UPPER_DECK_INTERFACE": manifold_to_mesh(
            deck
        ),
        "MID360_SENSOR": mid360_mesh,
        "MID360_OPTICAL_WINDOW": mid360_optical_window,
        "MID360_BODY": mid360_body,
        "MID360_HOUSING_EXTERIOR": mid360_housing_exterior,
        "MID360_CONNECTOR": mid360_connector,
        "J17A_SENSOR_CARRIER": j17a_mesh,
        "FACTORY_LIDAR_MOUNTS": factory_lidar_mounts_mesh,
        "MID360_ADAPTER": j20a_mesh,
        "MID360_GUARD": s410_mesh,
        "MID360_MOUNT_BRIDGE": adapter_bridge,
        "J17A_BASE_SPACERS": manifold_to_mesh(
            j17a_base_spacer_union.simplify(1.0e-7)
        ),
        "SENSOR_PRINT_CONNECTORS": manifold_to_mesh(
            sensor_connector_sleeves.simplify(1.0e-7)
        ),
        "PAYLOAD_BASE": deck_mesh,
        "FACTORY_INTERFACE": interface_mesh,
        "FACTORY_INTERFACE_CONNECTORS": interface_connectors_mesh,
        "FACTORY_INTERFACE_VENTS": interface_vents_mesh,
        "D435I_CAMERA": camera_visual_mesh,
        "FRONT_CAMERA_BAR": camera_print_mesh,
        "CAMERA_MOUNT_BRACKET": camera_mount_bracket_mesh,
        "CAMERA_PRINT_BRACKET": camera_print_bracket_mesh,
        "CAMERA_CARRIER_PLATE": camera_carrier_plate_mesh,
        "CAMERA_PRINT_CARRIER_PLATE": camera_print_carrier_plate_mesh,
        "CAMERA_RECEIVER_YOKE": camera_receiver_yoke_mesh,
        "CAMERA_PRINT_RECEIVER_YOKE": camera_print_receiver_yoke_mesh,
        "CAMERA_FASTENERS": camera_fasteners_mesh,
        "CAMERA_PRINT_FASTENERS": camera_print_fasteners_mesh,
    }


def transform_mesh(
    mesh: trimesh.Trimesh,
    matrix: np.ndarray,
) -> trimesh.Trimesh:
    result = mesh.copy()
    result.apply_transform(matrix)
    if np.linalg.det(matrix[:3, :3]) < 0:
        result.faces = np.asarray(result.faces)[:, ::-1]
    if result.is_watertight and result.volume < 0:
        result.faces = np.asarray(result.faces)[:, ::-1]
    result.remove_unreferenced_vertices()
    return result


def intersection_volume_mm3(
    first: trimesh.Trimesh,
    second: trimesh.Trimesh,
) -> float:
    intersection = mesh_to_manifold(first) ^ mesh_to_manifold(second)
    return float(intersection.volume() * 1_000_000_000.0)


def vertex_sampled_clearance_mm(
    first: trimesh.Trimesh,
    second: trimesh.Trimesh,
    maximum_samples: int = 8000,
) -> dict[str, float | int | str]:
    def sampled_vertices(mesh: trimesh.Trimesh) -> np.ndarray:
        count = min(maximum_samples, len(mesh.vertices))
        if count == len(mesh.vertices):
            return np.asarray(mesh.vertices)
        indices = np.linspace(
            0,
            len(mesh.vertices) - 1,
            count,
            dtype=int,
        )
        return np.asarray(mesh.vertices)[indices]

    first_points = sampled_vertices(first)
    second_points = sampled_vertices(second)
    _, first_distances, _ = trimesh.proximity.closest_point(
        second,
        first_points,
    )
    _, second_distances, _ = trimesh.proximity.closest_point(
        first,
        second_points,
    )
    distances_mm = np.concatenate(
        [first_distances, second_distances]
    ) * 1000.0
    return {
        "method": "bidirectional_deterministic_vertex_sample",
        "sample_count": int(len(distances_mm)),
        "minimum_mm": float(np.min(distances_mm)),
        "p01_mm": float(np.quantile(distances_mm, 0.01)),
    }


def shifted_mesh(
    mesh: trimesh.Trimesh,
    translation: np.ndarray,
) -> trimesh.Trimesh:
    result = mesh.copy()
    result.apply_translation(translation)
    return result


def color_mesh(mesh: trimesh.Trimesh, color: list[int]) -> trimesh.Trimesh:
    result = mesh.copy()
    result.visual.face_colors = np.tile(
        np.asarray(color, dtype=np.uint8),
        (len(result.faces), 1),
    )
    return result


def export_scene(
    meshes: dict[str, trimesh.Trimesh],
    path: Path,
    millimetres: bool,
) -> None:
    scene = trimesh.Scene()
    for name, mesh in meshes.items():
        output = mesh.copy()
        if millimetres:
            output.apply_scale(1000.0)
        family = next(
            (
                candidate
                for candidate in (
                    "UPPER_DECK_INTERFACE",
                    "UPPER_LIDAR_MODULE",
                    "MID360_SENSOR",
                    "MID360_OPTICAL_WINDOW",
                    "MID360_BODY",
                    "MID360_HOUSING_EXTERIOR",
                    "MID360_CONNECTOR",
                    "J17A_SENSOR_CARRIER",
                    "FACTORY_LIDAR_MOUNTS",
                    "MID360_ADAPTER",
                    "MID360_GUARD",
                    "FACTORY_INTERFACE_CONNECTORS",
                    "FACTORY_INTERFACE_VENTS",
                    "FACTORY_INTERFACE",
                    "D435I_CAMERA",
                    "CAMERA_MOUNT_BRACKET",
                    "CAMERA_CARRIER_PLATE",
                    "CAMERA_FASTENERS",
                    "FRONT_CAMERA_BAR",
                )
                if name.startswith(candidate)
            ),
            "TORSO" if name == "TORSO" else name.split("_")[-1],
        )
        output = color_mesh(output, COLORS.get(family, [180, 180, 180, 255]))
        scene.add_geometry(output, node_name=name, geom_name=name)
    scene.export(path)


def mesh_metrics_mm(mesh: trimesh.Trimesh) -> dict[str, Any]:
    edges = mesh.edges_sorted
    _, counts = np.unique(edges, axis=0, return_counts=True)
    manifold = mesh_to_manifold(mesh)
    return {
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "components": int(len(mesh.split(only_watertight=True))),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "boundary_edges": int(np.count_nonzero(counts == 1)),
        "nonmanifold_edges": int(np.count_nonzero(counts > 2)),
        "degenerate_faces": int(np.count_nonzero(mesh.area_faces <= 1.0e-10)),
        "volume_mm3": float(abs(mesh.volume)),
        "bbox_min_mm": mesh.bounds[0].tolist(),
        "bbox_max_mm": mesh.bounds[1].tolist(),
        "bbox_size_mm": (mesh.bounds[1] - mesh.bounds[0]).tolist(),
        "manifold_status": str(manifold.status()),
    }


def cut_joint_holes(
    mesh_mm: trimesh.Trimesh,
    cutters: list[trimesh.Trimesh],
) -> trimesh.Trimesh:
    if not cutters:
        return mesh_mm.copy()
    base = mesh_to_manifold(mesh_mm)
    cutter = md.Manifold.batch_boolean(
        [mesh_to_manifold(item) for item in cutters],
        md.OpType.Add,
    )
    # The boolean can leave distinct vertices closer than binary STL's
    # float32 precision after print orientation. A 0.1-micrometre manifold
    # simplification removes those numerical slivers without changing the
    # declared 0.8 mm minimum printable feature.
    return manifold_to_mesh((base - cutter).simplify(1.0e-4))


def union_print_meshes(
    base: trimesh.Trimesh,
    additions: list[trimesh.Trimesh],
) -> trimesh.Trimesh:
    if not additions:
        return base.copy()
    union = md.Manifold.batch_boolean(
        [mesh_to_manifold(base)]
        + [mesh_to_manifold(item) for item in additions],
        md.OpType.Add,
    )
    return manifold_to_mesh(union.simplify(1.0e-4))


def orient_for_print(mesh_mm: trimesh.Trimesh) -> trimesh.Trimesh:
    transform, _ = trimesh.bounds.oriented_bounds(mesh_mm, angle_digits=1)
    result = transform_mesh(mesh_mm, transform)
    extents = result.extents
    smallest = int(np.argmin(extents))
    if smallest == 0:
        result.apply_transform(
            trimesh.transformations.rotation_matrix(math.pi / 2.0, [0, 1, 0])
        )
    elif smallest == 1:
        result.apply_transform(
            trimesh.transformations.rotation_matrix(math.pi / 2.0, [1, 0, 0])
        )
    result.apply_translation(
        [
            -(result.bounds[0, 0] + result.bounds[1, 0]) / 2.0,
            -(result.bounds[0, 1] + result.bounds[1, 1]) / 2.0,
            -result.bounds[0, 2],
        ]
    )
    result.remove_unreferenced_vertices()
    return result


def arrange_layout(
    parts: dict[str, trimesh.Trimesh],
    bed_width_mm: float,
) -> dict[str, trimesh.Trimesh]:
    arranged: dict[str, trimesh.Trimesh] = {}
    cursor_x = 5.0
    cursor_y = 5.0
    row_depth = 0.0
    gap = 6.0
    for name, mesh in sorted(parts.items()):
        size = mesh.extents
        if cursor_x + size[0] + 5.0 > bed_width_mm:
            cursor_x = 5.0
            cursor_y += row_depth + gap
            row_depth = 0.0
        translated = mesh.copy()
        translated.apply_translation(
            [
                cursor_x - translated.bounds[0, 0],
                cursor_y - translated.bounds[0, 1],
                -translated.bounds[0, 2],
            ]
        )
        arranged[name] = translated
        cursor_x += size[0] + gap
        row_depth = max(row_depth, float(size[1]))
    return arranged


def write_stl(path: Path, mesh_mm: trimesh.Trimesh) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mesh_mm.export(path, file_type="stl")
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"Failed to write {path}")


def build_official_sensor_masters(
    config: dict[str, Any],
    sources: dict[str, Path],
) -> tuple[
    dict[str, trimesh.Trimesh],
    dict[str, Any],
    dict[str, Any],
]:
    raw_mid360 = tessellated_step_mesh(sources["mid360_tessellated_mesh"])
    raw_mid360_optical_window = tessellated_step_mesh(
        sources["mid360_optical_window_mesh"]
    )
    raw_mid360_body = tessellated_step_mesh(
        sources["mid360_body_mesh"]
    )
    raw_mid360_housing_exterior = tessellated_step_mesh(
        sources["mid360_housing_exterior_mesh"]
    )
    raw_mid360_connector = tessellated_step_mesh(
        sources["mid360_connector_mesh"]
    )
    raw_j20a = tessellated_step_mesh(sources["j20a_tessellated_mesh"])
    raw_j17a = tessellated_step_mesh(sources["j17a_tessellated_mesh"])
    raw_s410 = tessellated_step_mesh(sources["s410_tessellated_mesh"])
    raw_jetson_module = tessellated_step_mesh(
        sources["jetson_agx_orin_module_tessellated_mesh"]
    )
    raw_agx_orin_base = tessellated_step_mesh(
        sources["agx_orin_base_tessellated_mesh"]
    )
    raw_d435i_visual = source_mesh(sources["d435i_ros_mesh"])
    expected_d435i_bbox_mm = np.asarray(
        config["lidar_module"]["parameters_mm"][
            "d435i_ros_source_bbox"
        ]["value"],
        dtype=float,
    )
    actual_d435i_bbox_mm = raw_d435i_visual.extents * 1000.0
    if not np.allclose(
        actual_d435i_bbox_mm,
        expected_d435i_bbox_mm,
        atol=1.0e-6,
        rtol=0.0,
    ):
        raise ValueError(
            "Official D435i ROS mesh extent changed: "
            f"expected {expected_d435i_bbox_mm.tolist()}, "
            f"got {actual_d435i_bbox_mm.tolist()}"
        )
    for name, mesh in (
        ("j17a", raw_j17a),
        ("j20a", raw_j20a),
        ("s410", raw_s410),
    ):
        # FreeCAD's J17A STL writes one vertex triplet per face. Trimesh's
        # validate pass deletes eight zero-area tessellation triangles and
        # opens the otherwise closed source solid, so preserve its exact face
        # set and weld only identical vertices.
        mesh.process(validate=name != "j17a")
        mesh.merge_vertices()
        mesh.remove_unreferenced_vertices()
        if not mesh.is_watertight or not mesh.is_winding_consistent:
            raise ValueError(f"Official {name} STEP tessellation is not closed")
        mesh_to_manifold(mesh)
    raw_jetson_module.process(validate=False)
    raw_jetson_module.merge_vertices()
    raw_jetson_module.remove_unreferenced_vertices()
    raw_agx_orin_base.process(validate=True)
    raw_agx_orin_base.merge_vertices()
    raw_agx_orin_base.remove_unreferenced_vertices()
    if (
        not raw_agx_orin_base.is_watertight
        or not raw_agx_orin_base.is_winding_consistent
    ):
        raise ValueError("Official AGX Orin base STEP tessellation is not closed")
    mesh_to_manifold(raw_agx_orin_base)

    settings = config["official_sensor_reconstruction"]
    master_path = MASTER_DIR / "mid360_sensor_master_1_1.stl"
    diagnostic_reuse = (
        os.environ.get("LITE3_PRINT_REUSE_MASTERS") == "1"
        and master_path.is_file()
    )
    if diagnostic_reuse:
        mid360 = trimesh.load_mesh(master_path, process=True, validate=True)
        mid360.apply_scale(0.001)
        mid360.remove_unreferenced_vertices()
        mid360_report = {
            "diagnostic_reuse": True,
            "voxel_pitch_mm": float(settings["mid360_voxel_pitch_mm"]),
            "vertices": int(len(mid360.vertices)),
            "faces": int(len(mid360.faces)),
            "watertight": bool(mid360.is_watertight),
            "winding_consistent": bool(mid360.is_winding_consistent),
            "connected_components": len(
                mid360.split(only_watertight=True)
            ),
            "volume_mm3": float(mid360.volume * 1_000_000_000.0),
            "bbox_size_mm": (
                (mid360.bounds[1] - mid360.bounds[0]) * 1000.0
            ).tolist(),
            "source_to_master_surface_distance": {"p99_mm": -1.0},
            "master_to_source_surface_distance": {"p99_mm": -1.0},
        }
    else:
        mid360, mid360_report = reconstruct_master(
            "mid360",
            raw_mid360,
            {
                "voxel_pitch_mm": float(
                    settings["mid360_voxel_pitch_mm"]
                ),
                "minimum_component_volume_mm3": float(
                    settings["mid360_minimum_component_volume_mm3"]
                ),
                "bridge_boxes_mm": [],
            },
            {"enabled": False},
            int(settings["surface_sample_count"]),
        )

    d435i_master_path = MASTER_DIR / "d435i_sensor_master_1_1.stl"
    d435i_diagnostic_reuse = (
        os.environ.get("LITE3_PRINT_REUSE_D435_MASTER") == "1"
        and d435i_master_path.is_file()
    )
    if d435i_diagnostic_reuse:
        d435i = trimesh.load_mesh(
            d435i_master_path,
            process=True,
            validate=True,
        )
        d435i.apply_scale(0.001)
        d435i.remove_unreferenced_vertices()
        d435i_report = {
            "diagnostic_reuse": True,
            "voxel_pitch_mm": float(settings["d435i_voxel_pitch_mm"]),
            "vertices": int(len(d435i.vertices)),
            "faces": int(len(d435i.faces)),
            "watertight": bool(d435i.is_watertight),
            "winding_consistent": bool(d435i.is_winding_consistent),
            "connected_components": len(
                d435i.split(only_watertight=True)
            ),
            "volume_mm3": float(d435i.volume * 1_000_000_000.0),
            "bbox_size_mm": (
                (d435i.bounds[1] - d435i.bounds[0]) * 1000.0
            ).tolist(),
            "source_to_master_surface_distance": {"p99_mm": -1.0},
            "master_to_source_surface_distance": {"p99_mm": -1.0},
        }
    else:
        d435i, d435i_report = reconstruct_master(
            "d435i",
            raw_d435i_visual,
            {
                "voxel_pitch_mm": float(
                    settings["d435i_voxel_pitch_mm"]
                ),
                "minimum_component_volume_mm3": float(
                    settings["d435i_minimum_component_volume_mm3"]
                ),
                "bridge_boxes_mm": [],
            },
            {"enabled": False},
            int(settings["d435i_surface_sample_count"]),
        )

    masters = {
        "mid360": mid360,
        "mid360_optical_window": raw_mid360_optical_window,
        "mid360_body": raw_mid360_body,
        "mid360_housing_exterior": raw_mid360_housing_exterior,
        "mid360_connector": raw_mid360_connector,
        "j17a": raw_j17a,
        "j20a": raw_j20a,
        "s410": raw_s410,
        "jetson_agx_orin_module": raw_jetson_module,
        "agx_orin_base": raw_agx_orin_base,
        "d435i": d435i,
        "d435i_visual": raw_d435i_visual,
    }
    filenames = {
        "mid360": "mid360_sensor_master_1_1.stl",
        "d435i": "d435i_sensor_master_1_1.stl",
        "j17a": "j17a_sensor_carrier_master_1_1.stl",
        "j20a": "j20a_adapter_master_1_1.stl",
        "s410": "s410_guard_master_1_1.stl",
    }
    for name, filename in filenames.items():
        mesh = masters[name]
        output = mesh.copy()
        output.apply_scale(1000.0)
        write_stl(MASTER_DIR / filename, output)

    source_report = {
        "mid360_full_step_tessellation": topology_metrics(raw_mid360),
        "mid360_optical_window_step_tessellation": topology_metrics(
            raw_mid360_optical_window
        ),
        "mid360_body_step_tessellation": topology_metrics(raw_mid360_body),
        "mid360_housing_exterior_step_tessellation": topology_metrics(
            raw_mid360_housing_exterior
        ),
        "mid360_connector_step_tessellation": topology_metrics(
            raw_mid360_connector
        ),
        "j17a_step_tessellation": topology_metrics(raw_j17a),
        "j20a_step_tessellation": topology_metrics(raw_j20a),
        "s410_step_tessellation": topology_metrics(raw_s410),
        "jetson_agx_orin_module_step_tessellation": topology_metrics(
            raw_jetson_module
        ),
        "agx_orin_base_step_tessellation": topology_metrics(
            raw_agx_orin_base
        ),
        "d435i_ros_visual_mesh": topology_metrics(raw_d435i_visual),
    }
    master_report = {
        "mid360": mid360_report,
        "d435i": d435i_report,
        "mid360_optical_window": topology_metrics(
            raw_mid360_optical_window
        ),
        "mid360_body": topology_metrics(raw_mid360_body),
        "mid360_housing_exterior": topology_metrics(
            raw_mid360_housing_exterior
        ),
        "mid360_connector": topology_metrics(raw_mid360_connector),
        "j17a": topology_metrics(raw_j17a),
        "j20a": topology_metrics(raw_j20a),
        "s410": topology_metrics(raw_s410),
        "jetson_agx_orin_module": topology_metrics(raw_jetson_module),
        "agx_orin_base": topology_metrics(raw_agx_orin_base),
    }
    print(
        "master=mid360 "
        f"faces={len(mid360.faces)} "
        "master_to_source_p99_mm="
        f"{mid360_report['master_to_source_surface_distance']['p99_mm']:.4f}",
        flush=True,
    )
    print(
        "master=d435i "
        f"faces={len(d435i.faces)} "
        "master_to_source_p99_mm="
        f"{d435i_report['master_to_source_surface_distance']['p99_mm']:.4f}",
        flush=True,
    )
    return masters, source_report, master_report


def main() -> int:
    config = load_parameters()
    repo_root = find_repo_root(ROOT)
    sources = resolve_sources(config, repo_root)
    for directory in (MASTER_DIR, PRINT_DIR, REFERENCE_DIR, REPORT_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    component_settings = config["master_reconstruction"]["components"]
    smoothing_settings = config["master_reconstruction"]["smoothing"]
    sample_count = int(config["master_reconstruction"]["surface_sample_count"])
    raw_components: dict[str, trimesh.Trimesh] = {}
    masters: dict[str, trimesh.Trimesh] = {}
    source_report: dict[str, Any] = {}
    master_report: dict[str, Any] = {}
    for component_name, source_key in COMPONENT_FILES.items():
        raw = source_mesh(sources[source_key])
        raw_components[component_name] = raw
        source_report[component_name] = topology_metrics(raw)
        master_path = MASTER_DIR / f"{component_name}_master_1_1.stl"
        diagnostic_reuse = (
            os.environ.get("LITE3_PRINT_REUSE_MASTERS") == "1"
            and master_path.is_file()
        )
        if diagnostic_reuse:
            master = trimesh.load_mesh(master_path, process=True, validate=True)
            master.apply_scale(0.001)
            master.remove_unreferenced_vertices()
            metrics = {
                "diagnostic_reuse": True,
                "vertices": int(len(master.vertices)),
                "faces": int(len(master.faces)),
                "watertight": bool(master.is_watertight),
                "winding_consistent": bool(master.is_winding_consistent),
                "connected_components": len(
                    master.split(only_watertight=True)
                ),
                "volume_mm3": float(master.volume * 1_000_000_000.0),
                "bbox_size_mm": (
                    (master.bounds[1] - master.bounds[0]) * 1000.0
                ).tolist(),
                "source_to_master_surface_distance": {"p99_mm": -1.0},
                "master_to_source_surface_distance": {"p99_mm": -1.0},
            }
        else:
            master, metrics = reconstruct_master(
                component_name,
                raw,
                component_settings[component_name],
                smoothing_settings,
                sample_count,
            )
        masters[component_name] = master
        master_report[component_name] = metrics
        master_mm = master.copy()
        master_mm.apply_scale(1000.0)
        write_stl(master_path, master_mm)
        print(
            f"master={component_name} faces={len(master.faces)} "
            "master_to_source_p99_mm="
            f"{metrics['master_to_source_surface_distance']['p99_mm']:.4f}",
            flush=True,
        )

    sensor_masters, sensor_source_report, sensor_master_report = (
        build_official_sensor_masters(config, sources)
    )
    source_report.update(sensor_source_report)
    master_report.update(sensor_master_report)

    pose = config["factory_standing_pose"]
    robot, transforms, joints = resolve_urdf_transforms(
        sources["urdf"],
        float(pose["hip_y_rad"]["value"]),
        float(pose["knee_rad"]["value"]),
        float(pose["foot_collision_radius_mm"]["value"]) / 1000.0,
    )
    world_links = build_world_links(robot, transforms, masters)
    visual_world_links = build_world_links(robot, transforms, raw_components)
    base_min_z = min(mesh.bounds[0, 2] for mesh in world_links.values())
    visual_base_min_z = min(
        mesh.bounds[0, 2] for mesh in visual_world_links.values()
    )
    base_shift = np.asarray([0.0, 0.0, -base_min_z])
    visual_base_shift = np.asarray([0.0, 0.0, -visual_base_min_z])
    world_links = {
        name: shifted_mesh(mesh, base_shift) for name, mesh in world_links.items()
    }
    visual_world_links = {
        name: shifted_mesh(mesh, visual_base_shift)
        for name, mesh in visual_world_links.items()
    }
    for joint in joints.values():
        joint["center_m"] = np.asarray(joint["center_m"]) + base_shift

    lidar_meshes = build_lidar_geometry(config, sensor_masters)
    lidar_parameters = config["lidar_module"]["parameters_mm"]
    bridge_size = np.asarray(
        lidar_parameters["mid360_adapter_bridge_size"]["value"],
        dtype=float,
    )
    hole_pattern = np.asarray(
        lidar_parameters["mid360_mount_hole_pattern"]["value"],
        dtype=float,
    )
    hole_radius = (
        float(
            lidar_parameters["j20a_mid360_hole_diameter"]["value"]
        )
        / 2.0
    )
    bridge_hole_edge_clearance = (
        hole_pattern / 2.0
        - hole_radius
        - bridge_size[[0, 2]] / 2.0
    )
    native_fov = np.asarray(
        lidar_parameters["mid360_vertical_fov_deg"]["value"],
        dtype=float,
    )
    lidar_tilt_deg = float(lidar_parameters["j20a_tilt_deg"]["value"])
    deck_center_audit = np.asarray(
        lidar_parameters["deck_center"]["value"],
        dtype=float,
    )
    jetson_center_audit = np.asarray(
        lidar_parameters["jetson_agx_orin_center"]["value"],
        dtype=float,
    )
    jetson_size_audit = np.asarray(
        lidar_parameters["jetson_agx_orin_envelope"]["value"],
        dtype=float,
    )
    rail_size_audit = np.asarray(
        lidar_parameters["base_side_rail_size"]["value"],
        dtype=float,
    )
    rail_center_y_audit = float(
        lidar_parameters["base_side_rail_center_y"]["value"]
    )
    crossbar_x_audit = np.asarray(
        lidar_parameters["base_sensor_crossbar_x"]["value"],
        dtype=float,
    )
    crossbar_size_audit = np.asarray(
        lidar_parameters["base_sensor_crossbar_size"]["value"],
        dtype=float,
    )
    compute_crossbar_size_audit = np.asarray(
        lidar_parameters["agx_orin_compute_crossbar_size"]["value"],
        dtype=float,
    )
    agx_mount_centers_source_audit = np.asarray(
        lidar_parameters["agx_orin_base_deck_mount_centers_source"]["value"],
        dtype=float,
    )
    agx_mount_diameters_audit = np.asarray(
        lidar_parameters["agx_orin_base_deck_mount_diameters"]["value"],
        dtype=float,
    )
    agx_device_mount_centers_source_audit = np.asarray(
        lidar_parameters[
            "agx_orin_base_device_mount_centers_source"
        ]["value"],
        dtype=float,
    )
    agx_device_mount_diameter_audit = float(
        lidar_parameters["agx_orin_base_device_mount_diameter"]["value"]
    )
    agx_base_rotation_audit = np.asarray(
        [
            [1.0, 0.0, 0.0],
            [0.0, 0.0, -1.0],
            [0.0, 1.0, 0.0],
        ]
    )
    agx_base_to_robot_audit = transform_from_rotation_translation_mm(
        agx_base_rotation_audit,
        lidar_parameters["agx_orin_base_translation"]["value"],
    )
    agx_mount_centers_robot_audit = np.asarray(
        [
            (
                agx_base_to_robot_audit
                @ np.append(center_source / 1000.0, 1.0)
            )[:3]
            * 1000.0
            for center_source in agx_mount_centers_source_audit
        ]
    )
    agx_device_mount_centers_robot_audit = np.asarray(
        [
            (
                agx_base_to_robot_audit
                @ np.append(center_source / 1000.0, 1.0)
            )[:3]
            * 1000.0
            for center_source in agx_device_mount_centers_source_audit
        ]
    )
    payload_pattern_audit = np.asarray(
        lidar_parameters["lite3_payload_hole_pattern"]["value"],
        dtype=float,
    )
    payload_hole_diameter_audit = float(
        lidar_parameters["lite3_payload_hole_diameter"]["value"]
    )
    j17a_pattern_audit = np.asarray(
        lidar_parameters["j17a_mount_hole_pattern"]["value"],
        dtype=float,
    )
    j17a_hole_diameter_audit = float(
        lidar_parameters["j17a_mount_hole_diameter"]["value"]
    )
    payload_hole_probes = []
    for x_sign in (-1.0, 1.0):
        for y_sign in (-1.0, 1.0):
            probe = trimesh.creation.cylinder(
                radius=payload_hole_diameter_audit / 2000.0,
                height=0.010,
                sections=32,
            )
            probe.apply_translation(
                np.asarray(
                    [
                        deck_center_audit[0]
                        + x_sign * payload_pattern_audit[0] / 2.0,
                        deck_center_audit[1]
                        + y_sign * payload_pattern_audit[1] / 2.0,
                        deck_center_audit[2],
                    ]
                )
                / 1000.0
            )
            payload_hole_probes.append(probe)
    payload_hole_probe = trimesh.util.concatenate(payload_hole_probes)
    payload_hole_centers = np.asarray(
        [
            [
                deck_center_audit[0]
                + x_sign * payload_pattern_audit[0] / 2.0,
                deck_center_audit[1]
                + y_sign * payload_pattern_audit[1] / 2.0,
            ]
            for x_sign in (-1.0, 1.0)
            for y_sign in (-1.0, 1.0)
        ],
        dtype=float,
    )
    j17a_hole_probes = []
    for x in crossbar_x_audit:
        for y_sign in (-1.0, 1.0):
            probe = trimesh.creation.cylinder(
                radius=j17a_hole_diameter_audit / 2000.0,
                height=0.010,
                sections=32,
            )
            probe.apply_translation(
                np.asarray(
                    [
                        x,
                        y_sign * j17a_pattern_audit[1] / 2.0,
                        deck_center_audit[2],
                    ]
                )
                / 1000.0
            )
            j17a_hole_probes.append(probe)
    j17a_hole_probe = trimesh.util.concatenate(j17a_hole_probes)
    agx_base_hole_probes = []
    for center, diameter in zip(
        agx_mount_centers_robot_audit,
        agx_mount_diameters_audit,
        strict=True,
    ):
        probe = trimesh.creation.cylinder(
            radius=float(diameter) / 2000.0,
            height=0.010,
            sections=40,
        )
        probe.apply_translation(
            np.asarray(
                [
                    center[0],
                    center[1],
                    deck_center_audit[2],
                ]
            )
            / 1000.0
        )
        agx_base_hole_probes.append(probe)
    agx_base_hole_probe = trimesh.util.concatenate(agx_base_hole_probes)
    jetson_blind_mount_depth_audit = float(
        lidar_parameters["jetson_agx_orin_blind_mount_depth"]["value"]
    )
    jetson_blind_mount_diameter_audit = float(
        lidar_parameters["jetson_agx_orin_blind_mount_diameter"]["value"]
    )
    jetson_bottom_z_audit = (
        jetson_center_audit[2] - jetson_size_audit[2] / 2.0
    )
    jetson_mount_hole_probes = []
    for center in agx_device_mount_centers_robot_audit:
        probe = trimesh.creation.cylinder(
            radius=agx_device_mount_diameter_audit / 2000.0,
            height=jetson_blind_mount_depth_audit / 1000.0,
            sections=40,
        )
        probe.apply_translation(
            np.asarray(
                [
                    center[0],
                    center[1],
                    jetson_bottom_z_audit
                    + jetson_blind_mount_depth_audit / 2.0,
                ]
            )
            / 1000.0
        )
        jetson_mount_hole_probes.append(probe)
    jetson_mount_hole_probe = trimesh.util.concatenate(
        jetson_mount_hole_probes
    )
    j17a_hole_centers = np.asarray(
        [
            [x, y_sign * j17a_pattern_audit[1] / 2.0]
            for x in crossbar_x_audit
            for y_sign in (-1.0, 1.0)
        ],
        dtype=float,
    )
    hole_center_distances = np.linalg.norm(
        payload_hole_centers[:, None, :]
        - j17a_hole_centers[None, :, :],
        axis=2,
    )
    minimum_payload_to_j17a_hole_ligament = float(
        np.min(hole_center_distances)
        - payload_hole_diameter_audit / 2.0
        - j17a_hole_diameter_audit / 2.0
    )
    visible_collision_meshes = {
        "TORSO": world_links["TORSO"],
        "FACTORY_INTERFACE": lidar_meshes[
            "FACTORY_INTERFACE"
        ],
        "FACTORY_LIDAR_MOUNTS": lidar_meshes["FACTORY_LIDAR_MOUNTS"],
        "MID360_ADAPTER": lidar_meshes["MID360_ADAPTER"],
        "MID360_GUARD": lidar_meshes["MID360_GUARD"],
        "MID360_SENSOR": lidar_meshes["MID360_SENSOR"],
        "D435I_CAMERA": lidar_meshes["FRONT_CAMERA_BAR"],
        "CAMERA_MOUNT_BRACKET": lidar_meshes[
            "CAMERA_MOUNT_BRACKET"
        ],
        "CAMERA_CARRIER_PLATE": lidar_meshes[
            "CAMERA_CARRIER_PLATE"
        ],
        "CAMERA_RECEIVER_YOKE": lidar_meshes[
            "CAMERA_RECEIVER_YOKE"
        ],
    }
    visible_component_names = list(visible_collision_meshes)
    visible_collision_matrix_mm3 = {}
    for first_index, first_name in enumerate(visible_component_names):
        for second_name in visible_component_names[first_index + 1 :]:
            visible_collision_matrix_mm3[
                f"{first_name}__{second_name}"
            ] = intersection_volume_mm3(
                visible_collision_meshes[first_name],
                visible_collision_meshes[second_name],
            )
    lidar_geometry_audit = {
        "mount_normal_offset_mm": float(
            lidar_parameters["mid360_mount_normal_offset"]["value"]
        ),
        "visible_component_names": visible_component_names,
        "visible_collision_matrix_mm3": visible_collision_matrix_mm3,
        "declared_visible_engagement_pairs": [
            "MID360_GUARD__CAMERA_RECEIVER_YOKE"
        ],
        "boolean_intersection_mm3": {
            "factory_mounts_to_j20a": intersection_volume_mm3(
                lidar_meshes["FACTORY_LIDAR_MOUNTS"],
                lidar_meshes["MID360_ADAPTER"],
            ),
            "mid360_to_j20a": intersection_volume_mm3(
                lidar_meshes["MID360_SENSOR"],
                lidar_meshes["MID360_ADAPTER"],
            ),
            "mid360_to_s410": intersection_volume_mm3(
                lidar_meshes["MID360_SENSOR"],
                lidar_meshes["MID360_GUARD"],
            ),
            "mid360_to_hidden_bridge": intersection_volume_mm3(
                lidar_meshes["MID360_SENSOR"],
                lidar_meshes["MID360_MOUNT_BRIDGE"],
            ),
            "j20a_to_hidden_bridge": intersection_volume_mm3(
                lidar_meshes["MID360_ADAPTER"],
                lidar_meshes["MID360_MOUNT_BRIDGE"],
            ),
        },
        "surface_clearance": {
            "mid360_to_s410": vertex_sampled_clearance_mm(
                lidar_meshes["MID360_SENSOR"],
                lidar_meshes["MID360_GUARD"],
            ),
            "connector_to_s410": vertex_sampled_clearance_mm(
                lidar_meshes["MID360_CONNECTOR"],
                lidar_meshes["MID360_GUARD"],
            ),
        },
        "mount_hole_pattern_mm": hole_pattern.tolist(),
        "mount_hole_diameter_mm": hole_radius * 2.0,
        "hidden_bridge_size_mm": bridge_size.tolist(),
        "hidden_bridge_to_hole_edge_clearance_mm": (
            bridge_hole_edge_clearance.tolist()
        ),
        "upper_module_connected_components": len(
            lidar_meshes["UPPER_LIDAR_MODULE"].split(
                only_watertight=True
            )
        ),
        "upper_boolean_removed_negative_internal_shells_mm3": (
            lidar_meshes["UPPER_LIDAR_MODULE"].metadata.get(
                "removed_negative_internal_shells_mm3",
                [],
            )
        ),
        "payload_base": {
            "architecture": (
                "no_visible_spanning_plate_with_local_"
                "interface_feet_and_lidar_mounts"
            ),
            "visible_spanning_plate": False,
            "factory_lidar_mount_count": 4,
            "factory_lidar_mount_open_hole_diameter_mm": float(
                lidar_parameters["factory_lidar_mount_hole_diameter"]["value"]
            ),
            "official_hole_pattern_mm": payload_pattern_audit.tolist(),
            "open_hole_diameter_mm": payload_hole_diameter_audit,
            "sensor_crossbar_x_mm": crossbar_x_audit.tolist(),
            "sensor_crossbar_size_mm": crossbar_size_audit.tolist(),
            "j17a_hole_pattern_mm": j17a_pattern_audit.tolist(),
            "j17a_open_hole_diameter_mm": j17a_hole_diameter_audit,
            "visible_component_identity": "DEEP Robotics Interface",
            "ai_computer_identity": "NVIDIA Jetson Xavier NX",
            "ai_computer_location": "not_published",
            "factory_interface_envelope_mm": lidar_parameters[
                "factory_interface_box_envelope"
            ]["value"],
            "factory_interface_center_mm": lidar_parameters[
                "factory_interface_box_center"
            ]["value"],
            "factory_interface_mount_pattern_mm": lidar_parameters[
                "factory_interface_box_mount_pattern"
            ]["value"],
            "factory_interface_to_payload_base_intersection_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["FACTORY_INTERFACE"],
                    lidar_meshes["PAYLOAD_BASE"],
                )
            ),
            "factory_interface_to_torso_intersection_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["FACTORY_INTERFACE"],
                    world_links["TORSO"],
                )
            ),
            "factory_interface_to_mounts_intersection_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["FACTORY_INTERFACE"],
                    lidar_meshes["FACTORY_LIDAR_MOUNTS"],
                )
            ),
            "minimum_payload_to_j17a_hole_ligament_mm": (
                minimum_payload_to_j17a_hole_ligament
            ),
            "hole_probe_intersection_mm3": intersection_volume_mm3(
                lidar_meshes["PAYLOAD_BASE"],
                payload_hole_probe,
            ),
            "j17a_hole_probe_intersection_mm3": intersection_volume_mm3(
                lidar_meshes["PAYLOAD_BASE"],
                j17a_hole_probe,
            ),
        },
        "camera_mounting": {
            "product": "Intel RealSense D435i",
            "visual_geometry_node": "D435I_CAMERA",
            "visual_geometry_source": (
                "official_realsense_ros_d435_mesh_used_by_d435i_urdf"
            ),
            "visual_source_bbox_mm": lidar_meshes[
                "D435I_CAMERA"
            ].metadata.get("source_bbox_mm"),
            "source_to_robot_transform": lidar_meshes[
                "D435I_CAMERA"
            ].metadata.get("source_to_robot_transform"),
            "visual_print_ready": False,
            "print_geometry_node": "FRONT_CAMERA_BAR",
            "print_geometry_source": (
                "rear_plane_trimmed_voxel_reconstruction_of_official_"
                "ros_mesh_with_two_print_clearance_blind_holes"
            ),
            "official_nominal_bbox_mm": (
                lidar_parameters["d435i_nominal_size"]["value"]
            ),
            "j17a_mount_axis": (
                lidar_parameters["d435i_mount_axis_j17a_source"]["value"]
            ),
            "official_rear_thread": config[
                "d435i_mounting_contract"
            ]["official_rear_thread"],
            "official_rear_thread_count": config[
                "d435i_mounting_contract"
            ]["official_rear_thread_count"],
            "official_rear_thread_spacing_mm": config[
                "d435i_mounting_contract"
            ]["official_rear_thread_spacing_mm"],
            "official_maximum_thread_insertion_mm": config[
                "d435i_mounting_contract"
            ]["official_maximum_thread_insertion_mm"],
            "official_recommended_combined_torque_nm": config[
                "d435i_mounting_contract"
            ]["official_recommended_combined_torque_nm"],
            "camera_screw": config["d435i_mounting_contract"][
                "camera_screw"
            ],
            "camera_screw_count": 2,
            "carrier_screw": config["d435i_mounting_contract"][
                "carrier_screw"
            ],
            "carrier_screw_count": 2,
            "side_join_screw": config["d435i_mounting_contract"][
                "side_join_screw"
            ],
            "side_join_screw_count": config[
                "d435i_mounting_contract"
            ]["side_join_screw_count"],
            "calculated_camera_thread_insertion_mm": (
                float(
                    config["d435i_mounting_contract"][
                        "camera_screw_length_mm"
                    ]
                )
                - float(
                    config["d435i_mounting_contract"][
                        "bracket_plate_thickness_mm"
                    ]
                )
                - float(
                    config["d435i_mounting_contract"][
                        "bracket_main_face_clearance_mm"
                    ]
                )
            ),
            "calculated_carrier_thread_insertion_mm": (
                float(
                    config["d435i_mounting_contract"][
                        "carrier_screw_length_mm"
                    ]
                )
                - float(
                    config["d435i_mounting_contract"][
                        "bracket_plate_thickness_mm"
                    ]
                )
                - float(
                    config["d435i_mounting_contract"][
                        "bracket_main_face_clearance_mm"
                    ]
                )
            ),
            "camera_mating_pad_count": 2,
            "carrier_mating_pad_count": 2,
            "bracket_geometry_node": "CAMERA_MOUNT_BRACKET",
            "carrier_plate_geometry_node": "CAMERA_CARRIER_PLATE",
            "receiver_yoke_geometry_node": "CAMERA_RECEIVER_YOKE",
            "fastener_geometry_node": "CAMERA_FASTENERS",
            "socket_target": config["assembly_mounts"][
                "camera_mount_bracket"
            ]["socket_target"],
            "bracket_watertight": bool(
                lidar_meshes["CAMERA_MOUNT_BRACKET"].is_watertight
            ),
            "bracket_connected_components": len(
                lidar_meshes["CAMERA_MOUNT_BRACKET"].split(
                    only_watertight=True
                )
            ),
            "carrier_plate_watertight": bool(
                lidar_meshes["CAMERA_CARRIER_PLATE"].is_watertight
            ),
            "carrier_plate_connected_components": len(
                lidar_meshes["CAMERA_CARRIER_PLATE"].split(
                    only_watertight=True
                )
            ),
            "receiver_yoke_watertight": bool(
                lidar_meshes["CAMERA_RECEIVER_YOKE"].is_watertight
            ),
            "receiver_yoke_connected_components": len(
                lidar_meshes["CAMERA_RECEIVER_YOKE"].split(
                    only_watertight=True
                )
            ),
            "receiver_count": 2,
            "receiver_boss_outer_diameter_mm": float(
                config["d435i_mounting_contract"][
                    "receiver_boss_outer_diameter_mm"
                ]
            ),
            "receiver_bore_depth_mm": float(
                config["d435i_mounting_contract"][
                    "receiver_bore_depth_mm"
                ]
            ),
            "receiver_face_gap_mm": float(
                config["d435i_mounting_contract"][
                    "receiver_face_gap_mm"
                ]
            ),
            "receiver_guard_engagement_mm": float(
                config["d435i_mounting_contract"][
                    "receiver_guard_engagement_mm"
                ]
            ),
            "receiver_strut_size_mm": [
                float(
                    config["d435i_mounting_contract"][
                        "receiver_strut_width_mm"
                    ]
                ),
                float(
                    config["d435i_mounting_contract"][
                        "receiver_strut_thickness_mm"
                    ]
                ),
            ],
            "receiver_guard_surface_anchor_mm": lidar_meshes[
                "CAMERA_RECEIVER_YOKE"
            ].metadata.get("guard_surface_anchor_mm"),
            "receiver_guard_engaged_anchor_mm": lidar_meshes[
                "CAMERA_RECEIVER_YOKE"
            ].metadata.get("guard_engaged_anchor_mm"),
            "opposing_head_service_gap_mm": (
                float(
                    lidar_parameters["d435i_mount_standoff"]["value"]
                )
                - 2.0
                * (
                    float(
                        config["d435i_mounting_contract"][
                            "bracket_main_face_clearance_mm"
                        ]
                    )
                    + float(
                        config["d435i_mounting_contract"][
                            "bracket_plate_thickness_mm"
                        ]
                    )
                    + float(
                        config["d435i_mounting_contract"][
                            "camera_screw_head_height_mm"
                        ]
                    )
                )
            ),
            "visual_fastener_connected_components": len(
                lidar_meshes["CAMERA_FASTENERS"].split(
                    only_watertight=True
                )
            ),
            "print_fastener_connected_components": len(
                lidar_meshes["CAMERA_PRINT_FASTENERS"].split(
                    only_watertight=True
                )
            ),
            "print_clearance_hole_diameter_master_mm": config[
                "assembly_mounts"
            ]["camera_mount_bracket"][
                "print_clearance_hole_diameter_master_mm"
            ],
            "print_equivalent_screw_shaft_diameter_master_mm": config[
                "assembly_mounts"
            ]["camera_mount_bracket"][
                "print_equivalent_screw_shaft_diameter_master_mm"
            ],
            "receiver_minimum_radial_wall_print_mm": (
                (
                    float(
                        config["d435i_mounting_contract"][
                            "receiver_boss_outer_diameter_mm"
                        ]
                    )
                    - float(
                        config["assembly_mounts"][
                            "camera_mount_bracket"
                        ]["print_clearance_hole_diameter_master_mm"]
                    )
                )
                * float(config["print_profile"]["scale"])
                / 2.0
            ),
            "visible_collision_proxy": (
                "source_derived_watertight_print_body_for_open_"
                "official_visual_mesh"
            ),
            "official_visual_to_factory_mounts_clearance": (
                vertex_sampled_clearance_mm(
                    lidar_meshes["D435I_CAMERA"],
                    lidar_meshes["FACTORY_LIDAR_MOUNTS"],
                )
            ),
            "print_camera_to_factory_mounts_intersection_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["FRONT_CAMERA_BAR"],
                    lidar_meshes["FACTORY_LIDAR_MOUNTS"],
                )
            ),
            "camera_to_factory_mounts_intersection_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["FRONT_CAMERA_BAR"],
                    lidar_meshes["FACTORY_LIDAR_MOUNTS"],
                )
            ),
            "camera_to_bracket_intersection_mm3": intersection_volume_mm3(
                lidar_meshes["FRONT_CAMERA_BAR"],
                lidar_meshes["CAMERA_MOUNT_BRACKET"],
            ),
            "print_camera_to_print_bracket_intersection_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["FRONT_CAMERA_BAR"],
                    lidar_meshes["CAMERA_PRINT_BRACKET"],
                )
            ),
            "bracket_to_carrier_plate_intersection_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["CAMERA_MOUNT_BRACKET"],
                    lidar_meshes["CAMERA_CARRIER_PLATE"],
                )
            ),
            "print_bracket_to_print_carrier_plate_intersection_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["CAMERA_PRINT_BRACKET"],
                    lidar_meshes["CAMERA_PRINT_CARRIER_PLATE"],
                )
            ),
            "bracket_to_factory_mounts_intersection_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["CAMERA_MOUNT_BRACKET"],
                    lidar_meshes["FACTORY_LIDAR_MOUNTS"],
                )
            ),
            "bracket_to_guard_intersection_mm3": intersection_volume_mm3(
                lidar_meshes["CAMERA_MOUNT_BRACKET"],
                lidar_meshes["MID360_GUARD"],
            ),
            "bracket_to_guard_clearance": vertex_sampled_clearance_mm(
                lidar_meshes["CAMERA_MOUNT_BRACKET"],
                lidar_meshes["MID360_GUARD"],
            ),
            "carrier_plate_to_guard_intersection_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["CAMERA_CARRIER_PLATE"],
                    lidar_meshes["MID360_GUARD"],
                )
            ),
            "carrier_plate_to_guard_clearance": vertex_sampled_clearance_mm(
                lidar_meshes["CAMERA_CARRIER_PLATE"],
                lidar_meshes["MID360_GUARD"],
            ),
            "bracket_to_adapter_intersection_mm3": intersection_volume_mm3(
                lidar_meshes["CAMERA_MOUNT_BRACKET"],
                lidar_meshes["MID360_ADAPTER"],
            ),
            "carrier_plate_to_adapter_intersection_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["CAMERA_CARRIER_PLATE"],
                    lidar_meshes["MID360_ADAPTER"],
                )
            ),
            "receiver_yoke_to_guard_engagement_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["CAMERA_RECEIVER_YOKE"],
                    lidar_meshes["MID360_GUARD"],
                )
            ),
            "print_receiver_yoke_to_guard_engagement_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["CAMERA_PRINT_RECEIVER_YOKE"],
                    lidar_meshes["MID360_GUARD"],
                )
            ),
            "receiver_yoke_to_adapter_intersection_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["CAMERA_RECEIVER_YOKE"],
                    lidar_meshes["MID360_ADAPTER"],
                )
            ),
            "receiver_yoke_to_carrier_plate_intersection_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["CAMERA_RECEIVER_YOKE"],
                    lidar_meshes["CAMERA_CARRIER_PLATE"],
                )
            ),
            "print_receiver_yoke_to_print_carrier_plate_intersection_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["CAMERA_PRINT_RECEIVER_YOKE"],
                    lidar_meshes["CAMERA_PRINT_CARRIER_PLATE"],
                )
            ),
            "receiver_yoke_to_fasteners_intersection_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["CAMERA_RECEIVER_YOKE"],
                    lidar_meshes["CAMERA_FASTENERS"],
                )
            ),
            "print_receiver_yoke_to_print_fasteners_intersection_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["CAMERA_PRINT_RECEIVER_YOKE"],
                    lidar_meshes["CAMERA_PRINT_FASTENERS"],
                )
            ),
            "receiver_yoke_to_factory_mounts_intersection_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["CAMERA_RECEIVER_YOKE"],
                    lidar_meshes["FACTORY_LIDAR_MOUNTS"],
                )
            ),
            "receiver_yoke_to_interface_intersection_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["CAMERA_RECEIVER_YOKE"],
                    lidar_meshes["FACTORY_INTERFACE"],
                )
            ),
            "receiver_yoke_to_torso_intersection_mm3": (
                intersection_volume_mm3(
                    lidar_meshes["CAMERA_RECEIVER_YOKE"],
                    world_links["TORSO"],
                )
            ),
            "carrier_plate_to_receiver_yoke_clearance": (
                vertex_sampled_clearance_mm(
                    lidar_meshes["CAMERA_CARRIER_PLATE"],
                    lidar_meshes["CAMERA_RECEIVER_YOKE"],
                )
            ),
            "bracket_to_interface_intersection_mm3": intersection_volume_mm3(
                lidar_meshes["CAMERA_MOUNT_BRACKET"],
                lidar_meshes["FACTORY_INTERFACE"],
            ),
            "bracket_to_torso_intersection_mm3": intersection_volume_mm3(
                lidar_meshes["CAMERA_MOUNT_BRACKET"],
                world_links["TORSO"],
            ),
        },
        "longitudinal_fov_approximation_deg": {
            "method": (
                "native vertical FOV rotated in the front/rear "
                "longitudinal planes"
            ),
            "native": native_fov.tolist(),
            "front": (native_fov - lidar_tilt_deg).tolist(),
            "rear": (native_fov + lidar_tilt_deg).tolist(),
        },
    }
    upper_master_mm = lidar_meshes["UPPER_LIDAR_MODULE"].copy()
    upper_master_mm.apply_scale(1000.0)
    write_stl(MASTER_DIR / "upper_lidar_module_master_1_1.stl", upper_master_mm)
    camera_master_mm = lidar_meshes["FRONT_CAMERA_BAR"].copy()
    camera_master_mm.apply_scale(1000.0)
    write_stl(MASTER_DIR / "front_camera_bar_master_1_1.stl", camera_master_mm)
    camera_bracket_master_mm = lidar_meshes["CAMERA_PRINT_BRACKET"].copy()
    camera_bracket_master_mm.apply_scale(1000.0)
    write_stl(
        MASTER_DIR / "camera_mount_bracket_master_1_1.stl",
        camera_bracket_master_mm,
    )
    camera_carrier_plate_master_mm = lidar_meshes[
        "CAMERA_PRINT_CARRIER_PLATE"
    ].copy()
    camera_carrier_plate_master_mm.apply_scale(1000.0)
    write_stl(
        MASTER_DIR / "camera_carrier_plate_master_1_1.stl",
        camera_carrier_plate_master_mm,
    )
    camera_fasteners_master_mm = lidar_meshes["CAMERA_FASTENERS"].copy()
    camera_fasteners_master_mm.apply_scale(1000.0)
    write_stl(
        MASTER_DIR / "camera_fasteners_master_1_1.stl",
        camera_fasteners_master_mm,
    )

    lidar_reference_meshes = {
        name: mesh
        for name, mesh in lidar_meshes.items()
        if name
        not in (
            "UPPER_LIDAR_MODULE",
            "UPPER_DECK_INTERFACE",
            "MID360_SENSOR",
            "MID360_MOUNT_BRIDGE",
            "J17A_SENSOR_CARRIER",
            "J17A_BASE_SPACERS",
            "SENSOR_PRINT_CONNECTORS",
            "PAYLOAD_BASE",
            "FRONT_CAMERA_BAR",
            "CAMERA_PRINT_BRACKET",
            "CAMERA_PRINT_CARRIER_PLATE",
            "CAMERA_PRINT_RECEIVER_YOKE",
            "CAMERA_PRINT_FASTENERS",
        )
    }
    visual_reference_1_1 = {
        **visual_world_links,
        **lidar_reference_meshes,
    }
    printable_reference_1_1 = {
        **world_links,
        "UPPER_LIDAR_MODULE": lidar_meshes["UPPER_LIDAR_MODULE"],
        "FACTORY_INTERFACE": lidar_meshes[
            "FACTORY_INTERFACE"
        ],
        "FRONT_CAMERA_BAR": lidar_meshes["FRONT_CAMERA_BAR"],
        "CAMERA_MOUNT_BRACKET": lidar_meshes[
            "CAMERA_PRINT_BRACKET"
        ],
        "CAMERA_CARRIER_PLATE": lidar_meshes[
            "CAMERA_PRINT_CARRIER_PLATE"
        ],
        "CAMERA_FASTENERS": lidar_meshes["CAMERA_PRINT_FASTENERS"],
    }
    export_scene(
        visual_reference_1_1,
        REFERENCE_DIR / "lite3_lidar_1_1_reference.glb",
        millimetres=False,
    )
    export_scene(
        printable_reference_1_1,
        REFERENCE_DIR / "lite3_lidar_1_1_reference.3mf",
        millimetres=True,
    )

    combined_reference = trimesh.util.concatenate(
        list(visual_reference_1_1.values())
    )
    reference_bounds_mm = combined_reference.bounds * 1000.0
    visual_body = trimesh.util.concatenate(list(visual_world_links.values()))
    printable_body = trimesh.util.concatenate(list(world_links.values()))
    visual_body_bounds_mm = visual_body.bounds * 1000.0
    printable_body_bounds_mm = printable_body.bounds * 1000.0

    print_profile = config["print_profile"]
    print_scale = float(print_profile["scale"])
    hole_radius = (
        float(print_profile["pin_diameter_mm"]) / 2.0
        + float(print_profile["pin_radial_clearance_mm"])
    )
    cutter_length = 30.0
    cutters_by_link: dict[str, list[trimesh.Trimesh]] = {
        name: [] for name in world_links
    }
    print_joint_report: dict[str, Any] = {}
    for joint_name, joint in joints.items():
        center_mm = np.asarray(joint["center_m"]) * 1000.0 * print_scale
        axis = np.asarray(joint["axis"], dtype=float)
        cutter = trimesh_cylinder_between(
            center_mm - axis * cutter_length / 2.0,
            center_mm + axis * cutter_length / 2.0,
            hole_radius,
            40,
        )
        cutters_by_link[joint["parent"]].append(cutter)
        cutters_by_link[joint["child"]].append(cutter)
        print_joint_report[joint_name] = {
            "parent": joint["parent"],
            "child": joint["child"],
            "center_mm": center_mm.tolist(),
            "axis": axis.tolist(),
            "hole_radius_mm": hole_radius,
        }

    mounts = config["assembly_mounts"]
    upper_mount = mounts["upper_module"]
    upper_pin_meshes: list[trimesh.Trimesh] = []
    upper_mount_report: dict[str, Any] = {
        "evidence_class": upper_mount["evidence_class"],
        "pins": [],
    }
    deck_parameters = config["lidar_module"]["parameters_mm"]
    deck_center_print = (
        np.asarray(deck_parameters["deck_center"]["value"], dtype=float)
        * print_scale
    )
    deck_size_print = (
        np.asarray(deck_parameters["deck_size"]["value"], dtype=float)
        * print_scale
    )
    deck_xy_clearance = float(
        upper_mount["deck_pocket_xy_clearance_print_mm"]
    )
    deck_vertical_clearance = float(
        upper_mount["deck_pocket_vertical_clearance_print_mm"]
    )
    pocket_size = deck_size_print + np.asarray(
        [
            2.0 * deck_xy_clearance,
            2.0 * deck_xy_clearance,
            2.0 * deck_vertical_clearance,
        ]
    )
    pocket = trimesh.creation.box(extents=pocket_size)
    pocket.apply_translation(deck_center_print)
    cutters_by_link["TORSO"].append(pocket)
    upper_mount_report["deck_pocket"] = {
        "center_mm": deck_center_print.tolist(),
        "size_mm": pocket_size.tolist(),
        "xy_clearance_mm": deck_xy_clearance,
        "vertical_clearance_mm": deck_vertical_clearance,
    }
    upper_pin_length = float(upper_mount["pin_length_print_mm"])
    upper_pin_overlap = float(upper_mount["pin_overlap_print_mm"])
    upper_pin_radius = float(upper_mount["pin_radius_print_mm"])
    upper_socket_radius = float(upper_mount["socket_radius_print_mm"])
    upper_socket_extra = float(
        upper_mount["socket_extra_depth_print_mm"]
    )
    for index, center_master in enumerate(
        upper_mount["pin_centers_master_mm"],
        start=1,
    ):
        center_print = np.asarray(center_master, dtype=float) * print_scale
        pin_top = center_print.copy()
        pin_top[2] += upper_pin_overlap
        pin_bottom = pin_top.copy()
        pin_bottom[2] -= upper_pin_length
        pin = trimesh_cylinder_between(
            pin_bottom,
            pin_top,
            upper_pin_radius,
            40,
        )
        upper_pin_meshes.append(pin)
        socket_top = pin_top.copy()
        socket_top[2] += upper_socket_extra
        socket_bottom = pin_bottom.copy()
        socket_bottom[2] -= upper_socket_extra
        socket = trimesh_cylinder_between(
            socket_bottom,
            socket_top,
            upper_socket_radius,
            40,
        )
        cutters_by_link["TORSO"].append(socket)
        upper_mount_report["pins"].append(
            {
                "id": f"UPPER_PIN_{index}",
                "pin_start_mm": pin_bottom.tolist(),
                "pin_end_mm": pin_top.tolist(),
                "pin_radius_mm": upper_pin_radius,
                "socket_start_mm": socket_bottom.tolist(),
                "socket_end_mm": socket_top.tolist(),
                "socket_radius_mm": upper_socket_radius,
            }
        )

    camera_mount = mounts["camera_mount_bracket"]
    camera_mount_report: dict[str, Any] = {
        "evidence_class": camera_mount["evidence_class"],
        "socket_target": camera_mount["socket_target"],
        "camera_fasteners": 2,
        "carrier_fasteners": 2,
        "side_join_fasteners": int(
            config["d435i_mounting_contract"]["side_join_screw_count"]
        ),
        "official_camera_hole_spacing_mm": float(
            config["d435i_mounting_contract"][
                "official_rear_thread_spacing_mm"
            ]
        ),
        "print_clearance_hole_diameter_master_mm": float(
            camera_mount[
                "print_clearance_hole_diameter_master_mm"
            ]
        ),
        "print_equivalent_screw_shaft_diameter_master_mm": float(
            camera_mount[
                "print_equivalent_screw_shaft_diameter_master_mm"
            ]
        ),
        "print_radial_clearance_mm": (
            float(
                camera_mount[
                    "print_clearance_hole_diameter_master_mm"
                ]
            )
            - float(
                camera_mount[
                    "print_equivalent_screw_shaft_diameter_master_mm"
                ]
            )
        )
        * print_scale
        / 2.0,
        "carrier_side_hole_spacing_mm": float(
            config["d435i_mounting_contract"][
                "official_rear_thread_spacing_mm"
            ]
        ),
        "carrier_side_axis_source": "pinned_J17A_source_model",
        "receiver_geometry_node": "CAMERA_RECEIVER_YOKE",
        "receiver_boss_count": 2,
        "receiver_bore_depth_mm": float(
            config["d435i_mounting_contract"][
                "receiver_bore_depth_mm"
            ]
        ),
        "receiver_guard_engagement": "integrated_into_S410_guard",
    }

    print_parts: dict[str, trimesh.Trimesh] = {}
    assembly_print_reference: dict[str, trimesh.Trimesh] = {}
    print_report: dict[str, Any] = {}
    build_volume = np.asarray(print_profile["build_volume_mm"], dtype=float)
    for link_name, world_mesh in sorted(world_links.items()):
        mesh_mm = world_mesh.copy()
        mesh_mm.apply_scale(1000.0 * print_scale)
        holed = cut_joint_holes(mesh_mm, cutters_by_link[link_name])
        assembly_print_reference[link_name] = holed.copy()
        oriented = orient_for_print(holed)
        print_parts[link_name] = oriented
        metrics = mesh_metrics_mm(oriented)
        metrics["fits_build_volume"] = bool(
            np.all(np.asarray(metrics["bbox_size_mm"]) <= build_volume + 1.0e-6)
        )
        if not metrics["fits_build_volume"]:
            raise ValueError(f"Print part exceeds build volume: {link_name}")
        write_stl(PRINT_DIR / f"{link_name}.stl", oriented)
        print_report[link_name] = metrics

    upper_print = lidar_meshes["UPPER_LIDAR_MODULE"].copy()
    upper_print.apply_scale(1000.0 * print_scale)
    upper_print = union_print_meshes(upper_print, upper_pin_meshes)
    assembly_print_reference["UPPER_LIDAR_MODULE"] = upper_print.copy()
    upper_print = orient_for_print(upper_print)
    print_parts["UPPER_LIDAR_MODULE"] = upper_print
    write_stl(PRINT_DIR / "UPPER_LIDAR_MODULE.stl", upper_print)
    print_report["UPPER_LIDAR_MODULE"] = mesh_metrics_mm(upper_print)

    for component_name in ("FACTORY_INTERFACE",):
        component_print = lidar_meshes[component_name].copy()
        component_print.apply_scale(1000.0 * print_scale)
        assembly_print_reference[component_name] = component_print.copy()
        oriented = orient_for_print(component_print)
        metrics = mesh_metrics_mm(oriented)
        metrics["fits_build_volume"] = bool(
            np.all(
                np.asarray(metrics["bbox_size_mm"])
                <= build_volume + 1.0e-6
            )
        )
        if not metrics["fits_build_volume"]:
            raise ValueError(
                f"Print part exceeds build volume: {component_name}"
            )
        print_parts[component_name] = oriented
        write_stl(PRINT_DIR / f"{component_name}.stl", oriented)
        print_report[component_name] = metrics

    camera_print = lidar_meshes["FRONT_CAMERA_BAR"].copy()
    camera_print.apply_scale(1000.0 * print_scale)
    assembly_print_reference["FRONT_CAMERA_BAR"] = camera_print.copy()
    camera_print = orient_for_print(camera_print)
    print_parts["FRONT_CAMERA_BAR"] = camera_print
    write_stl(PRINT_DIR / "FRONT_CAMERA_BAR.stl", camera_print)
    print_report["FRONT_CAMERA_BAR"] = mesh_metrics_mm(camera_print)

    bracket_print = lidar_meshes["CAMERA_PRINT_BRACKET"].copy()
    bracket_print.apply_scale(1000.0 * print_scale)
    assembly_print_reference["CAMERA_MOUNT_BRACKET"] = bracket_print.copy()
    bracket_print = orient_for_print(bracket_print)
    print_parts["CAMERA_MOUNT_BRACKET"] = bracket_print
    write_stl(
        PRINT_DIR / "CAMERA_MOUNT_BRACKET.stl",
        bracket_print,
    )
    print_report["CAMERA_MOUNT_BRACKET"] = mesh_metrics_mm(bracket_print)

    carrier_plate_print = lidar_meshes[
        "CAMERA_PRINT_CARRIER_PLATE"
    ].copy()
    carrier_plate_print.apply_scale(1000.0 * print_scale)
    assembly_print_reference["CAMERA_CARRIER_PLATE"] = (
        carrier_plate_print.copy()
    )
    carrier_plate_print = orient_for_print(carrier_plate_print)
    print_parts["CAMERA_CARRIER_PLATE"] = carrier_plate_print
    write_stl(
        PRINT_DIR / "CAMERA_CARRIER_PLATE.stl",
        carrier_plate_print,
    )
    print_report["CAMERA_CARRIER_PLATE"] = mesh_metrics_mm(
        carrier_plate_print
    )

    fasteners_assembled_print = lidar_meshes[
        "CAMERA_PRINT_FASTENERS"
    ].copy()
    fasteners_assembled_print.apply_scale(1000.0 * print_scale)
    assembly_print_reference["CAMERA_FASTENERS"] = (
        fasteners_assembled_print.copy()
    )
    laid_out_fasteners = []
    for fastener_index, fastener in enumerate(
        fasteners_assembled_print.split(only_watertight=True)
    ):
        oriented_fastener = orient_for_print(fastener)
        oriented_fastener.apply_translation(
            [
                float(fastener_index % 4) * 5.0,
                float(fastener_index // 4) * 5.0,
                0.0,
            ]
        )
        laid_out_fasteners.append(oriented_fastener)
    fasteners_print = trimesh.util.concatenate(laid_out_fasteners)
    print_parts["CAMERA_FASTENERS"] = fasteners_print
    write_stl(PRINT_DIR / "CAMERA_FASTENERS.stl", fasteners_print)
    print_report["CAMERA_FASTENERS"] = mesh_metrics_mm(fasteners_print)

    pin_radius = float(print_profile["pin_diameter_mm"]) / 2.0
    pin_length = float(print_profile["pin_length_mm"])
    total_pins = int(print_profile["pin_count"]) + int(
        print_profile["spare_pin_count"]
    )
    pin_parts = []
    for index in range(total_pins):
        pin = trimesh.creation.cylinder(
            radius=pin_radius,
            height=pin_length,
            sections=40,
        )
        column = index % 7
        row = index // 7
        pin.apply_translation([column * 6.0, row * 6.0, pin_length / 2.0])
        pin_parts.append(pin)
    pins = trimesh.util.concatenate(pin_parts)
    pins.process(validate=True)
    print_parts["ASSEMBLY_PINS"] = pins
    write_stl(PRINT_DIR / "ASSEMBLY_PINS.stl", pins)
    print_report["ASSEMBLY_PINS"] = mesh_metrics_mm(pins)

    reference_print_scene = {}
    for name, mesh in assembly_print_reference.items():
        if name == "UPPER_LIDAR_MODULE":
            continue
        family_name = (
            "TORSO"
            if name == "TORSO"
            else (
                "FRONT_CAMERA_BAR"
                if name == "FRONT_CAMERA_BAR"
                else (
                    "CAMERA_MOUNT_BRACKET"
                    if name == "CAMERA_MOUNT_BRACKET"
                    else (
                        "CAMERA_CARRIER_PLATE"
                        if name == "CAMERA_CARRIER_PLATE"
                        else (
                            "CAMERA_FASTENERS"
                            if name == "CAMERA_FASTENERS"
                            else name.split("_")[-1]
                        )
                    )
                )
            )
        )
        reference_print_scene[name] = color_mesh(
            mesh,
            COLORS.get(family_name, [180, 180, 180, 255]),
        )
    for name in (
        "UPPER_DECK_INTERFACE",
        "MID360_OPTICAL_WINDOW",
        "MID360_BODY",
        "MID360_HOUSING_EXTERIOR",
        "MID360_CONNECTOR",
        "FACTORY_LIDAR_MOUNTS",
        "MID360_ADAPTER",
        "MID360_GUARD",
        "FACTORY_INTERFACE",
        "FACTORY_INTERFACE_CONNECTORS",
        "FACTORY_INTERFACE_VENTS",
    ):
        component_print = lidar_meshes[name].copy()
        component_print.apply_scale(1000.0 * print_scale)
        reference_print_scene[name] = color_mesh(
            component_print,
            COLORS[name],
        )
    scene = trimesh.Scene()
    for name, mesh in reference_print_scene.items():
        glb_mesh = mesh.copy()
        glb_mesh.apply_scale(0.001)
        scene.add_geometry(glb_mesh, node_name=name, geom_name=name)
    scene.export(REFERENCE_DIR / "lite3_lidar_1_4_assembled.glb")
    assembled_print_meshes = [
        *assembly_print_reference.values(),
    ]
    assembled_print_mesh = trimesh.util.concatenate(assembled_print_meshes)
    # Binary STL stores one unlabelled triangle soup. Directly concatenating
    # touching assembly parts lets an importer weld unrelated coincident
    # vertices and create open edges. A print-scale voxel reference preserves
    # the silhouette while producing an unambiguous closed STL surface.
    reference_pitch = float(
        print_profile["assembled_reference_voxel_pitch_mm"]
    )
    assembled_voxels = assembled_print_mesh.voxelized(
        reference_pitch,
        method="subdivide",
    )
    assembled_voxels.fill()
    assembled_stl = assembled_voxels.marching_cubes
    assembled_stl.apply_transform(assembled_voxels.transform)
    assembled_stl.remove_unreferenced_vertices()
    if not assembled_stl.is_watertight or not assembled_stl.is_winding_consistent:
        raise ValueError("Assembled 1:4 reference STL is not closed")
    write_stl(
        REFERENCE_DIR / "lite3_lidar_1_4_assembled_reference.stl",
        assembled_stl,
    )

    layout_parts = arrange_layout(
        print_parts,
        float(print_profile["build_volume_mm"][0]),
    )
    layout_scene = trimesh.Scene()
    for name, mesh in layout_parts.items():
        glb_mesh = color_mesh(mesh, [175, 180, 186, 255])
        glb_mesh.apply_scale(0.001)
        layout_scene.add_geometry(
            glb_mesh,
            node_name=name,
            geom_name=name,
        )
    layout_scene.export(REFERENCE_DIR / "lite3_lidar_1_4_print_layout.glb")

    output_paths = [
        *sorted(MASTER_DIR.glob("*")),
        *sorted(PRINT_DIR.glob("*")),
        *sorted(REFERENCE_DIR.glob("*")),
    ]
    output_report = {
        path.name: {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in output_paths
        if path.is_file()
    }
    report = {
        "schema_version": 1,
        "model_id": config["model_id"],
        "artifact_label": config["artifact_label"],
        "forbidden_labels": config["forbidden_labels"],
        "parameters_path": str(PARAMETERS_PATH),
        "parameters_sha256": sha256(PARAMETERS_PATH),
        "sources": {
            name: {
                "path": str(path),
                "sha256": sha256(path),
                "size_bytes": path.stat().st_size,
            }
            for name, path in sources.items()
        },
        "source_topology": source_report,
        "master_reconstruction": master_report,
        "body_geometry_tracks": {
            "visual_reference": {
                "body_source": "official_high_resolution_urdf_dae",
                "output": "models/reference/lite3_lidar_1_1_reference.glb",
                "print_ready": False,
                "claim": (
                    "Smooth official exterior for visual/CAD reference. "
                    "The source contains open and non-manifold shells."
                ),
                "bbox_min_mm": visual_body_bounds_mm[0].tolist(),
                "bbox_max_mm": visual_body_bounds_mm[1].tolist(),
                "bbox_size_mm": (
                    visual_body_bounds_mm[1] - visual_body_bounds_mm[0]
                ).tolist(),
                "ground_error_mm": float(visual_body_bounds_mm[0, 2]),
            },
            "printable_reference": {
                "body_source": (
                    "watertight_voxel_reconstruction_with_bounded_"
                    "topology_preserving_smoothing"
                ),
                "output": "models/reference/lite3_lidar_1_1_reference.3mf",
                "print_ready": True,
                "claim": (
                    "Multi-object printable reference; not the original "
                    "manufacturer CAD surface."
                ),
                "bbox_min_mm": printable_body_bounds_mm[0].tolist(),
                "bbox_max_mm": printable_body_bounds_mm[1].tolist(),
                "bbox_size_mm": (
                    printable_body_bounds_mm[1] - printable_body_bounds_mm[0]
                ).tolist(),
                "ground_error_mm": float(printable_body_bounds_mm[0, 2]),
            },
        },
        "standing_reference_1_1": {
            "bbox_min_mm": reference_bounds_mm[0].tolist(),
            "bbox_max_mm": reference_bounds_mm[1].tolist(),
            "bbox_size_mm": (
                reference_bounds_mm[1] - reference_bounds_mm[0]
            ).tolist(),
            "ground_error_mm": float(reference_bounds_mm[0, 2]),
            "official_target_mm": [
                float(
                    config["assembled_variant_envelope"]["length_mm"]["value"]
                ),
                float(
                    config["assembled_variant_envelope"]["width_mm"]["value"]
                ),
                float(
                    config["assembled_variant_envelope"]["height_mm"]["value"]
                ),
            ],
            "factory_official_target_mm": [
                float(config["official_envelope"]["length_mm"]["value"]),
                float(config["official_envelope"]["width_mm"]["value"]),
                float(config["official_envelope"]["height_mm"]["value"]),
            ],
            "height_target_evidence_class": config[
                "assembled_variant_envelope"
            ]["height_mm"]["evidence_class"],
        },
        "print_profile": print_profile,
        "joint_holes": print_joint_report,
        "assembly_mounts": {
            "upper_module": upper_mount_report,
            "camera_mount_bracket": camera_mount_report,
        },
        "lidar_geometry_audit": lidar_geometry_audit,
        "print_parts": print_report,
        "outputs": output_report,
        "claim_boundary": (
            "Static printable exterior replica. LiDAR dimensions not published "
            "by the manufacturer remain image estimates. Not functional, "
            "load-bearing, fit-validated, or manufacturing-exact."
        ),
    }
    report_path = REPORT_DIR / "build_report.json"
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"report={report_path}", flush=True)
    print(
        "reference_bbox_mm="
        + ",".join(
            f"{value:.6f}"
            for value in report["standing_reference_1_1"]["bbox_size_mm"]
        ),
        flush=True,
    )
    print(f"print_part_count={len(print_parts)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
