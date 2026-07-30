#!/usr/bin/env python3
"""Assemble an official Lite3 URDF and its visual meshes into single 3D files."""

from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import trimesh


def parse_vector(value: str | None, default: tuple[float, float, float]) -> np.ndarray:
    if not value:
        return np.asarray(default, dtype=float)
    result = np.fromstring(value, sep=" ", dtype=float)
    if result.shape != (3,):
        raise ValueError(f"Expected three values, got {value!r}")
    return result


def origin_transform(origin: ET.Element | None) -> np.ndarray:
    xyz = parse_vector(origin.get("xyz") if origin is not None else None, (0, 0, 0))
    rpy = parse_vector(origin.get("rpy") if origin is not None else None, (0, 0, 0))
    roll, pitch, yaw = rpy

    rx = trimesh.transformations.rotation_matrix(roll, (1, 0, 0))
    ry = trimesh.transformations.rotation_matrix(pitch, (0, 1, 0))
    rz = trimesh.transformations.rotation_matrix(yaw, (0, 0, 1))
    transform = rz @ ry @ rx
    transform[:3, 3] = xyz
    return transform


def scene_meshes(path: Path) -> list[trimesh.Trimesh]:
    loaded = trimesh.load(path, force="scene", process=False)
    meshes: list[trimesh.Trimesh] = []
    for node_name in loaded.graph.nodes_geometry:
        node_transform, geometry_name = loaded.graph[node_name]
        mesh = loaded.geometry[geometry_name].copy()
        mesh.apply_transform(node_transform)
        meshes.append(mesh)
    if not meshes:
        raise ValueError(f"No mesh geometry found in {path}")
    return meshes


def resolve_link_transforms(
    robot: ET.Element,
    hip_y_angle: float,
    knee_angle: float,
) -> dict[str, np.ndarray]:
    child_joints: dict[str, tuple[str, np.ndarray]] = {}
    for joint in robot.findall("joint"):
        parent = joint.find("parent")
        child = joint.find("child")
        if parent is None or child is None:
            raise ValueError(f"Joint {joint.get('name')} lacks parent or child")
        joint_name = joint.get("name", "")
        joint_angle = 0.0
        if joint_name.endswith("_HipY_joint"):
            joint_angle = hip_y_angle
        elif joint_name.endswith("_Knee_joint"):
            joint_angle = knee_angle
        axis_element = joint.find("axis")
        axis = parse_vector(
            axis_element.get("xyz") if axis_element is not None else None,
            (1, 0, 0),
        )
        joint_rotation = trimesh.transformations.rotation_matrix(joint_angle, axis)
        child_joints[child.get("link")] = (
            parent.get("link"),
            origin_transform(joint.find("origin")) @ joint_rotation,
        )

    link_names = [link.get("name") for link in robot.findall("link")]
    roots = [name for name in link_names if name not in child_joints]
    if len(roots) != 1:
        raise ValueError(f"Expected one root link, found {roots}")

    transforms: dict[str, np.ndarray] = {roots[0]: np.eye(4)}

    def resolve(link_name: str) -> np.ndarray:
        if link_name in transforms:
            return transforms[link_name]
        parent_name, joint_transform = child_joints[link_name]
        transforms[link_name] = resolve(parent_name) @ joint_transform
        return transforms[link_name]

    for name in link_names:
        resolve(name)
    return transforms


def assemble(
    urdf_path: Path,
    hip_y_angle: float,
    knee_angle: float,
    ground_align: bool,
    foot_radius_m: float,
    output_up_axis: str,
) -> tuple[
    trimesh.Scene,
    trimesh.Trimesh,
    dict[str, np.ndarray],
    float,
    int,
]:
    robot = ET.parse(urdf_path).getroot()
    link_transforms = resolve_link_transforms(robot, hip_y_angle, knee_angle)
    foot_names = ("FL_FOOT", "FR_FOOT", "HL_FOOT", "HR_FOOT")
    missing_feet = [name for name in foot_names if name not in link_transforms]
    if missing_feet:
        raise ValueError(f"URDF lacks expected foot links: {missing_feet}")

    foot_positions = {
        name: link_transforms[name][:3, 3].copy() for name in foot_names
    }
    foot_heights = np.asarray([position[2] for position in foot_positions.values()])
    if np.ptp(foot_heights) > 1.0e-6:
        raise ValueError(
            "Factory-standing pose does not place all feet at one height: "
            + ", ".join(f"{value:.9f}" for value in foot_heights)
        )

    root_z_offset = 0.0
    if ground_align:
        root_z_offset = foot_radius_m - float(np.mean(foot_heights))
        root_translation = np.eye(4)
        root_translation[2, 3] = root_z_offset
        link_transforms = {
            name: root_translation @ transform
            for name, transform in link_transforms.items()
        }
        foot_positions = {
            name: link_transforms[name][:3, 3].copy() for name in foot_names
        }

    vertical_index = 2
    if output_up_axis == "y":
        # URDF uses Z-up; Fusion's default modeling space and glTF use Y-up.
        output_transform = trimesh.transformations.rotation_matrix(
            -np.pi / 2.0, (1, 0, 0)
        )
        link_transforms = {
            name: output_transform @ transform
            for name, transform in link_transforms.items()
        }
        foot_positions = {
            name: link_transforms[name][:3, 3].copy() for name in foot_names
        }
        vertical_index = 1

    output_scene = trimesh.Scene()
    assembled_meshes: list[trimesh.Trimesh] = []

    for link in robot.findall("link"):
        link_name = link.get("name")
        link_transform = link_transforms[link_name]
        for visual_index, visual in enumerate(link.findall("visual")):
            geometry = visual.find("geometry")
            mesh_element = geometry.find("mesh") if geometry is not None else None
            if mesh_element is None:
                continue

            mesh_path = (urdf_path.parent / mesh_element.get("filename")).resolve()
            scale = parse_vector(mesh_element.get("scale"), (1, 1, 1))
            scale_transform = np.eye(4)
            scale_transform[0, 0], scale_transform[1, 1], scale_transform[2, 2] = scale
            visual_transform = origin_transform(visual.find("origin"))
            world_transform = link_transform @ visual_transform @ scale_transform

            for geometry_index, mesh in enumerate(scene_meshes(mesh_path)):
                mesh.apply_transform(world_transform)
                if np.linalg.det(world_transform[:3, :3]) < 0:
                    mesh.invert()
                name = f"{link_name}_visual_{visual_index}_geometry_{geometry_index}"
                output_scene.add_geometry(mesh, node_name=name, geom_name=name)
                assembled_meshes.append(mesh)

    if not assembled_meshes:
        raise ValueError("URDF contained no visual mesh geometry")
    return (
        output_scene,
        trimesh.util.concatenate(assembled_meshes),
        foot_positions,
        root_z_offset,
        vertical_index,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("urdf", type=Path)
    parser.add_argument("output_prefix", type=Path)
    parser.add_argument("--hip-y", type=float, default=0.0)
    parser.add_argument("--knee", type=float, default=0.0)
    parser.add_argument(
        "--ground-align",
        action="store_true",
        help="Translate the root so the four spherical feet touch z=0.",
    )
    parser.add_argument(
        "--foot-radius-m",
        type=float,
        default=0.02,
        help="Radius of the URDF foot collision sphere in metres.",
    )
    parser.add_argument(
        "--output-up-axis",
        choices=("z", "y"),
        default="z",
        help="Use z for URDF-native output or y for Fusion/glTF-oriented output.",
    )
    args = parser.parse_args()

    scene, mesh_meters, foot_positions, root_z_offset, vertical_index = assemble(
        args.urdf.resolve(),
        args.hip_y,
        args.knee,
        args.ground_align,
        args.foot_radius_m,
        args.output_up_axis,
    )
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)

    glb_path = args.output_prefix.with_suffix(".glb")
    stl_path = args.output_prefix.with_suffix(".stl")
    scene.export(glb_path)

    mesh_millimeters = mesh_meters.copy()
    mesh_millimeters.apply_scale(1000.0)
    mesh_millimeters.export(stl_path)

    bounds_m = scene.bounds
    size_m = bounds_m[1] - bounds_m[0]
    print(f"glb={glb_path}")
    print(f"stl={stl_path}")
    print(f"geometry_count={len(scene.geometry)}")
    print(f"vertices={len(mesh_meters.vertices)}")
    print(f"faces={len(mesh_meters.faces)}")
    print(f"hip_y_rad={args.hip_y:.6f}")
    print(f"knee_rad={args.knee:.6f}")
    print(f"root_z_offset_m={root_z_offset:.9f}")
    print(f"output_up_axis={args.output_up_axis}")
    for name, position in foot_positions.items():
        print(
            f"{name.lower()}_center_m="
            + ",".join(f"{value:.9f}" for value in position)
        )
    foot_heights = [
        position[vertical_index] for position in foot_positions.values()
    ]
    print(f"foot_center_height_spread_m={np.ptp(foot_heights):.9f}")
    print(
        "ground_contact_height_m="
        f"{float(np.mean(foot_heights)) - args.foot_radius_m:.9f}"
    )
    print(
        "assembled_size_m="
        + ",".join(f"{value:.6f}" for value in size_m)
    )


if __name__ == "__main__":
    main()
