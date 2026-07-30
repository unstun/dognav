#!/usr/bin/env python3
"""Reproduce a rejected Lite3 LiDAR V1.0.7 multiview hypothesis.

Dr Sun rejected this evidence track on 2026-07-26 because the Interface
placement and the surrounding plate, post, support, guard, standoff, and
fastener-head geometry are unsupported reconstructions. Running this script
may reproduce the negative evidence, but its output is not a replica, real
assembly, factory CAD, or print-ready attachment.
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import trimesh


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[2]
OUTPUT_ROOT = (
    TASK_ROOT / "evidence/official-lidar-v107-multiview-replica-candidate"
)
MESH_ROOT = OUTPUT_ROOT / "meshes"
MODEL_ROOT = OUTPUT_ROOT / "models"
MANIFEST = OUTPUT_ROOT / "manifest.json"

BASELINE_MODULE_PATH = (
    TASK_ROOT / "research/prepare_official_lidar_v107_baseline.py"
)
VISIBLE_MODULE_PATH = (
    TASK_ROOT / "research/prepare_official_lidar_v107_visible_replica.py"
)
BODY_SOURCE = (
    TASK_ROOT
    / "evidence/official-lidar-v107-visible-replica-candidate"
    / "models/lite3_official_manual_pose.stl"
)
MID360_CACHE = (
    REPO_ROOT
    / "references/derived/2026-07-24_lite3-lidar-printable-replica"
    / "source_cache/official_sensor_meshes"
)
MID360_STEP = (
    REPO_ROOT
    / "references/upstream/2026-07-24_livox-mid360-cad"
    / "source/original/mid-360-asm.stp"
)
D435_DAE = (
    REPO_ROOT
    / "references/upstream/2026-07-25_realsense-d435i-ros-mesh"
    / "source/original/d435.dae"
)
DESIGN_DRAWING_ROOT = (
    REPO_ROOT
    / "references/upstream/2026-07-24_lite3-design-drawings/derived"
)
OFFICIAL_MEDIA_ROOT = (
    REPO_ROOT
    / "references/upstream/2026-07-26_lite3-current-lidar-official-us-media"
)

# Robot frame: +X front, +Y left, +Z up.  These values are registered against
# the official V1.0.7 front/side/rear views and are not factory dimensions.
BASE_PLATE_CENTER_MM = np.asarray([144.5, 0.0, 400.25])
BASE_PLATE_SIZE_MM = np.asarray([163.0, 112.0, 3.5])
BASE_PLATE_RADIUS_MM = 7.0
BASE_STANDOFF_AXES_MM = (
    (76.0, -46.0),
    (76.0, 46.0),
    (210.0, -46.0),
    (210.0, 46.0),
)
BASE_STANDOFF_RADIUS_MM = 6.0

TILT_DEG = 15.0
TILT_PLATE_MOUNT_CENTER_MM = np.asarray([145.0, 0.0, 421.0])
TILT_PLATE_SIZE_MM = np.asarray([96.0, 82.0, 4.0])
TILT_PLATE_RADIUS_MM = 3.0
POST_U_AXES_MM = (-37.0, 37.0)
POST_V_AXES_MM = (-34.0, 34.0)
POST_SECTION_MM = 12.0

CAMERA_FRONT_ORIGIN_MM = np.asarray([216.5, 0.0, 416.5])
CAMERA_TILT_DEG = 20.0
CAMERA_REAR_PLATE_LOCAL_Z_MM = -27.05
CAMERA_REAR_PLATE_SIZE_MM = np.asarray([72.0, 18.0, 4.0])
CAMERA_SUPPORT_Y_MM = (-30.0, 30.0)
CAMERA_SUPPORT_SECTION_MM = 9.0

GUARD_STRAP_MM = 5.0
GUARD_XZ_RADIUS_MM = 43.0
GUARD_YZ_RADIUS_MM = 34.0
GUARD_CENTERLINE_TOP_NORMAL_MM = 73.55
GUARD_BASE_CENTER_NORMAL_MM = GUARD_STRAP_MM / 2.0
GUARD_CROSSBAR_NORMAL_MM = 35.0

INTERFACE_LENGTH_MM = 218.0
INTERFACE_CENTER_X_MM = -57.0
TARGET_STANDING_HEIGHT_MM = 496.0

COLORS = {
    "FULL_LITE3_OFFICIAL_VISUAL": [210, 214, 220, 255],
    "LITE3_TOP_CONTACT_SURFACE": [205, 209, 214, 255],
    "FACTORY_SENSOR_BASE_PLATE": [205, 207, 210, 255],
    "FACTORY_SENSOR_BASE_STANDOFFS": [132, 135, 140, 255],
    "FACTORY_SENSOR_TILTED_PLATE": [152, 155, 160, 255],
    "FACTORY_SENSOR_UNEQUAL_POSTS": [135, 138, 143, 255],
    "FACTORY_D435_REAR_PLATE": [177, 180, 184, 255],
    "FACTORY_D435_SUPPORT_POSTS": [135, 138, 143, 255],
    "FACTORY_GUARD_XZ_STRAP": [34, 36, 40, 255],
    "FACTORY_GUARD_YZ_STRAP": [34, 36, 40, 255],
    "FACTORY_GUARD_CROSSBARS": [34, 36, 40, 255],
    "FACTORY_GUARD_TOP_CAP": [34, 36, 40, 255],
    "FACTORY_VISIBLE_MOUNT_FASTENER_HEADS": [61, 64, 69, 255],
    "MID360_BODY": [159, 162, 166, 255],
    "MID360_HOUSING_EXTERIOR": [165, 168, 172, 255],
    "MID360_OPTICAL_WINDOW": [14, 61, 132, 255],
    "MID360_CONNECTOR": [30, 31, 34, 255],
    "D435I_CAMERA": [205, 207, 210, 255],
    "D435_FRONT_FACE_DERIVED": [28, 29, 32, 255],
    "INTERFACE_BODY": [224, 225, 226, 255],
    "INTERFACE_LID": [235, 236, 237, 255],
    "INTERFACE_PORT_POWER": [200, 137, 39, 255],
    "INTERFACE_PORT_DATA": [30, 32, 35, 255],
    "INTERFACE_PORT_USB3": [43, 90, 145, 255],
    "INTERFACE_VENTS": [52, 54, 57, 255],
    "INTERFACE_SERVICE_PANEL": [111, 113, 117, 255],
    "INTERFACE_VISIBLE_FEET": [105, 108, 112, 255],
    "INTERFACE_TOP_FASTENER_HEAD": [70, 72, 75, 255],
    "INTERFACE_SIDE_FASTENER_HEAD": [70, 72, 75, 255],
    "INTERFACE_END_FASTENER_HEADS": [70, 72, 75, 255],
}


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load helpers from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def transform_from_rotation_translation(
    rotation: np.ndarray,
    translation_m: np.ndarray,
) -> np.ndarray:
    transform = np.eye(4)
    transform[:3, :3] = rotation
    transform[:3, 3] = translation_m
    return transform


def tilted_frame() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    angle = math.radians(TILT_DEG)
    forward_down = np.asarray(
        [math.cos(angle), 0.0, -math.sin(angle)]
    )
    left = np.asarray([0.0, 1.0, 0.0])
    normal = np.asarray(
        [math.sin(angle), 0.0, math.cos(angle)]
    )
    return forward_down, left, normal


def oriented_box(
    extents_mm: np.ndarray,
    center_mm: np.ndarray,
    rotation: np.ndarray,
) -> trimesh.Trimesh:
    mesh = trimesh.creation.box(
        extents=np.asarray(extents_mm, dtype=float) / 1000.0
    )
    mesh.apply_transform(
        transform_from_rotation_translation(
            rotation,
            np.asarray(center_mm, dtype=float) / 1000.0,
        )
    )
    return mesh


def rectangular_strap_between(
    start_mm: np.ndarray,
    end_mm: np.ndarray,
    section_mm: float,
) -> trimesh.Trimesh:
    start = np.asarray(start_mm, dtype=float)
    end = np.asarray(end_mm, dtype=float)
    vector = end - start
    length = float(np.linalg.norm(vector))
    if length <= 1.0e-9:
        raise ValueError("Zero-length guard strap segment")
    x_axis = vector / length
    helper = np.asarray([0.0, 0.0, 1.0])
    if abs(float(np.dot(x_axis, helper))) > 0.94:
        helper = np.asarray([0.0, 1.0, 0.0])
    y_axis = np.cross(helper, x_axis)
    y_axis /= np.linalg.norm(y_axis)
    z_axis = np.cross(x_axis, y_axis)
    rotation = np.column_stack((x_axis, y_axis, z_axis))
    return oriented_box(
        np.asarray([length, section_mm, section_mm]),
        (start + end) / 2.0,
        rotation,
    )


def strap_polyline(points_mm: list[np.ndarray]) -> trimesh.Trimesh:
    return trimesh.util.concatenate(
        [
            rectangular_strap_between(
                points_mm[index],
                points_mm[index + 1],
                GUARD_STRAP_MM,
            )
            for index in range(len(points_mm) - 1)
        ]
    )


def cylinder_along(
    radius_mm: float,
    height_mm: float,
    center_mm: np.ndarray,
    axis: np.ndarray,
) -> trimesh.Trimesh:
    z_axis = np.asarray(axis, dtype=float)
    z_axis /= np.linalg.norm(z_axis)
    helper = np.asarray([0.0, 1.0, 0.0])
    if abs(float(np.dot(z_axis, helper))) > 0.94:
        helper = np.asarray([1.0, 0.0, 0.0])
    x_axis = np.cross(helper, z_axis)
    x_axis /= np.linalg.norm(x_axis)
    y_axis = np.cross(z_axis, x_axis)
    rotation = np.column_stack((x_axis, y_axis, z_axis))
    mesh = trimesh.creation.cylinder(
        radius=radius_mm / 1000.0,
        height=height_mm / 1000.0,
        sections=48,
    )
    mesh.apply_transform(
        transform_from_rotation_translation(
            rotation,
            np.asarray(center_mm, dtype=float) / 1000.0,
        )
    )
    return mesh


def load_mid360_part(path: Path) -> trimesh.Trimesh:
    mesh = trimesh.load_mesh(
        path,
        process=False,
        maintain_order=True,
    )
    mesh.apply_scale(0.001)
    angle = math.radians(TILT_DEG)
    rotation = np.asarray(
        [
            [-math.cos(angle), math.sin(angle), 0.0],
            [0.0, 0.0, 1.0],
            [math.sin(angle), math.cos(angle), 0.0],
        ]
    )
    source_mount_center_m = np.asarray(
        [0.0, -25.9171, 0.0]
    ) / 1000.0
    target_mount_center_m = TILT_PLATE_MOUNT_CENTER_MM / 1000.0
    translation_m = (
        target_mount_center_m - rotation @ source_mount_center_m
    )
    mesh.apply_transform(
        transform_from_rotation_translation(rotation, translation_m)
    )
    return mesh


def load_d435() -> tuple[trimesh.Trimesh, np.ndarray]:
    scene = trimesh.load(D435_DAE, force="scene", process=False)
    if not isinstance(scene, trimesh.Scene):
        raise RuntimeError("Official D435 source did not load as a scene")
    camera = scene.to_geometry()
    angle = math.radians(CAMERA_TILT_DEG)
    rotation = np.asarray(
        [
            [0.0, math.sin(angle), math.cos(angle)],
            [1.0, 0.0, 0.0],
            [0.0, math.cos(angle), -math.sin(angle)],
        ]
    )
    camera.apply_transform(
        transform_from_rotation_translation(
            rotation,
            CAMERA_FRONT_ORIGIN_MM / 1000.0,
        )
    )
    return camera, rotation


def make_mount_geometry(base):
    forward_down, left, normal = tilted_frame()
    rotation = np.column_stack((forward_down, left, normal))

    base_plate = base.rounded_rect_prism(
        BASE_PLATE_SIZE_MM[0] / 1000.0,
        BASE_PLATE_SIZE_MM[1] / 1000.0,
        BASE_PLATE_SIZE_MM[2] / 1000.0,
        BASE_PLATE_RADIUS_MM / 1000.0,
        BASE_PLATE_CENTER_MM / 1000.0,
    )
    plate_top_z = float(
        BASE_PLATE_CENTER_MM[2] + BASE_PLATE_SIZE_MM[2] / 2.0
    )
    plate_bottom_z = float(
        BASE_PLATE_CENTER_MM[2] - BASE_PLATE_SIZE_MM[2] / 2.0
    )

    tilted_plate_center = (
        TILT_PLATE_MOUNT_CENTER_MM
        - normal * (TILT_PLATE_SIZE_MM[2] / 2.0)
    )
    tilted_plate = base.rounded_rect_prism(
        TILT_PLATE_SIZE_MM[0] / 1000.0,
        TILT_PLATE_SIZE_MM[1] / 1000.0,
        TILT_PLATE_SIZE_MM[2] / 1000.0,
        TILT_PLATE_RADIUS_MM / 1000.0,
        np.zeros(3),
    )
    tilted_plate.apply_transform(
        transform_from_rotation_translation(
            rotation,
            tilted_plate_center / 1000.0,
        )
    )

    posts: list[trimesh.Trimesh] = []
    post_metrics = []
    for u_value in POST_U_AXES_MM:
        for v_value in POST_V_AXES_MM:
            plane_bottom = (
                TILT_PLATE_MOUNT_CENTER_MM
                + forward_down * u_value
                + left * v_value
                - normal * TILT_PLATE_SIZE_MM[2]
            )
            post_height = float(plane_bottom[2] - plate_top_z)
            if post_height <= 1.0:
                raise RuntimeError("Official-view post height is not positive")
            center = np.asarray(
                [
                    plane_bottom[0],
                    plane_bottom[1],
                    plate_top_z + post_height / 2.0,
                ]
            )
            posts.append(
                base.box_mm(
                    [
                        POST_SECTION_MM,
                        POST_SECTION_MM,
                        post_height,
                    ],
                    center.tolist(),
                )
            )
            post_metrics.append(
                {
                    "u_mm": u_value,
                    "v_mm": v_value,
                    "height_mm": post_height,
                    "top_center_mm": plane_bottom.tolist(),
                }
            )

    xz_straight_normal = (
        GUARD_CENTERLINE_TOP_NORMAL_MM - GUARD_XZ_RADIUS_MM
    )
    yz_straight_normal = (
        GUARD_CENTERLINE_TOP_NORMAL_MM - GUARD_YZ_RADIUS_MM
    )
    xz_points_local: list[tuple[float, float, float]] = [
        (
            -GUARD_XZ_RADIUS_MM,
            0.0,
            GUARD_BASE_CENTER_NORMAL_MM,
        ),
        (-GUARD_XZ_RADIUS_MM, 0.0, xz_straight_normal),
    ]
    for index in range(1, 25):
        angle = math.pi - math.pi * index / 24.0
        xz_points_local.append(
            (
                GUARD_XZ_RADIUS_MM * math.cos(angle),
                0.0,
                xz_straight_normal
                + GUARD_XZ_RADIUS_MM * math.sin(angle),
            )
        )
    xz_points_local.append(
        (
            GUARD_XZ_RADIUS_MM,
            0.0,
            GUARD_BASE_CENTER_NORMAL_MM,
        )
    )
    yz_points_local: list[tuple[float, float, float]] = [
        (
            0.0,
            -GUARD_YZ_RADIUS_MM,
            GUARD_BASE_CENTER_NORMAL_MM,
        ),
        (0.0, -GUARD_YZ_RADIUS_MM, yz_straight_normal),
    ]
    for index in range(1, 25):
        angle = math.pi - math.pi * index / 24.0
        yz_points_local.append(
            (
                0.0,
                GUARD_YZ_RADIUS_MM * math.cos(angle),
                yz_straight_normal
                + GUARD_YZ_RADIUS_MM * math.sin(angle),
            )
        )
    yz_points_local.append(
        (
            0.0,
            GUARD_YZ_RADIUS_MM,
            GUARD_BASE_CENTER_NORMAL_MM,
        )
    )

    def world(local: tuple[float, float, float]) -> np.ndarray:
        u_value, v_value, n_value = local
        return (
            TILT_PLATE_MOUNT_CENTER_MM
            + forward_down * u_value
            + left * v_value
            + normal * n_value
        )

    guard_xz = strap_polyline([world(point) for point in xz_points_local])
    guard_yz = strap_polyline([world(point) for point in yz_points_local])
    guard_crossbars = trimesh.util.concatenate(
        [
            rectangular_strap_between(
                world(
                    (
                        -GUARD_XZ_RADIUS_MM,
                        0.0,
                        GUARD_CROSSBAR_NORMAL_MM,
                    )
                ),
                world(
                    (
                        GUARD_XZ_RADIUS_MM,
                        0.0,
                        GUARD_CROSSBAR_NORMAL_MM,
                    )
                ),
                GUARD_STRAP_MM,
            ),
            rectangular_strap_between(
                world(
                    (
                        0.0,
                        -GUARD_YZ_RADIUS_MM,
                        GUARD_CROSSBAR_NORMAL_MM,
                    )
                ),
                world(
                    (
                        0.0,
                        GUARD_YZ_RADIUS_MM,
                        GUARD_CROSSBAR_NORMAL_MM,
                    )
                ),
                GUARD_STRAP_MM,
            ),
        ]
    )
    guard_top_cap = cylinder_along(
        6.0,
        3.0,
        world((0.0, 0.0, GUARD_CENTERLINE_TOP_NORMAL_MM - 0.75)),
        normal,
    )

    upper_heads = [
        cylinder_along(
            2.7,
            0.8,
            (
                TILT_PLATE_MOUNT_CENTER_MM
                + forward_down * u_value
                + left * v_value
                + normal * 0.4
            ),
            normal,
        )
        for u_value in POST_U_AXES_MM
        for v_value in POST_V_AXES_MM
    ]
    lower_heads = [
        base.cylinder_mm(
            3.0,
            0.8,
            [x_value, y_value, plate_top_z + 0.4],
        )
        for x_value, y_value in BASE_STANDOFF_AXES_MM
    ]

    return {
        "FACTORY_SENSOR_BASE_PLATE": base_plate,
        "FACTORY_SENSOR_TILTED_PLATE": tilted_plate,
        "FACTORY_SENSOR_UNEQUAL_POSTS": (
            trimesh.util.concatenate(posts)
        ),
        "FACTORY_GUARD_XZ_STRAP": guard_xz,
        "FACTORY_GUARD_YZ_STRAP": guard_yz,
        "FACTORY_GUARD_CROSSBARS": guard_crossbars,
        "FACTORY_GUARD_TOP_CAP": guard_top_cap,
        "FACTORY_VISIBLE_MOUNT_FASTENER_HEADS": (
            trimesh.util.concatenate(upper_heads + lower_heads)
        ),
    }, {
        "plate_top_z_mm": plate_top_z,
        "plate_bottom_z_mm": plate_bottom_z,
        "post_metrics": post_metrics,
        "tilted_frame_forward_down": forward_down.tolist(),
        "tilted_frame_left": left.tolist(),
        "tilted_frame_normal": normal.tolist(),
    }


def make_camera_bracket(
    base,
    camera_rotation: np.ndarray,
    plate_top_z_mm: float,
) -> tuple[dict[str, trimesh.Trimesh], dict[str, object]]:
    local_center = np.asarray(
        [0.0, 0.0, CAMERA_REAR_PLATE_LOCAL_Z_MM]
    )
    rear_plate_center = (
        CAMERA_FRONT_ORIGIN_MM + camera_rotation @ local_center
    )
    rear_plate = oriented_box(
        CAMERA_REAR_PLATE_SIZE_MM,
        rear_plate_center,
        camera_rotation,
    )
    local_bottom = np.asarray(
        [
            0.0,
            -CAMERA_REAR_PLATE_SIZE_MM[1] / 2.0,
            CAMERA_REAR_PLATE_LOCAL_Z_MM,
        ]
    )
    bracket_bottom_world = (
        CAMERA_FRONT_ORIGIN_MM + camera_rotation @ local_bottom
    )
    support_height = float(bracket_bottom_world[2] - plate_top_z_mm)
    if support_height <= 1.0:
        raise RuntimeError("D435 visible support height is not positive")
    supports = trimesh.util.concatenate(
        [
            base.box_mm(
                [
                    CAMERA_SUPPORT_SECTION_MM,
                    CAMERA_SUPPORT_SECTION_MM,
                    support_height,
                ],
                [
                    bracket_bottom_world[0],
                    y_value,
                    plate_top_z_mm + support_height / 2.0,
                ],
            )
            for y_value in CAMERA_SUPPORT_Y_MM
        ]
    )

    camera_axis = camera_rotation[:, 2]
    screw_centers = [
        CAMERA_FRONT_ORIGIN_MM
        + camera_rotation
        @ np.asarray(
            [
                x_value,
                0.0,
                CAMERA_REAR_PLATE_LOCAL_Z_MM - 2.35,
            ]
        )
        for x_value in (-22.5, 22.5)
    ]
    screw_heads = trimesh.util.concatenate(
        [
            cylinder_along(
                2.6,
                0.9,
                center,
                camera_axis,
            )
            for center in screw_centers
        ]
    )
    return {
        "FACTORY_D435_REAR_PLATE": rear_plate,
        "FACTORY_D435_SUPPORT_POSTS": supports,
        "FACTORY_VISIBLE_MOUNT_FASTENER_HEADS": screw_heads,
    }, {
        "camera_rear_plate_center_mm": rear_plate_center.tolist(),
        "camera_support_height_mm": support_height,
        "camera_screw_head_centers_mm": [
            center.tolist() for center in screw_centers
        ],
        "camera_axis_robot": camera_axis.tolist(),
    }


def main() -> None:
    base = load_module(
        BASELINE_MODULE_PATH,
        "official_lidar_v107_baseline_helpers",
    )
    visible = load_module(
        VISIBLE_MODULE_PATH,
        "official_lidar_v107_visible_helpers",
    )
    MESH_ROOT.mkdir(parents=True, exist_ok=True)
    MODEL_ROOT.mkdir(parents=True, exist_ok=True)
    if not BODY_SOURCE.is_file():
        raise FileNotFoundError(BODY_SOURCE)

    full_body = base.load_mm_as_m(BODY_SOURCE)
    ground_normalization_mm = -float(full_body.bounds[0, 2] * 1000.0)
    full_body.apply_translation(
        np.asarray([0.0, 0.0, ground_normalization_mm]) / 1000.0
    )
    sampler = base.TopSurfaceSampler(full_body)
    deck_contact_z_mm = float(
        np.max(
            [
                sampler.sample_mm(x_value, y_value)
                for x_value in visible.INTERFACE_FOOT_X_MM
                for y_value in visible.INTERFACE_FOOT_Y_MM
            ]
        )
    )

    meshes: dict[str, trimesh.Trimesh] = {
        "FULL_LITE3_OFFICIAL_VISUAL": full_body,
        "LITE3_TOP_CONTACT_SURFACE": base.derive_top_contact_surface(sampler),
    }
    mount_meshes, mount_metrics = make_mount_geometry(base)
    meshes.update(mount_meshes)

    plate_bottom_z_mm = float(mount_metrics["plate_bottom_z_mm"])
    standoffs: list[trimesh.Trimesh] = []
    standoff_metrics = []
    for x_value, y_value in BASE_STANDOFF_AXES_MM:
        body_top_z_mm = float(sampler.sample_mm(x_value, y_value))
        height_mm = plate_bottom_z_mm - body_top_z_mm
        if height_mm <= 0.5:
            raise RuntimeError("Sensor base visible standoff is not positive")
        standoffs.append(
            base.cylinder_mm(
                BASE_STANDOFF_RADIUS_MM,
                height_mm,
                [
                    x_value,
                    y_value,
                    body_top_z_mm + height_mm / 2.0,
                ],
            )
        )
        standoff_metrics.append(
            {
                "axis_mm": [x_value, y_value],
                "body_top_z_mm": body_top_z_mm,
                "height_mm": height_mm,
            }
        )
    meshes["FACTORY_SENSOR_BASE_STANDOFFS"] = (
        trimesh.util.concatenate(standoffs)
    )

    mid360_paths = {
        "MID360_BODY": MID360_CACHE / "mid360_body_official.stl",
        "MID360_HOUSING_EXTERIOR": (
            MID360_CACHE / "mid360_housing_exterior_official.stl"
        ),
        "MID360_OPTICAL_WINDOW": (
            MID360_CACHE / "mid360_optical_window_official.stl"
        ),
        "MID360_CONNECTOR": (
            MID360_CACHE / "mid360_connector_official.stl"
        ),
    }
    for node_name, path in mid360_paths.items():
        meshes[node_name] = load_mid360_part(path)

    camera, camera_rotation = load_d435()
    meshes["D435I_CAMERA"] = camera
    meshes["D435_FRONT_FACE_DERIVED"] = (
        base.derive_camera_front_surface(camera)
    )
    camera_meshes, camera_metrics = make_camera_bracket(
        base,
        camera_rotation,
        float(mount_metrics["plate_top_z_mm"]),
    )
    camera_fasteners = camera_meshes.pop(
        "FACTORY_VISIBLE_MOUNT_FASTENER_HEADS"
    )
    meshes.update(camera_meshes)
    meshes["FACTORY_VISIBLE_MOUNT_FASTENER_HEADS"] = (
        trimesh.util.concatenate(
            [
                meshes["FACTORY_VISIBLE_MOUNT_FASTENER_HEADS"],
                camera_fasteners,
            ]
        )
    )

    meshes.update(visible.make_visible_interface(base, deck_contact_z_mm))

    forbidden_node_fragments = ("J17A", "J20A", "S410")
    if any(
        fragment in node_name
        for node_name in meshes
        for fragment in forbidden_node_fragments
    ):
        raise RuntimeError("Rejected adaptation geometry entered replica scene")

    evidence_classes = {
        "FULL_LITE3_OFFICIAL_VISUAL": "official_visual",
        "LITE3_TOP_CONTACT_SURFACE": "source_derived_visual_surface",
        "FACTORY_SENSOR_BASE_PLATE": "official_multiview_image_estimate",
        "FACTORY_SENSOR_BASE_STANDOFFS": (
            "official_visible_contact_image_estimate"
        ),
        "FACTORY_SENSOR_TILTED_PLATE": (
            "official_multiview_image_estimate"
        ),
        "FACTORY_SENSOR_UNEQUAL_POSTS": (
            "official_multiview_image_estimate"
        ),
        "FACTORY_D435_REAR_PLATE": (
            "official_multiview_image_estimate"
        ),
        "FACTORY_D435_SUPPORT_POSTS": (
            "official_multiview_image_estimate"
        ),
        "FACTORY_GUARD_XZ_STRAP": "official_multiview_image_estimate",
        "FACTORY_GUARD_YZ_STRAP": "official_multiview_image_estimate",
        "FACTORY_GUARD_CROSSBARS": "official_multiview_image_estimate",
        "FACTORY_GUARD_TOP_CAP": "official_visible_surface_feature",
        "FACTORY_VISIBLE_MOUNT_FASTENER_HEADS": (
            "official_visible_surface_feature"
        ),
        "MID360_BODY": "manufacturer_cad_exterior",
        "MID360_HOUSING_EXTERIOR": "manufacturer_cad_exterior",
        "MID360_OPTICAL_WINDOW": "manufacturer_cad_exterior",
        "MID360_CONNECTOR": "manufacturer_cad_exterior",
        "D435I_CAMERA": "manufacturer_ros_visual_mesh",
        "D435_FRONT_FACE_DERIVED": (
            "source_derived_visual_material_layer"
        ),
        "INTERFACE_BODY": "official_multiview_image_estimate",
        "INTERFACE_LID": "official_multiview_image_estimate",
        "INTERFACE_PORT_POWER": "official_visible_image_estimate",
        "INTERFACE_PORT_DATA": "official_visible_image_estimate",
        "INTERFACE_PORT_USB3": "official_visible_image_estimate",
        "INTERFACE_VENTS": "official_visible_image_estimate",
        "INTERFACE_SERVICE_PANEL": "official_visible_image_estimate",
        "INTERFACE_VISIBLE_FEET": "official_visible_image_estimate",
        "INTERFACE_TOP_FASTENER_HEAD": (
            "official_visible_surface_feature"
        ),
        "INTERFACE_SIDE_FASTENER_HEAD": (
            "official_visible_surface_feature"
        ),
        "INTERFACE_END_FASTENER_HEADS": (
            "official_visible_surface_feature"
        ),
    }
    entries = []
    for name, mesh in meshes.items():
        if mesh.is_empty:
            raise RuntimeError(f"Generated empty mesh: {name}")
        metrics = base.export_mm(mesh, MESH_ROOT / f"{name}.stl")
        entries.append(
            {
                "node_name": name,
                "evidence_class": evidence_classes[name],
                "color_rgba": COLORS[name],
                **metrics,
            }
        )

    guard_names = (
        "FACTORY_GUARD_XZ_STRAP",
        "FACTORY_GUARD_YZ_STRAP",
        "FACTORY_GUARD_TOP_CAP",
    )
    guard_top_mm = max(
        float(meshes[name].bounds[1, 2] * 1000.0)
        for name in guard_names
    )
    carrier_rear_x_mm = float(
        meshes["FACTORY_SENSOR_BASE_PLATE"].bounds[0, 0] * 1000.0
    )
    interface_front_x_mm = (
        INTERFACE_CENTER_X_MM + INTERFACE_LENGTH_MM / 2.0
    )
    visible_gap_mm = carrier_rear_x_mm - interface_front_x_mm
    if abs(guard_top_mm - TARGET_STANDING_HEIGHT_MM) > 1.0:
        raise RuntimeError(
            f"Guard top {guard_top_mm:.3f} mm misses the 496 mm envelope"
        )
    if visible_gap_mm <= 0.0:
        raise RuntimeError("Interface overlaps visible sensor carrier in X")

    source_paths = {
        "official_front_render": (
            DESIGN_DRAWING_ROOT / "lite3-lidar-v107-front-render-original.png"
        ),
        "official_side_render": (
            DESIGN_DRAWING_ROOT / "lite3-lidar-v107-side-render-original.png"
        ),
        "official_front_line_art": (
            DESIGN_DRAWING_ROOT
            / "lite3-lidar-v107-front-line-art-original.png"
        ),
        "official_rear_line_art": (
            DESIGN_DRAWING_ROOT
            / "lite3-lidar-v107-rear-line-art-original.png"
        ),
        "official_current_studio": (
            OFFICIAL_MEDIA_ROOT
            / "source/original/lite3-lidar-current-studio-2048x2048.jpg"
        ),
        "official_current_studio_alt": (
            OFFICIAL_MEDIA_ROOT
            / "source/original/lite3-lidar-current-studio-alt-2048x2048.jpg"
        ),
        "livox_mid360_step": MID360_STEP,
        "realsense_d435_ros_mesh": D435_DAE,
        "lite3_manual_pose_body": BODY_SOURCE,
    }
    manifest = {
        "schema_version": 1,
        "purpose": (
            "rejected_lite3_lidar_v107_multiview_reconstruction_evidence"
        ),
        "status": "rejected_by_dr_sun_2026_07_26",
        "claim_boundary": (
            "Rejected negative evidence. The Interface placement and all "
            "surrounding plate, post, support, guard, standoff, and "
            "fastener-head geometry are unsupported reconstructions. This "
            "is not a replica, real assembly, factory CAD, or print-ready "
            "attachment."
        ),
        "replica_identity": {
            "imported_bracket_geometry": [],
            "forbidden_imports": [
                "J17A carrier",
                "J20A adapter",
                "S410 guard",
            ],
            "manufacturer_sensor_geometry": [
                "Livox Mid-360 exterior CAD",
                "RealSense D435 ROS visual mesh",
            ],
            "image_reconstructed_parts": [
                "local lower sensor plate",
                "four unequal short posts",
                "down-tilted upper sensor plate",
                "D435 rear plate and visible supports",
                "two orthogonal guard straps and crossbars",
                "visible surface fastener heads",
                "Interface enclosure visible exterior",
            ],
        },
        "source_files": {
            name: {
                "path": str(path.resolve()),
                "sha256": base.sha256(path),
            }
            for name, path in source_paths.items()
        },
        "image_registered_parameters": {
            "base_plate_center_mm": BASE_PLATE_CENTER_MM.tolist(),
            "base_plate_size_mm": BASE_PLATE_SIZE_MM.tolist(),
            "base_standoffs": standoff_metrics,
            "tilt_deg": TILT_DEG,
            "tilt_plate_mount_center_mm": (
                TILT_PLATE_MOUNT_CENTER_MM.tolist()
            ),
            "tilt_plate_size_mm": TILT_PLATE_SIZE_MM.tolist(),
            "post_metrics": mount_metrics["post_metrics"],
            "mid360_mount_center_mm": (
                TILT_PLATE_MOUNT_CENTER_MM.tolist()
            ),
            "camera_front_origin_mm": CAMERA_FRONT_ORIGIN_MM.tolist(),
            "camera_tilt_deg": CAMERA_TILT_DEG,
            **camera_metrics,
            "guard_top_mm": guard_top_mm,
            "interface_envelope_mm": [218.0, 92.0, 44.0],
            "interface_center_x_mm": INTERFACE_CENTER_X_MM,
            "interface_to_carrier_visible_x_gap_mm": visible_gap_mm,
            "deck_contact_z_mm": deck_contact_z_mm,
        },
        "explicitly_absent": [
            "J17A carrier mesh",
            "J20A adapter mesh",
            "S410 guard mesh",
            "spanning payload deck",
            "long external rails",
            "hidden factory receiver guess",
            "hidden thread or nut guess",
            "clearance-driven sensor translation",
            "print adaptation",
        ],
        "entries": entries,
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"manifest={MANIFEST}")
    print(f"guard_top_mm={guard_top_mm:.6f}")
    print(f"interface_to_carrier_visible_x_gap_mm={visible_gap_mm:.6f}")
    print(
        "post_heights_mm="
        f"{[round(item['height_mm'], 6) for item in mount_metrics['post_metrics']]}"
    )


if __name__ == "__main__":
    main()
