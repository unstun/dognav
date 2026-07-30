#!/usr/bin/env python3
"""Prepare an evidence-only Lite3 LiDAR V1.0.7 appearance baseline.

The candidate deliberately does not modify the printable-replica generator.
It combines the official Lite3 standing visual, official Mid-360 and D435
geometry, related-source J17A/J20A/S410 geometry, and an image-derived long
Interface enclosure.  The Venture FAST-LIVO2 BZ20/AGX arrangement and every
custom Pro adapter are excluded.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import trimesh
from scipy.ndimage import maximum_filter
from scipy.spatial import cKDTree


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[2]
REPLICA_ROOT = (
    REPO_ROOT
    / "references/derived/2026-07-24_lite3-lidar-printable-replica"
)
CURRENT_GLB = (
    REPLICA_ROOT / "models/reference/lite3_lidar_1_1_reference.glb"
)
HISTORY_GLB = (
    REPLICA_ROOT
    / "rebuild-check-j17a-ipc-base/models/reference/"
    "lite3_lidar_1_1_reference.glb"
)
DIRECT_MESH_ROOT = (
    TASK_ROOT / "evidence/j17a-direct-camera-candidate/meshes"
)
DIRECT_MANIFEST = DIRECT_MESH_ROOT.parent / "manifest.json"
OUTPUT_ROOT = (
    TASK_ROOT / "evidence/official-lidar-v107-baseline-candidate"
)
MESH_ROOT = OUTPUT_ROOT / "meshes"
MODEL_ROOT = OUTPUT_ROOT / "models"
MANIFEST = OUTPUT_ROOT / "manifest.json"
MANUAL_POSE_BODY_SOURCE = (
    MODEL_ROOT / "lite3_official_manual_pose.stl"
)
OFFICIAL_HIGH_RES_URDF = (
    REPO_ROOT
    / "references/upstream/2026-07-24_deep-robotics-model/"
    "source/high_res_official/Lite3/urdf/Lite3_high_res.urdf"
)
OFFICIAL_CURRENT_LIDAR_MEDIA_ROOT = (
    REPO_ROOT
    / "references/upstream/"
    "2026-07-26_lite3-current-lidar-official-us-media"
)
OFFICIAL_CURRENT_LIDAR_FRONT_LEFT = (
    OFFICIAL_CURRENT_LIDAR_MEDIA_ROOT
    / "source/original/lite3-lidar-current-front-left-800x600.jpg"
)
J17A_SOURCE_STEP = (
    REPO_ROOT
    / "references/upstream/2026-07-24_lite3-venture-fast-livo2-hardware/"
    "source/original/1T21-J17A-lidar base.STEP"
)
J17A_SOURCE_DRAWING = (
    REPO_ROOT
    / "references/upstream/2026-07-24_lite3-venture-fast-livo2-hardware/"
    "derived/j17a-drawing.png"
)

TARGET_GUARD_TOP_MM = 496.0
SENSOR_IMAGE_X_SHIFT_MM = 55.0
INTERFACE_LENGTH_MM = 233.0
INTERFACE_WIDTH_MM = 92.0
INTERFACE_HEIGHT_MM = 46.0
INTERFACE_CENTER_X_MM = -0.5
INTERFACE_SOURCE_BOTTOM_Z_MM = 428.0
INTERFACE_CORNER_RADIUS_MM = 0.8
MANUAL_POSE_HIP_Y_RAD = -0.68
MANUAL_POSE_KNEE_RAD = 1.48
INTERFACE_CARRIER_CLEARANCE_MM = 0.8
INTERFACE_FOOT_AXIS_X_MM = (-86.0, 82.0)
INTERFACE_FOOT_AXIS_Y_MM = (-36.0, 36.0)
INTERFACE_FOOT_RADIUS_MM = 7.5
INTERFACE_M3_CLEARANCE_DIAMETER_MM = 3.4
INTERFACE_M3_HEAD_DIAMETER_MM = 5.5
INTERFACE_M3_HEAD_HEIGHT_MM = 3.0
INTERFACE_RECEIVER_OUTER_DIAMETER_MM = 10.0
INTERFACE_RECEIVER_MINOR_DIAMETER_MM = 2.5
INTERFACE_RECEIVER_DEPTH_MM = 5.0

# The J17A drawing explicitly calls out four M3 threaded robot-side holes.
# Their source axes are X=-51.75/58.25, Y=+/-43, Z=0..2.5 mm.  After the
# related-source rigid transform, the unregistered robot-X axes are
# 82.851997/192.851997 mm.  The V1.0.7 image registration then applies the
# shared sensor X shift below.
J17A_AXIS_X_MM = tuple(
    value + SENSOR_IMAGE_X_SHIFT_MM
    for value in (82.851997, 192.851997)
)
J17A_AXIS_Y_MM = (-43.0, 43.0)
J17A_SOURCE_SEATING_Z_MM = 446.0
J17A_SOURCE_THREAD_DEPTH_MM = 2.5
J17A_M3_CLEARANCE_DIAMETER_MM = 3.4
J17A_SUPPORT_MAIN_SIZE_MM = 14.0
J17A_SUPPORT_BODY_FASTENER_Y_OFFSET_MM = 6.0
J17A_SUPPORT_FOOT_SIZE_MM = 8.0
J17A_SUPPORT_LOW_HEIGHT_MM = 6.0
J17A_SUPPORT_BOTTOM_CLEARANCE_MM = 0.25
J17A_SUPPORT_PROFILE_SAMPLES = 21

M3_SHAFT_DIAMETER_MM = 3.0
M3_HEAD_DIAMETER_MM = 5.5
M3_HEAD_HEIGHT_MM = 3.0
CAMERA_AXIS_ROBOT = np.asarray(
    [0.9396926207859084, 0.0, -0.3420201433256687],
    dtype=float,
)

SENSOR_INPUT_NODES = [
    "J17A_SENSOR_CARRIER_SOURCE",
    "MID360_ADAPTER",
    "MID360_GUARD",
    "MID360_BODY",
    "MID360_HOUSING_EXTERIOR",
    "MID360_OPTICAL_WINDOW",
    "MID360_CONNECTOR",
]

COLORS = {
    "FULL_LITE3_OFFICIAL_VISUAL": [210, 214, 220, 255],
    "LITE3_TOP_CONTACT_SURFACE": [205, 209, 214, 255],
    "J17A_SENSOR_CARRIER_CANDIDATE": [102, 106, 112, 255],
    "MID360_ADAPTER": [148, 153, 158, 255],
    "MID360_GUARD": [24, 26, 30, 255],
    "MID360_BODY": [145, 150, 156, 255],
    "MID360_HOUSING_EXTERIOR": [160, 165, 171, 255],
    "MID360_OPTICAL_WINDOW": [14, 71, 148, 255],
    "MID360_CONNECTOR": [25, 27, 31, 255],
    "D435I_CAMERA": [184, 189, 196, 255],
    "D435_FRONT_FACE_DERIVED": [22, 24, 28, 255],
    "D435_DIRECT_FASTENER_REFERENCES": [38, 40, 44, 255],
    "INTERFACE_BODY": [218, 220, 222, 255],
    "INTERFACE_LID": [232, 233, 234, 255],
    "INTERFACE_FRONT_CAP": [190, 193, 196, 255],
    "INTERFACE_PORT_POWER": [213, 143, 37, 255],
    "INTERFACE_PORT_DATA": [28, 31, 35, 255],
    "INTERFACE_PORT_USB3": [35, 100, 179, 255],
    "INTERFACE_VENTS": [35, 38, 42, 255],
    "INTERFACE_SERVICE_PANEL": [104, 108, 113, 255],
    "INTERFACE_FEET": [83, 87, 92, 255],
    "INTERFACE_M3_FASTENERS": [43, 46, 51, 255],
    "INTERFACE_RECEIVER_PROXIES": [174, 111, 42, 255],
    "INTERFACE_TOP_FASTENER": [72, 75, 80, 255],
    "INTERFACE_SIDE_FASTENER": [72, 75, 80, 255],
    "INTERFACE_END_FASTENERS": [72, 75, 80, 255],
    "J17A_LOCAL_SUPPORTS": [92, 96, 102, 255],
    "J17A_UPWARD_M3_FASTENERS": [43, 46, 51, 255],
    "J17A_BODY_M3_FASTENERS": [43, 46, 51, 255],
    "J17A_BODY_RECEIVER_PROXIES": [174, 111, 42, 255],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_mm_as_m(
    path: Path,
    *,
    repair: bool = False,
) -> trimesh.Trimesh:
    mesh = trimesh.load_mesh(
        path,
        process=repair,
        validate=repair,
        maintain_order=True,
    )
    mesh.apply_scale(0.001)
    return mesh


def rounded_rect_prism(
    length_m: float,
    width_m: float,
    height_m: float,
    radius_m: float,
    center_m: np.ndarray,
    corner_sections: int = 8,
) -> trimesh.Trimesh:
    """Create a closed Z-extruded rounded rectangle without extra packages."""
    half_x = length_m / 2.0
    half_y = width_m / 2.0
    radius_m = min(radius_m, half_x, half_y)
    corner_centers = [
        (half_x - radius_m, half_y - radius_m, 0.0),
        (-half_x + radius_m, half_y - radius_m, math.pi / 2.0),
        (-half_x + radius_m, -half_y + radius_m, math.pi),
        (half_x - radius_m, -half_y + radius_m, 3.0 * math.pi / 2.0),
    ]
    contour: list[list[float]] = []
    for cx, cy, start in corner_centers:
        for index in range(corner_sections + 1):
            angle = start + index * (math.pi / 2.0) / corner_sections
            contour.append(
                [
                    cx + radius_m * math.cos(angle),
                    cy + radius_m * math.sin(angle),
                ]
            )

    count = len(contour)
    z_bottom = -height_m / 2.0
    z_top = height_m / 2.0
    vertices = [
        [x_value, y_value, z_bottom] for x_value, y_value in contour
    ]
    vertices.extend(
        [x_value, y_value, z_top] for x_value, y_value in contour
    )
    bottom_center = len(vertices)
    vertices.append([0.0, 0.0, z_bottom])
    top_center = len(vertices)
    vertices.append([0.0, 0.0, z_top])

    faces: list[list[int]] = []
    for index in range(count):
        next_index = (index + 1) % count
        faces.append([bottom_center, next_index, index])
        faces.append([top_center, count + index, count + next_index])
        faces.append([index, next_index, count + next_index])
        faces.append([index, count + next_index, count + index])

    mesh = trimesh.Trimesh(
        vertices=np.asarray(vertices),
        faces=np.asarray(faces),
        process=True,
        validate=True,
    )
    mesh.apply_translation(center_m)
    return mesh


def box_mm(
    extents_mm: list[float],
    center_mm: list[float],
) -> trimesh.Trimesh:
    transform = trimesh.transformations.translation_matrix(
        np.asarray(center_mm, dtype=float) / 1000.0
    )
    return trimesh.creation.box(
        extents=np.asarray(extents_mm, dtype=float) / 1000.0,
        transform=transform,
    )


def cylinder_mm(
    radius_mm: float,
    height_mm: float,
    center_mm: list[float],
    axis: str = "z",
) -> trimesh.Trimesh:
    mesh = trimesh.creation.cylinder(
        radius=radius_mm / 1000.0,
        height=height_mm / 1000.0,
        sections=48,
    )
    if axis == "x":
        mesh.apply_transform(
            trimesh.transformations.rotation_matrix(
                math.pi / 2.0,
                [0.0, 1.0, 0.0],
            )
        )
    elif axis == "y":
        mesh.apply_transform(
            trimesh.transformations.rotation_matrix(
                math.pi / 2.0,
                [1.0, 0.0, 0.0],
            )
        )
    mesh.apply_translation(np.asarray(center_mm, dtype=float) / 1000.0)
    return mesh


def concatenate(meshes: list[trimesh.Trimesh]) -> trimesh.Trimesh:
    return trimesh.util.concatenate(meshes)


class TopSurfaceSampler:
    """Sample the uppermost source-body triangle at an XY position."""

    def __init__(self, mesh_m: trimesh.Trimesh) -> None:
        triangles_mm = np.asarray(mesh_m.triangles, dtype=float) * 1000.0
        self.xy = triangles_mm[:, :, :2]
        self.z = triangles_mm[:, :, 2]
        self.centroid_tree = cKDTree(np.mean(self.xy, axis=1))
        edge_0 = self.xy[:, 1] - self.xy[:, 0]
        edge_1 = self.xy[:, 2] - self.xy[:, 0]
        projected_area_mm2 = np.abs(
            edge_0[:, 0] * edge_1[:, 1]
            - edge_0[:, 1] * edge_1[:, 0]
        ) / 2.0
        self.large_triangle_indices = np.flatnonzero(
            projected_area_mm2 >= 25.0
        )

    def sample_mm(self, x_mm: float, y_mm: float) -> float:
        point = np.asarray([x_mm, y_mm], dtype=float)
        candidate_count = min(8192, len(self.xy))
        _, candidate_indices = self.centroid_tree.query(
            point,
            k=candidate_count,
        )
        candidate_indices = np.unique(
            np.concatenate(
                (
                    np.atleast_1d(candidate_indices),
                    self.large_triangle_indices,
                )
            )
        )
        candidate_xy = self.xy[candidate_indices]
        candidate_z = self.z[candidate_indices]
        first = candidate_xy[:, 0]
        edge_0 = candidate_xy[:, 1] - first
        edge_1 = candidate_xy[:, 2] - first
        offset = point - first
        denominator = (
            edge_0[:, 0] * edge_1[:, 1]
            - edge_1[:, 0] * edge_0[:, 1]
        )
        valid = np.abs(denominator) > 1.0e-12
        barycentric_0 = np.full(len(candidate_xy), np.nan)
        barycentric_1 = np.full(len(candidate_xy), np.nan)
        barycentric_0[valid] = (
            offset[valid, 0] * edge_1[valid, 1]
            - edge_1[valid, 0] * offset[valid, 1]
        ) / denominator[valid]
        barycentric_1[valid] = (
            edge_0[valid, 0] * offset[valid, 1]
            - offset[valid, 0] * edge_0[valid, 1]
        ) / denominator[valid]
        inside = (
            valid
            & (barycentric_0 >= -1.0e-9)
            & (barycentric_1 >= -1.0e-9)
            & (barycentric_0 + barycentric_1 <= 1.0 + 1.0e-9)
        )
        if not np.any(inside):
            raise RuntimeError(
                f"No body surface found at ({x_mm}, {y_mm}) mm"
            )
        intersection_z = (
            candidate_z[inside, 0]
            + barycentric_0[inside]
            * (candidate_z[inside, 1] - candidate_z[inside, 0])
            + barycentric_1[inside]
            * (candidate_z[inside, 2] - candidate_z[inside, 0])
        )
        return float(np.max(intersection_z))


def profiled_rect_prism_mm(
    center_x_mm: float,
    center_y_mm: float,
    size_x_mm: float,
    size_y_mm: float,
    top_z_mm: float,
    sampler: TopSurfaceSampler,
    *,
    sample_count: int = J17A_SUPPORT_PROFILE_SAMPLES,
    bottom_clearance_mm: float = J17A_SUPPORT_BOTTOM_CLEARANCE_MM,
) -> tuple[trimesh.Trimesh, list[list[float]]]:
    """Build a flat-top support whose lower skin follows the visual body."""
    x_values = np.linspace(
        center_x_mm - size_x_mm / 2.0,
        center_x_mm + size_x_mm / 2.0,
        sample_count,
    )
    y_values = np.linspace(
        center_y_mm - size_y_mm / 2.0,
        center_y_mm + size_y_mm / 2.0,
        sample_count,
    )
    sampled_surface_grid = np.asarray(
        [
            [
                sampler.sample_mm(float(x_value), float(y_value))
                for y_value in y_values
            ]
            for x_value in x_values
        ],
        dtype=float,
    )
    bottom_grid = (
        maximum_filter(
            sampled_surface_grid,
            size=3,
            mode="nearest",
        )
        + bottom_clearance_mm
    ).tolist()
    if top_z_mm <= max(max(row) for row in bottom_grid):
        raise RuntimeError("Profiled support top is below its body surface")

    vertices_mm: list[list[float]] = []
    for x_index, x_value in enumerate(x_values):
        for y_index, y_value in enumerate(y_values):
            vertices_mm.append(
                [
                    float(x_value),
                    float(y_value),
                    bottom_grid[x_index][y_index],
                ]
            )
    top_offset = len(vertices_mm)
    for x_value in x_values:
        for y_value in y_values:
            vertices_mm.append(
                [float(x_value), float(y_value), top_z_mm]
            )

    def grid_index(x_index: int, y_index: int) -> int:
        return x_index * sample_count + y_index

    faces: list[list[int]] = []
    for x_index in range(sample_count - 1):
        for y_index in range(sample_count - 1):
            a = grid_index(x_index, y_index)
            b = grid_index(x_index + 1, y_index)
            c = grid_index(x_index + 1, y_index + 1)
            d = grid_index(x_index, y_index + 1)
            faces.extend(([a, c, b], [a, d, c]))
            faces.extend(
                (
                    [top_offset + a, top_offset + b, top_offset + c],
                    [top_offset + a, top_offset + c, top_offset + d],
                )
            )

    for x_index in range(sample_count - 1):
        low_a = grid_index(x_index, 0)
        low_b = grid_index(x_index + 1, 0)
        high_a = grid_index(x_index, sample_count - 1)
        high_b = grid_index(x_index + 1, sample_count - 1)
        faces.extend(
            (
                [low_a, low_b, top_offset + low_b],
                [low_a, top_offset + low_b, top_offset + low_a],
                [high_a, top_offset + high_b, high_b],
                [high_a, top_offset + high_a, top_offset + high_b],
            )
        )
    for y_index in range(sample_count - 1):
        low_a = grid_index(0, y_index)
        low_b = grid_index(0, y_index + 1)
        high_a = grid_index(sample_count - 1, y_index)
        high_b = grid_index(sample_count - 1, y_index + 1)
        faces.extend(
            (
                [low_a, top_offset + low_b, low_b],
                [low_a, top_offset + low_a, top_offset + low_b],
                [high_a, high_b, top_offset + high_b],
                [high_a, top_offset + high_b, top_offset + high_a],
            )
        )

    mesh = trimesh.Trimesh(
        vertices=np.asarray(vertices_mm, dtype=float) / 1000.0,
        faces=np.asarray(faces, dtype=int),
        process=True,
        validate=True,
    )
    if not mesh.is_watertight:
        raise RuntimeError("Profiled support is not watertight")
    return mesh, bottom_grid


def subtract_cylinders(
    mesh: trimesh.Trimesh,
    cutters: list[trimesh.Trimesh],
) -> trimesh.Trimesh:
    result = mesh
    for cutter in cutters:
        difference = trimesh.boolean.difference(
            [result, cutter],
            engine="manifold",
            check_volume=False,
        )
        if not isinstance(difference, trimesh.Trimesh):
            raise RuntimeError("Cylindrical cut did not return one mesh")
        result = difference
    return result


def annulus_mm(
    outer_diameter_mm: float,
    inner_diameter_mm: float,
    height_mm: float,
    center_mm: list[float],
) -> trimesh.Trimesh:
    outer = cylinder_mm(
        outer_diameter_mm / 2.0,
        height_mm,
        center_mm,
    )
    inner = cylinder_mm(
        inner_diameter_mm / 2.0,
        height_mm + 0.4,
        center_mm,
    )
    result = trimesh.boolean.difference(
        [outer, inner],
        engine="manifold",
        check_volume=False,
    )
    if not isinstance(result, trimesh.Trimesh):
        raise RuntimeError("Receiver annulus Boolean failed")
    return result


def socket_head_screw_mm(
    *,
    x_mm: float,
    y_mm: float,
    bearing_z_mm: float,
    thread_end_z_mm: float,
    direction: str,
) -> trimesh.Trimesh:
    if direction == "up":
        if thread_end_z_mm <= bearing_z_mm:
            raise ValueError("Upward screw must end above its bearing plane")
        shaft_center_z_mm = (
            bearing_z_mm + thread_end_z_mm
        ) / 2.0
        shaft_height_mm = thread_end_z_mm - bearing_z_mm
        head_center_z_mm = bearing_z_mm - M3_HEAD_HEIGHT_MM / 2.0
    elif direction == "down":
        if thread_end_z_mm >= bearing_z_mm:
            raise ValueError("Downward screw must end below its bearing plane")
        shaft_center_z_mm = (
            bearing_z_mm + thread_end_z_mm
        ) / 2.0
        shaft_height_mm = bearing_z_mm - thread_end_z_mm
        head_center_z_mm = bearing_z_mm + M3_HEAD_HEIGHT_MM / 2.0
    else:
        raise ValueError(f"Unsupported screw direction: {direction}")
    return concatenate(
        [
            cylinder_mm(
                M3_SHAFT_DIAMETER_MM / 2.0,
                shaft_height_mm,
                [x_mm, y_mm, shaft_center_z_mm],
            ),
            cylinder_mm(
                M3_HEAD_DIAMETER_MM / 2.0,
                M3_HEAD_HEIGHT_MM,
                [x_mm, y_mm, head_center_z_mm],
            ),
        ]
    )


def derive_camera_front_surface(
    camera: trimesh.Trimesh,
) -> trimesh.Trimesh:
    """Derive the visible black D435 front face from source mesh triangles."""
    face_centers = np.asarray(camera.triangles_center)
    face_normals = np.asarray(camera.face_normals)
    vertex_projection = np.asarray(camera.vertices) @ CAMERA_AXIS_ROBOT
    front_projection = float(np.max(vertex_projection))
    face_projection = face_centers @ CAMERA_AXIS_ROBOT
    front_facing = face_normals @ CAMERA_AXIS_ROBOT
    selected = np.flatnonzero(
        (face_projection >= front_projection - 0.0005)
        & (front_facing >= 0.25)
    )
    if len(selected) == 0:
        raise RuntimeError("Could not derive the D435 front face")
    surface = camera.submesh(
        [selected],
        append=True,
        repair=False,
    )
    if not isinstance(surface, trimesh.Trimesh) or surface.is_empty:
        raise RuntimeError("D435 front-face derivation returned no mesh")
    surface.apply_translation(CAMERA_AXIS_ROBOT * 0.00003)
    return surface


def derive_top_contact_surface(
    sampler: TopSurfaceSampler,
) -> trimesh.Trimesh:
    """Sample a clean display-only upper shell patch for fastener review."""
    x_values = np.linspace(-125.0, 225.0, 71)
    y_values = np.linspace(-54.0, 54.0, 23)
    z_grid = np.full((len(x_values), len(y_values)), np.nan)
    for x_index, x_value in enumerate(x_values):
        for y_index, y_value in enumerate(y_values):
            try:
                sampled_z_mm = sampler.sample_mm(
                    float(x_value),
                    float(y_value),
                )
            except RuntimeError:
                continue
            minimum_shell_z_mm = 385.0 if x_value <= 185.0 else 360.0
            if sampled_z_mm >= minimum_shell_z_mm:
                z_grid[x_index, y_index] = sampled_z_mm

    valid_indices = np.argwhere(np.isfinite(z_grid))
    missing_indices = np.argwhere(~np.isfinite(z_grid))
    if len(valid_indices) == 0:
        raise RuntimeError("Lite3 contact surface has no valid samples")
    if len(missing_indices):
        valid_coordinates = np.asarray(
            [
                [
                    x_values[x_index],
                    y_values[y_index],
                ]
                for x_index, y_index in valid_indices
            ]
        )
        missing_coordinates = np.asarray(
            [
                [
                    x_values[x_index],
                    y_values[y_index],
                ]
                for x_index, y_index in missing_indices
            ]
        )
        nearest_tree = cKDTree(valid_coordinates)
        _, nearest = nearest_tree.query(missing_coordinates, k=1)
        valid_z = np.asarray(
            [
                z_grid[x_index, y_index]
                for x_index, y_index in valid_indices
            ]
        )
        for missing_index, (x_index, y_index) in enumerate(
            missing_indices
        ):
            z_grid[x_index, y_index] = valid_z[nearest[missing_index]]

    vertices_mm: list[list[float]] = []
    for x_index, x_value in enumerate(x_values):
        for y_index, y_value in enumerate(y_values):
            vertices_mm.append(
                [
                    float(x_value),
                    float(y_value),
                    float(z_grid[x_index, y_index]) + 0.03,
                ]
            )

    y_count = len(y_values)
    faces: list[list[int]] = []
    for x_index in range(len(x_values) - 1):
        for y_index in range(y_count - 1):
            first = x_index * y_count + y_index
            next_x = (x_index + 1) * y_count + y_index
            diagonal = next_x + 1
            next_y = first + 1
            faces.extend(
                (
                    [first, next_x, diagonal],
                    [first, diagonal, next_y],
                )
            )
    surface = trimesh.Trimesh(
        vertices=np.asarray(vertices_mm, dtype=float) / 1000.0,
        faces=np.asarray(faces, dtype=int),
        process=False,
        validate=False,
    )
    if surface.is_empty:
        raise RuntimeError("Lite3 contact-surface derivation returned no mesh")
    return surface


def make_interface(
    interface_bottom_z_mm: float,
    deck_contact_z_mm: float,
) -> dict[str, trimesh.Trimesh]:
    body_height_mm = INTERFACE_HEIGHT_MM - 1.7
    body_center_z_mm = interface_bottom_z_mm + body_height_mm / 2.0
    body = rounded_rect_prism(
        INTERFACE_LENGTH_MM / 1000.0,
        INTERFACE_WIDTH_MM / 1000.0,
        body_height_mm / 1000.0,
        INTERFACE_CORNER_RADIUS_MM / 1000.0,
        np.asarray(
            [
                INTERFACE_CENTER_X_MM,
                0.0,
                body_center_z_mm,
            ]
        )
        / 1000.0,
    )

    # The manual line art exposes a shallow central front/underside relief.
    # It is deliberately image-derived rather than claimed as factory CAD.
    relief = box_mm(
        [30.0, 74.0, 7.0],
        [
            INTERFACE_CENTER_X_MM + INTERFACE_LENGTH_MM / 2.0 - 13.0,
            0.0,
            interface_bottom_z_mm + 3.5,
        ],
    )
    body_relieved = trimesh.boolean.difference(
        [body, relief],
        engine="manifold",
    )
    if not isinstance(body_relieved, trimesh.Trimesh):
        raise RuntimeError("Interface relief Boolean did not return one mesh")

    lid = rounded_rect_prism(
        (INTERFACE_LENGTH_MM + 2.0) / 1000.0,
        (INTERFACE_WIDTH_MM + 2.0) / 1000.0,
        1.7 / 1000.0,
        3.0 / 1000.0,
        np.asarray(
            [
                INTERFACE_CENTER_X_MM,
                0.0,
                interface_bottom_z_mm
                + INTERFACE_HEIGHT_MM
                - 0.85,
            ]
        )
        / 1000.0,
    )

    power_ports = concatenate(
        [
            box_mm(
                [4.4, 0.8, 8.5],
                [
                    57.0 + offset,
                    -46.4,
                    interface_bottom_z_mm + 23.5,
                ],
            )
            for offset in (-6.0, 0.0, 6.0)
        ]
    )
    data_ports = concatenate(
        [
            box_mm(
                [11.0, 0.8, 12.0],
                [31.0, -46.4, interface_bottom_z_mm + 23.5],
            ),
            box_mm(
                [17.0, 0.8, 13.0],
                [-53.0, -46.4, interface_bottom_z_mm + 23.5],
            ),
            box_mm(
                [7.0, 0.8, 14.0],
                [-91.0, -46.4, interface_bottom_z_mm + 23.5],
            ),
        ]
    )
    usb3 = box_mm(
        [8.0, 0.8, 14.0],
        [-75.0, -46.4, interface_bottom_z_mm + 23.5],
    )

    vents = concatenate(
        [
            box_mm(
                [0.8, 12.0, 2.2],
                [
                    INTERFACE_CENTER_X_MM
                    - INTERFACE_LENGTH_MM / 2.0
                    - 0.4,
                    y_value,
                    z_value,
                ],
            )
            for z_value in (
                interface_bottom_z_mm + 7.5,
                interface_bottom_z_mm + 12.5,
                interface_bottom_z_mm + 17.5,
                interface_bottom_z_mm + 22.5,
            )
            for y_value in (-24.0, -8.0, 8.0)
        ]
    )
    service_panel = box_mm(
        [20.0, 0.8, 19.0],
        [-61.0, 46.4, interface_bottom_z_mm + 21.5],
    )
    foot_height_mm = interface_bottom_z_mm - deck_contact_z_mm
    if foot_height_mm <= 0.0:
        raise RuntimeError("Interface mounting-pad height is not positive")
    feet_parts: list[trimesh.Trimesh] = []
    interface_fasteners: list[trimesh.Trimesh] = []
    interface_receivers: list[trimesh.Trimesh] = []
    for x_value in INTERFACE_FOOT_AXIS_X_MM:
        for y_value in INTERFACE_FOOT_AXIS_Y_MM:
            foot = cylinder_mm(
                INTERFACE_FOOT_RADIUS_MM,
                foot_height_mm,
                [
                    x_value,
                    y_value,
                    (
                        interface_bottom_z_mm + deck_contact_z_mm
                    )
                    / 2.0,
                ],
            )
            bore = cylinder_mm(
                INTERFACE_M3_CLEARANCE_DIAMETER_MM / 2.0,
                foot_height_mm + 0.8,
                [
                    x_value,
                    y_value,
                    (
                        interface_bottom_z_mm + deck_contact_z_mm
                    )
                    / 2.0,
                ],
            )
            feet_parts.append(subtract_cylinders(foot, [bore]))
            screw_bearing_z_mm = interface_bottom_z_mm + 1.5
            interface_fasteners.append(
                socket_head_screw_mm(
                    x_mm=x_value,
                    y_mm=y_value,
                    bearing_z_mm=screw_bearing_z_mm,
                    thread_end_z_mm=(
                        deck_contact_z_mm
                        - INTERFACE_RECEIVER_DEPTH_MM
                        + 1.0
                    ),
                    direction="down",
                )
            )
            interface_receivers.append(
                annulus_mm(
                    INTERFACE_RECEIVER_OUTER_DIAMETER_MM,
                    INTERFACE_RECEIVER_MINOR_DIAMETER_MM,
                    INTERFACE_RECEIVER_DEPTH_MM,
                    [
                        x_value,
                        y_value,
                        (
                            deck_contact_z_mm
                            - INTERFACE_RECEIVER_DEPTH_MM / 2.0
                        ),
                    ],
                )
            )
    feet = concatenate(feet_parts)
    top_fastener = cylinder_mm(
        2.6,
        0.7,
        [
            -16.0,
            0.0,
            interface_bottom_z_mm + INTERFACE_HEIGHT_MM + 0.35,
        ],
    )
    side_fastener = cylinder_mm(
        2.2,
        0.8,
        [
            89.0,
            46.4,
            interface_bottom_z_mm + 13.0,
        ],
        axis="y",
    )
    end_fasteners = concatenate(
        [
            cylinder_mm(
                2.2,
                0.8,
                [
                    (
                        INTERFACE_CENTER_X_MM
                        - INTERFACE_LENGTH_MM / 2.0
                        - 0.4
                    ),
                    y_value,
                    interface_bottom_z_mm + 10.0,
                ],
                axis="x",
            )
            for y_value in (-35.0, 35.0)
        ]
    )
    return {
        "INTERFACE_BODY": body_relieved,
        "INTERFACE_LID": lid,
        "INTERFACE_PORT_POWER": power_ports,
        "INTERFACE_PORT_DATA": data_ports,
        "INTERFACE_PORT_USB3": usb3,
        "INTERFACE_VENTS": vents,
        "INTERFACE_SERVICE_PANEL": service_panel,
        "INTERFACE_FEET": feet,
        "INTERFACE_M3_FASTENERS": concatenate(interface_fasteners),
        "INTERFACE_RECEIVER_PROXIES": concatenate(interface_receivers),
        "INTERFACE_TOP_FASTENER": top_fastener,
        "INTERFACE_SIDE_FASTENER": side_fastener,
        "INTERFACE_END_FASTENERS": end_fasteners,
    }


def make_j17a_local_mounts(
    sampler: TopSurfaceSampler,
    j17a_seating_z_mm: float,
) -> tuple[dict[str, trimesh.Trimesh], list[dict[str, object]]]:
    """Build four local, independently bolted supports under J17A."""
    support_parts: list[trimesh.Trimesh] = []
    upward_fasteners: list[trimesh.Trimesh] = []
    body_fasteners: list[trimesh.Trimesh] = []
    receiver_proxies: list[trimesh.Trimesh] = []
    support_records: list[dict[str, object]] = []

    for x_value in J17A_AXIS_X_MM:
        for y_value in J17A_AXIS_Y_MM:
            y_direction = -1.0 if y_value < 0.0 else 1.0
            body_axis_y_mm = (
                y_value
                + y_direction
                * J17A_SUPPORT_BODY_FASTENER_Y_OFFSET_MM
            )
            low_center_y_mm = (y_value + body_axis_y_mm) / 2.0
            low_size_y_mm = (
                abs(body_axis_y_mm - y_value)
                + J17A_SUPPORT_FOOT_SIZE_MM
            )
            low_sample_x = np.linspace(
                x_value - J17A_SUPPORT_FOOT_SIZE_MM / 2.0,
                x_value + J17A_SUPPORT_FOOT_SIZE_MM / 2.0,
                J17A_SUPPORT_PROFILE_SAMPLES,
            )
            low_sample_y = np.linspace(
                low_center_y_mm - low_size_y_mm / 2.0,
                low_center_y_mm + low_size_y_mm / 2.0,
                J17A_SUPPORT_PROFILE_SAMPLES,
            )
            low_surface_values = [
                sampler.sample_mm(float(x_sample), float(y_sample))
                for x_sample in low_sample_x
                for y_sample in low_sample_y
            ]
            low_top_z_mm = (
                max(low_surface_values) + J17A_SUPPORT_LOW_HEIGHT_MM
            )
            low_mount, low_bottom_grid = profiled_rect_prism_mm(
                x_value,
                low_center_y_mm,
                J17A_SUPPORT_FOOT_SIZE_MM,
                low_size_y_mm,
                low_top_z_mm,
                sampler,
            )
            main_post, main_bottom_grid = profiled_rect_prism_mm(
                x_value,
                y_value,
                J17A_SUPPORT_MAIN_SIZE_MM,
                J17A_SUPPORT_MAIN_SIZE_MM,
                j17a_seating_z_mm,
                sampler,
            )
            support = trimesh.boolean.union(
                [low_mount, main_post],
                engine="manifold",
                check_volume=False,
            )
            if not isinstance(support, trimesh.Trimesh):
                raise RuntimeError("J17A local-support union failed")

            main_surface_z_mm = sampler.sample_mm(x_value, y_value)
            body_surface_z_mm = sampler.sample_mm(
                x_value,
                body_axis_y_mm,
            )
            upward_bearing_z_mm = (
                main_surface_z_mm
                + J17A_SUPPORT_BOTTOM_CLEARANCE_MM
                + M3_HEAD_HEIGHT_MM
            )
            body_bearing_z_mm = low_top_z_mm - M3_HEAD_HEIGHT_MM
            support_min_z_mm = float(support.bounds[0, 2] * 1000.0)
            support = subtract_cylinders(
                support,
                [
                    cylinder_mm(
                        J17A_M3_CLEARANCE_DIAMETER_MM / 2.0,
                        j17a_seating_z_mm
                        - support_min_z_mm
                        + J17A_SOURCE_THREAD_DEPTH_MM
                        + 2.0,
                        [
                            x_value,
                            y_value,
                            (
                                j17a_seating_z_mm
                                + J17A_SOURCE_THREAD_DEPTH_MM
                                + support_min_z_mm
                                - 2.0
                            )
                            / 2.0,
                        ],
                    ),
                    cylinder_mm(
                        M3_HEAD_DIAMETER_MM / 2.0 + 0.35,
                        upward_bearing_z_mm - support_min_z_mm + 1.0,
                        [
                            x_value,
                            y_value,
                            (
                                upward_bearing_z_mm
                                + support_min_z_mm
                                - 1.0
                            )
                            / 2.0,
                        ],
                    ),
                    cylinder_mm(
                        J17A_M3_CLEARANCE_DIAMETER_MM / 2.0,
                        low_top_z_mm
                        - body_surface_z_mm
                        + INTERFACE_RECEIVER_DEPTH_MM
                        + 2.0,
                        [
                            x_value,
                            body_axis_y_mm,
                            (
                                low_top_z_mm
                                + body_surface_z_mm
                                - INTERFACE_RECEIVER_DEPTH_MM
                            )
                            / 2.0,
                        ],
                    ),
                    cylinder_mm(
                        M3_HEAD_DIAMETER_MM / 2.0 + 0.35,
                        M3_HEAD_HEIGHT_MM + 0.6,
                        [
                            x_value,
                            body_axis_y_mm,
                            low_top_z_mm
                            - M3_HEAD_HEIGHT_MM / 2.0
                            + 0.3,
                        ],
                    ),
                ],
            )
            support_parts.append(support)
            upward_fasteners.append(
                socket_head_screw_mm(
                    x_mm=x_value,
                    y_mm=y_value,
                    bearing_z_mm=upward_bearing_z_mm,
                    thread_end_z_mm=(
                        j17a_seating_z_mm
                        + J17A_SOURCE_THREAD_DEPTH_MM
                    ),
                    direction="up",
                )
            )
            body_fasteners.append(
                socket_head_screw_mm(
                    x_mm=x_value,
                    y_mm=body_axis_y_mm,
                    bearing_z_mm=body_bearing_z_mm,
                    thread_end_z_mm=(
                        body_surface_z_mm
                        - INTERFACE_RECEIVER_DEPTH_MM
                        + 1.0
                    ),
                    direction="down",
                )
            )
            receiver_proxies.append(
                annulus_mm(
                    INTERFACE_RECEIVER_OUTER_DIAMETER_MM,
                    INTERFACE_RECEIVER_MINOR_DIAMETER_MM,
                    INTERFACE_RECEIVER_DEPTH_MM,
                    [
                        x_value,
                        body_axis_y_mm,
                        (
                            body_surface_z_mm
                            - INTERFACE_RECEIVER_DEPTH_MM / 2.0
                        ),
                    ],
                )
            )
            support_records.append(
                {
                    "j17a_axis_mm": [x_value, y_value],
                    "body_fastener_axis_mm": [
                        x_value,
                        body_axis_y_mm,
                    ],
                    "j17a_seating_z_mm": round(
                        j17a_seating_z_mm,
                        6,
                    ),
                    "main_body_surface_z_mm": round(
                        main_surface_z_mm,
                        6,
                    ),
                    "body_fastener_surface_z_mm": round(
                        body_surface_z_mm,
                        6,
                    ),
                    "low_mount_top_z_mm": round(low_top_z_mm, 6),
                    "profiled_bottom_z_range_mm": [
                        round(
                            min(
                                min(row)
                                for row in (
                                    main_bottom_grid
                                    + low_bottom_grid
                                )
                            ),
                            6,
                        ),
                        round(
                            max(
                                max(row)
                                for row in (
                                    main_bottom_grid
                                    + low_bottom_grid
                                )
                            ),
                            6,
                        ),
                    ],
                    "bottom_clearance_mm": (
                        J17A_SUPPORT_BOTTOM_CLEARANCE_MM
                    ),
                }
            )

    return (
        {
            "J17A_LOCAL_SUPPORTS": concatenate(support_parts),
            "J17A_UPWARD_M3_FASTENERS": concatenate(
                upward_fasteners
            ),
            "J17A_BODY_M3_FASTENERS": concatenate(body_fasteners),
            "J17A_BODY_RECEIVER_PROXIES": concatenate(
                receiver_proxies
            ),
        },
        support_records,
    )


def cut_carrier_keepout(
    interface_parts: dict[str, trimesh.Trimesh],
    carrier: trimesh.Trimesh,
) -> dict[str, trimesh.Trimesh]:
    """Cut an image-estimated clearance relief around the carrier candidate."""
    offsets_mm = [
        [0.0, 0.0, 0.0],
        [INTERFACE_CARRIER_CLEARANCE_MM, 0.0, 0.0],
        [-INTERFACE_CARRIER_CLEARANCE_MM, 0.0, 0.0],
        [0.0, INTERFACE_CARRIER_CLEARANCE_MM, 0.0],
        [0.0, -INTERFACE_CARRIER_CLEARANCE_MM, 0.0],
        [0.0, 0.0, INTERFACE_CARRIER_CLEARANCE_MM],
        [0.0, 0.0, -INTERFACE_CARRIER_CLEARANCE_MM],
    ]
    cutters: list[trimesh.Trimesh] = []
    for offset_mm in offsets_mm:
        cutter = carrier.copy()
        cutter.apply_translation(
            np.asarray(offset_mm, dtype=float) / 1000.0
        )
        cutters.append(cutter)
    clearance_cutter = trimesh.boolean.union(
        cutters,
        engine="manifold",
        check_volume=False,
    )
    if not isinstance(clearance_cutter, trimesh.Trimesh):
        raise RuntimeError("Carrier clearance union did not return one mesh")
    for part_name in ("INTERFACE_BODY",):
        result = interface_parts[part_name]
        overlap_extent = (
            np.minimum(result.bounds[1], clearance_cutter.bounds[1])
            - np.maximum(result.bounds[0], clearance_cutter.bounds[0])
        )
        if np.any(overlap_extent <= 0.0):
            continue
        difference = trimesh.boolean.difference(
            [result, clearance_cutter],
            engine="manifold",
            check_volume=False,
        )
        if not isinstance(difference, trimesh.Trimesh):
            raise RuntimeError(
                f"Carrier relief failed for {part_name}"
            )
        volumetric_components = [
            component
            for component in difference.split(only_watertight=False)
            if abs(float(component.volume)) > 1.0e-10
        ]
        if len(volumetric_components) != 1:
            raise RuntimeError(
                f"Carrier relief split {part_name} into "
                f"{len(volumetric_components)} volumetric components"
            )
        cleaned = volumetric_components[0].copy()
        cleaned.process(validate=True)
        if not cleaned.is_watertight:
            raise RuntimeError(
                f"Carrier relief left {part_name} non-watertight"
            )
        interface_parts[part_name] = cleaned
    return interface_parts


def export_mm(
    mesh_m: trimesh.Trimesh,
    path: Path,
) -> dict[str, object]:
    mesh_mm = mesh_m.copy()
    mesh_mm.apply_scale(1000.0)
    mesh_mm.export(path)
    return {
        "path": str(path.resolve()),
        "bounds_mm": np.asarray(mesh_mm.bounds).round(6).tolist(),
        "extent_mm": np.asarray(mesh_mm.extents).round(6).tolist(),
        "vertex_count": int(len(mesh_mm.vertices)),
        "face_count": int(len(mesh_mm.faces)),
        "watertight": bool(mesh_mm.is_watertight),
        "connected_components": (
            int(len(mesh_mm.split(only_watertight=False)))
            if len(mesh_mm.faces) < 500_000
            else None
        ),
        "volume_mm3": (
            round(float(abs(mesh_mm.volume)), 6)
            if mesh_mm.is_watertight
            else None
        ),
    }


def intersection_volume_mm3(
    first: trimesh.Trimesh,
    second: trimesh.Trimesh,
) -> float:
    overlap = trimesh.boolean.intersection(
        [first, second],
        engine="manifold",
        check_volume=False,
    )
    if not isinstance(overlap, trimesh.Trimesh) or len(overlap.faces) == 0:
        return 0.0
    return float(abs(overlap.volume) * 1_000_000_000.0)


def sampled_support_body_clearance_mm(
    supports_m: trimesh.Trimesh,
    sampler: TopSurfaceSampler,
) -> tuple[float, int]:
    """Sample the profiled support underside against the visual top shell."""
    triangles_mm = np.asarray(supports_m.triangles, dtype=float) * 1000.0
    xy = triangles_mm[:, :, :2]
    z = triangles_mm[:, :, 2]
    first = xy[:, 0]
    edge_0 = xy[:, 1] - first
    edge_1 = xy[:, 2] - first
    denominator = (
        edge_0[:, 0] * edge_1[:, 1]
        - edge_1[:, 0] * edge_0[:, 1]
    )
    valid = np.abs(denominator) > 1.0e-12
    clearances: list[float] = []

    for x_center_mm in J17A_AXIS_X_MM:
        for y_center_mm in J17A_AXIS_Y_MM:
            y_direction = -1.0 if y_center_mm < 0.0 else 1.0
            body_axis_y_mm = (
                y_center_mm
                + y_direction
                * J17A_SUPPORT_BODY_FASTENER_Y_OFFSET_MM
            )
            for x_mm in np.linspace(
                x_center_mm - 3.8,
                x_center_mm + 3.8,
                17,
            ):
                for y_mm in np.linspace(
                    min(y_center_mm, body_axis_y_mm) - 3.8,
                    max(y_center_mm, body_axis_y_mm) + 3.8,
                    33,
                ):
                    point = np.asarray([x_mm, y_mm], dtype=float)
                    offset = point - first
                    barycentric_0 = np.zeros(len(xy))
                    barycentric_1 = np.zeros(len(xy))
                    barycentric_0[valid] = (
                        offset[valid, 0] * edge_1[valid, 1]
                        - edge_1[valid, 0] * offset[valid, 1]
                    ) / denominator[valid]
                    barycentric_1[valid] = (
                        edge_0[valid, 0] * offset[valid, 1]
                        - offset[valid, 0] * edge_0[valid, 1]
                    ) / denominator[valid]
                    inside = (
                        valid
                        & (barycentric_0 >= -1.0e-9)
                        & (barycentric_1 >= -1.0e-9)
                        & (
                            barycentric_0 + barycentric_1
                            <= 1.0 + 1.0e-9
                        )
                    )
                    if not np.any(inside):
                        continue
                    intersection_z = (
                        z[inside, 0]
                        + barycentric_0[inside]
                        * (z[inside, 1] - z[inside, 0])
                        + barycentric_1[inside]
                        * (z[inside, 2] - z[inside, 0])
                    )
                    support_bottom_z_mm = float(
                        np.min(intersection_z)
                    )
                    clearances.append(
                        support_bottom_z_mm
                        - sampler.sample_mm(
                            float(x_mm),
                            float(y_mm),
                        )
                    )
    if not clearances:
        raise RuntimeError("No support/body clearance samples were produced")
    return float(np.min(clearances)), len(clearances)


def main() -> None:
    MESH_ROOT.mkdir(parents=True, exist_ok=True)
    MODEL_ROOT.mkdir(parents=True, exist_ok=True)
    direct_manifest = json.loads(
        DIRECT_MANIFEST.read_text(encoding="utf-8")
    )
    direct_camera_contact_mm = float(
        direct_manifest[
            "direct_camera_to_j17a_sampled_minimum_distance_mm"
        ]
    )

    if not MANUAL_POSE_BODY_SOURCE.is_file():
        raise FileNotFoundError(
            "Generate the official manual-pose body first with "
            "assemble_lite3_urdf.py; missing "
            f"{MANUAL_POSE_BODY_SOURCE}"
        )
    full_body = load_mm_as_m(MANUAL_POSE_BODY_SOURCE)
    full_body_ground_normalization_mm = -float(
        full_body.bounds[0, 2] * 1000.0
    )
    full_body.apply_translation(
        np.asarray([0.0, 0.0, full_body_ground_normalization_mm])
        / 1000.0
    )
    top_surface_sampler = TopSurfaceSampler(full_body)
    source_guard = load_mm_as_m(DIRECT_MESH_ROOT / "MID360_GUARD.stl")
    sensor_z_shift_mm = (
        TARGET_GUARD_TOP_MM - float(source_guard.bounds[1, 2] * 1000.0)
    )
    sensor_translation_mm = np.asarray(
        [
            SENSOR_IMAGE_X_SHIFT_MM,
            0.0,
            sensor_z_shift_mm,
        ]
    )
    sensor_translation_m = sensor_translation_mm / 1000.0

    meshes: dict[str, trimesh.Trimesh] = {
        "FULL_LITE3_OFFICIAL_VISUAL": full_body,
        "LITE3_TOP_CONTACT_SURFACE": derive_top_contact_surface(
            top_surface_sampler
        ),
    }
    for source_name in SENSOR_INPUT_NODES:
        output_name = (
            "J17A_SENSOR_CARRIER_CANDIDATE"
            if source_name == "J17A_SENSOR_CARRIER_SOURCE"
            else source_name
        )
        mesh = load_mm_as_m(
            DIRECT_MESH_ROOT / f"{source_name}.stl",
            repair=(source_name == "J17A_SENSOR_CARRIER_SOURCE"),
        )
        mesh.apply_translation(sensor_translation_m)
        meshes[output_name] = mesh

    camera = load_mm_as_m(
        DIRECT_MESH_ROOT / "D435I_CAMERA_DIRECT.stl"
    )
    camera.apply_translation(sensor_translation_m)
    meshes["D435I_CAMERA"] = camera
    meshes["D435_FRONT_FACE_DERIVED"] = derive_camera_front_surface(
        camera
    )
    camera_fasteners = load_mm_as_m(
        DIRECT_MESH_ROOT / "D435_DIRECT_FASTENER_REFERENCES.stl"
    )
    camera_fasteners.apply_translation(sensor_translation_m)
    meshes[
        "D435_DIRECT_FASTENER_REFERENCES"
    ] = camera_fasteners
    interface_bottom_z_mm = (
        INTERFACE_SOURCE_BOTTOM_Z_MM + sensor_z_shift_mm
    )
    interface_contact_samples_mm = [
        top_surface_sampler.sample_mm(x_value, y_value)
        for x_value in INTERFACE_FOOT_AXIS_X_MM
        for y_value in INTERFACE_FOOT_AXIS_Y_MM
    ]
    if np.ptp(interface_contact_samples_mm) > 0.01:
        raise RuntimeError(
            "Interface foot axes do not share one body contact plane: "
            f"{interface_contact_samples_mm}"
        )
    interface_deck_contact_z_mm = float(
        np.max(interface_contact_samples_mm)
    )
    j17a_seating_z_mm = (
        J17A_SOURCE_SEATING_Z_MM + sensor_z_shift_mm
    )
    carrier_mount_parts, carrier_support_records = (
        make_j17a_local_mounts(
            top_surface_sampler,
            j17a_seating_z_mm,
        )
    )
    interface_parts = make_interface(
        interface_bottom_z_mm,
        interface_deck_contact_z_mm,
    )
    carrier_keepout = concatenate(
        [
            meshes["J17A_SENSOR_CARRIER_CANDIDATE"],
            carrier_mount_parts["J17A_LOCAL_SUPPORTS"],
        ]
    )
    interface_parts = cut_carrier_keepout(
        interface_parts,
        carrier_keepout,
    )
    meshes.update(interface_parts)
    meshes.update(carrier_mount_parts)
    support_body_clearance_mm, support_body_sample_count = (
        sampled_support_body_clearance_mm(
            meshes["J17A_LOCAL_SUPPORTS"],
            top_surface_sampler,
        )
    )
    if support_body_clearance_mm < -1.0e-3:
        raise RuntimeError(
            "Profiled J17A supports penetrate the visual body by "
            f"{-support_body_clearance_mm:.6f} mm"
        )

    interface_solid = trimesh.util.concatenate(
        [meshes["INTERFACE_BODY"], meshes["INTERFACE_LID"]]
    )
    j17a = meshes["J17A_SENSOR_CARRIER_CANDIDATE"]
    interface_j17a_overlap_mm3 = sum(
        intersection_volume_mm3(j17a, meshes[name])
        for name in (
            "INTERFACE_BODY",
            "INTERFACE_LID",
        )
    )
    if interface_j17a_overlap_mm3 > 1.0e-6:
        raise RuntimeError(
            "Interface still intersects the candidate carrier: "
            f"{interface_j17a_overlap_mm3:.6f} mm3"
        )
    interface_support_overlap_mm3 = sum(
        intersection_volume_mm3(
            meshes["J17A_LOCAL_SUPPORTS"],
            meshes[name],
        )
        for name in (
            "INTERFACE_BODY",
            "INTERFACE_LID",
        )
    )
    if interface_support_overlap_mm3 > 1.0e-6:
        raise RuntimeError(
            "Interface still intersects the local carrier supports: "
            f"{interface_support_overlap_mm3:.6f} mm3"
        )
    support_camera_overlap_mm3 = intersection_volume_mm3(
        meshes["J17A_LOCAL_SUPPORTS"],
        meshes["D435I_CAMERA"],
    )
    body_fastener_j17a_overlap_mm3 = intersection_volume_mm3(
        meshes["J17A_BODY_M3_FASTENERS"],
        j17a,
    )
    interface_feet_support_overlap_mm3 = intersection_volume_mm3(
        meshes["INTERFACE_FEET"],
        meshes["J17A_LOCAL_SUPPORTS"],
    )
    unintended_mount_overlap_mm3 = (
        support_camera_overlap_mm3
        + body_fastener_j17a_overlap_mm3
        + interface_feet_support_overlap_mm3
    )
    if unintended_mount_overlap_mm3 > 1.0e-6:
        raise RuntimeError(
            "The local mounting chains contain unintended overlap: "
            f"{unintended_mount_overlap_mm3:.6f} mm3"
        )

    guard_top_mm = float(meshes["MID360_GUARD"].bounds[1, 2] * 1000.0)
    if abs(guard_top_mm - TARGET_GUARD_TOP_MM) > 1.0e-6:
        raise RuntimeError(
            f"Guard top {guard_top_mm:.6f} mm misses target"
        )

    entries: list[dict[str, object]] = []
    source_classes = {
        "FULL_LITE3_OFFICIAL_VISUAL": "official_visual",
        "LITE3_TOP_CONTACT_SURFACE": (
            "source_derived_visual_surface"
        ),
        "J17A_SENSOR_CARRIER_CANDIDATE": "related_source_candidate",
        "MID360_ADAPTER": "related_source_candidate",
        "MID360_GUARD": "related_source_candidate",
        "MID360_BODY": "official_visual",
        "MID360_HOUSING_EXTERIOR": "official_visual",
        "MID360_OPTICAL_WINDOW": "official_visual",
        "MID360_CONNECTOR": "official_visual",
        "D435I_CAMERA": "official_visual",
        "D435_FRONT_FACE_DERIVED": (
            "source_derived_visual_material_layer"
        ),
        "D435_DIRECT_FASTENER_REFERENCES": (
            "source_backed_axis_reference"
        ),
        "INTERFACE_M3_FASTENERS": "image_inferred_mechanical_proxy",
        "INTERFACE_RECEIVER_PROXIES": (
            "image_inferred_mechanical_proxy"
        ),
        "J17A_LOCAL_SUPPORTS": "image_inferred_support_geometry",
        "J17A_UPWARD_M3_FASTENERS": (
            "source_axis_mechanical_proxy"
        ),
        "J17A_BODY_M3_FASTENERS": (
            "image_inferred_mechanical_proxy"
        ),
        "J17A_BODY_RECEIVER_PROXIES": (
            "image_inferred_mechanical_proxy"
        ),
    }
    for name, mesh in meshes.items():
        if mesh.is_empty:
            raise RuntimeError(f"Generated empty mesh: {name}")
        evidence_class = source_classes.get(name, "image_estimate")
        metrics = export_mm(mesh, MESH_ROOT / f"{name}.stl")
        entries.append(
            {
                "node_name": name,
                "evidence_class": evidence_class,
                "color_rgba": COLORS[name],
                **metrics,
            }
        )

    reference_meshes = [
        mesh
        for name, mesh in meshes.items()
        if name != "FULL_LITE3_OFFICIAL_VISUAL"
    ]
    all_bounds = np.asarray(
        [mesh.bounds for mesh in [full_body, *reference_meshes]]
    )
    reference_bounds_m = np.asarray(
        [
            np.min(all_bounds[:, 0, :], axis=0),
            np.max(all_bounds[:, 1, :], axis=0),
        ]
    )
    interface_path = MODEL_ROOT / "interface_baseline_candidate.stl"
    interface_mm = interface_solid.copy()
    interface_mm.apply_scale(1000.0)
    interface_mm.export(interface_path)

    manifest = {
        "schema_version": 1,
        "purpose": "official_lite3_lidar_v107_appearance_baseline_review",
        "target_identity": (
            "Lite3 LiDAR assembly shown in official V1.0.7 manual"
        ),
        "primary_evidence": [
            str(OFFICIAL_CURRENT_LIDAR_FRONT_LEFT.resolve()),
            str(
                (
                    REPO_ROOT
                    / "references/upstream/2026-07-24_lite3-design-drawings/"
                    "derived/lite3-lidar-v107-front-render-original.png"
                ).resolve()
            ),
            str(
                (
                    REPO_ROOT
                    / "references/upstream/2026-07-24_lite3-design-drawings/"
                    "derived/lite3-lidar-v107-side-render-original.png"
                ).resolve()
            ),
            str(
                (
                    REPO_ROOT
                    / "references/upstream/2026-07-24_lite3-design-drawings/"
                    "derived/lite3-lidar-v107-rear-line-art-original.png"
                ).resolve()
            ),
            str(
                (
                    REPO_ROOT
                    / "references/upstream/2026-07-24_lite3-design-drawings/"
                    "derived/lite3-lidar-v107-front-line-art-original.png"
                ).resolve()
            ),
        ],
        "source_files": {
            "current_reference_glb": {
                "path": str(CURRENT_GLB.resolve()),
                "sha256": sha256(CURRENT_GLB),
            },
            "related_source_history_glb": {
                "path": str(HISTORY_GLB.resolve()),
                "sha256": sha256(HISTORY_GLB),
            },
            "official_full_body_visual": {
                "path": str(MANUAL_POSE_BODY_SOURCE.resolve()),
                "sha256": sha256(MANUAL_POSE_BODY_SOURCE),
                "source_urdf": str(OFFICIAL_HIGH_RES_URDF.resolve()),
                "hip_y_rad": MANUAL_POSE_HIP_Y_RAD,
                "knee_rad": MANUAL_POSE_KNEE_RAD,
            },
            "related_source_sensor_meshes": {
                "path": str(DIRECT_MESH_ROOT.resolve()),
                "manifest": str(
                    (DIRECT_MESH_ROOT.parent / "manifest.json").resolve()
                ),
            },
            "official_d435_visual_mesh": {
                "path": str(
                    (
                        DIRECT_MESH_ROOT / "D435I_CAMERA_DIRECT.stl"
                    ).resolve()
                ),
                "sha256": sha256(
                    DIRECT_MESH_ROOT / "D435I_CAMERA_DIRECT.stl"
                ),
            },
            "d435_fastener_reference_mesh": {
                "path": str(
                    (
                        DIRECT_MESH_ROOT
                        / "D435_DIRECT_FASTENER_REFERENCES.stl"
                    ).resolve()
                ),
                "sha256": sha256(
                    DIRECT_MESH_ROOT
                    / "D435_DIRECT_FASTENER_REFERENCES.stl"
                ),
            },
            "official_current_lidar_front_left_image": {
                "path": str(
                    OFFICIAL_CURRENT_LIDAR_FRONT_LEFT.resolve()
                ),
                "sha256": sha256(OFFICIAL_CURRENT_LIDAR_FRONT_LEFT),
                "source_record": str(
                    (
                        OFFICIAL_CURRENT_LIDAR_MEDIA_ROOT
                        / "source_record.yaml"
                    ).resolve()
                ),
            },
            "related_source_j17a_step": {
                "path": str(J17A_SOURCE_STEP.resolve()),
                "sha256": sha256(J17A_SOURCE_STEP),
                "drawing": str(J17A_SOURCE_DRAWING.resolve()),
                "drawing_sha256": sha256(J17A_SOURCE_DRAWING),
                "claim": (
                    "The related-source drawing proves four M3 J17A "
                    "robot-side receivers; current-LiDAR identity remains "
                    "a silhouette candidate."
                ),
            },
        },
        "image_estimated_parameters": {
            "sensor_translation_mm_from_related_source_assembly": (
                sensor_translation_mm.round(6).tolist()
            ),
            "camera_translation_mm_from_current_official_mesh_transform": (
                sensor_translation_mm.round(6).tolist()
            ),
            "interface_envelope_mm": [
                INTERFACE_LENGTH_MM,
                INTERFACE_WIDTH_MM,
                INTERFACE_HEIGHT_MM,
            ],
            "interface_center_x_mm": INTERFACE_CENTER_X_MM,
            "interface_bottom_z_mm": round(
                interface_bottom_z_mm,
                6,
            ),
            "interface_corner_radius_mm": INTERFACE_CORNER_RADIUS_MM,
            "interface_deck_contact_z_mm": (
                interface_deck_contact_z_mm
            ),
            "interface_mounting_pad_height_mm": round(
                interface_bottom_z_mm
                - interface_deck_contact_z_mm,
                6,
            ),
            "interface_contact_samples_mm": [
                round(value, 6)
                for value in interface_contact_samples_mm
            ],
            "interface_mounting_chain": {
                "foot_axes_mm": [
                    [x_value, y_value]
                    for x_value in INTERFACE_FOOT_AXIS_X_MM
                    for y_value in INTERFACE_FOOT_AXIS_Y_MM
                ],
                "clearance_hole_diameter_mm": (
                    INTERFACE_M3_CLEARANCE_DIAMETER_MM
                ),
                "receiver_minor_diameter_mm": (
                    INTERFACE_RECEIVER_MINOR_DIAMETER_MM
                ),
                "receiver_depth_mm": INTERFACE_RECEIVER_DEPTH_MM,
                "classification": "image_inferred_mechanical_proxy",
            },
            "j17a_mounting_chain": {
                "source_thread_callout": "4 x M3",
                "source_pattern_mm": [110.0, 86.0],
                "current_axes_mm": [
                    [x_value, y_value]
                    for x_value in J17A_AXIS_X_MM
                    for y_value in J17A_AXIS_Y_MM
                ],
                "source_thread_depth_geometry_mm": (
                    J17A_SOURCE_THREAD_DEPTH_MM
                ),
                "seating_z_mm": round(j17a_seating_z_mm, 6),
                "support_records": carrier_support_records,
                "classification": (
                    "source_axis_plus_image_inferred_local_support"
                ),
            },
            "full_body_ground_normalization_mm": round(
                full_body_ground_normalization_mm,
                6,
            ),
            "manual_pose": {
                "hip_y_rad": MANUAL_POSE_HIP_Y_RAD,
                "knee_rad": MANUAL_POSE_KNEE_RAD,
                "classification": "image_estimate_from_manual_side_view",
            },
            "interface_relief": {
                "size_mm": [30.0, 74.0, 7.0],
                "classification": "image_estimate",
                "carrier_clearance_mm": (
                    INTERFACE_CARRIER_CLEARANCE_MM
                ),
            },
        },
        "validation": {
            "guard_top_mm": round(guard_top_mm, 6),
            "official_standing_height_target_mm": TARGET_GUARD_TOP_MM,
            "interface_to_j17a_intersection_mm3": round(
                interface_j17a_overlap_mm3,
                6,
            ),
            "interface_to_local_support_intersection_mm3": round(
                interface_support_overlap_mm3,
                6,
            ),
            "sampled_local_support_to_body_minimum_clearance_mm": round(
                support_body_clearance_mm,
                6,
            ),
            "sampled_local_support_to_body_sample_count": (
                support_body_sample_count
            ),
            "unintended_mount_overlap_mm3": round(
                unintended_mount_overlap_mm3,
                6,
            ),
            "unintended_mount_overlap_breakdown_mm3": {
                "local_support_to_d435": round(
                    support_camera_overlap_mm3,
                    6,
                ),
                "body_fastener_to_j17a": round(
                    body_fastener_j17a_overlap_mm3,
                    6,
                ),
                "interface_feet_to_local_support": round(
                    interface_feet_support_overlap_mm3,
                    6,
                ),
            },
            "d435_to_j17a_sampled_minimum_distance_mm": (
                direct_camera_contact_mm
            ),
            "d435_contact_metric_note": (
                "Inherited unchanged from the direct-mount evidence candidate "
                "because D435 and J17A receive the same rigid transform."
            ),
            "assembled_reference_bounds_mm": (
                reference_bounds_m * 1000.0
            ).round(6).tolist(),
            "assembled_reference_extents_mm": (
                np.ptp(reference_bounds_m, axis=0) * 1000.0
            ).round(6).tolist(),
        },
        "excluded_rejected_tracks": [
            "BZ20_BACKLOAD_SHELL_SOURCE",
            "AGX_ORIN_BASE_SOURCE",
            "PRO_J17A_TRUSS_ADAPTER",
            "UPPER_DECK_INTERFACE",
            "PAYLOAD_BASE",
            "CAMERA_MOUNT_BRACKET",
            "CAMERA_CARRIER_PLATE",
            "CAMERA_RECEIVER_YOKE",
            "CAMERA_FASTENERS",
            "FACTORY_LIDAR_MOUNTS",
        ],
        "claim_boundary": (
            "This is an evidence-only visible-assembly candidate. Mid-360, "
            "D435, and the Lite3 exterior use source geometry. J17A/J20A/S410 "
            "remain related-source candidates. The J17A four-M3 axes come "
            "from its source STEP and drawing; the visible local supports, "
            "Interface feet, body-side fasteners, and hidden receiver "
            "proxies are explicitly image-inferred mechanical proxies. They "
            "close two inspectable load paths without claiming the unpublished "
            "factory receiver geometry. Physical Lite3 hole positions, thread "
            "engagement, material, and the user's final industrial-PC base "
            "remain measurement gates. This is not factory CAD or "
            "fit-validated hardware."
        ),
        "models": {
            "assembled_fcstd": str(
                (
                    MODEL_ROOT
                    / "lite3_lidar_v107_baseline_candidate.FCStd"
                ).resolve()
            ),
            "interface_stl": str(interface_path.resolve()),
        },
        "entries": entries,
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"manifest={MANIFEST}")
    print(f"interface_model={interface_path}")
    print(f"guard_top_mm={guard_top_mm:.6f}")
    print(
        "interface_to_j17a_intersection_mm3="
        f"{interface_j17a_overlap_mm3:.6f}"
    )
    print(
        "interface_to_local_support_intersection_mm3="
        f"{interface_support_overlap_mm3:.6f}"
    )
    print(
        "sampled_local_support_to_body_minimum_clearance_mm="
        f"{support_body_clearance_mm:.6f}"
    )
    print(
        "unintended_mount_overlap_mm3="
        f"{unintended_mount_overlap_mm3:.6f}"
    )
    print(
        "assembled_extents_mm="
        f"{manifest['validation']['assembled_reference_extents_mm']}"
    )


if __name__ == "__main__":
    main()
