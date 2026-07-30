#!/usr/bin/env python3
"""Prepare a minimum-forward-shift Pro/Interface clearance candidate.

The candidate preserves every visible source part and translates the complete
J17A/Mid-360/D435 assembly only far enough to clear the current Interface
placeholder by 3 mm. It is a placement review, not an accepted adapter design.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh


TASK_ROOT = Path(__file__).resolve().parents[1]
DIRECT_ROOT = TASK_ROOT / "evidence/j17a-direct-camera-candidate"
DIRECT_MESH_ROOT = DIRECT_ROOT / "meshes"
OUTPUT_ROOT = TASK_ROOT / "evidence/pro-clearance-placement-candidate"
MESH_ROOT = OUTPUT_ROOT / "meshes"
MANIFEST = OUTPUT_ROOT / "manifest.json"

TARGET_CLEARANCE_MM = 3.0
J17A_MOUNT_X_MM = np.asarray([72.676, 182.676], dtype=float)
J17A_MOUNT_Y_MM = np.asarray([-43.0, 43.0], dtype=float)
LITE3_PRO_PATTERN_CENTER_MM = np.asarray([20.0, 0.0], dtype=float)
LITE3_PRO_PATTERN_MM = np.asarray([74.0, 94.0], dtype=float)

CONTEXT_NODES = [
    "TORSO",
    "FACTORY_INTERFACE",
    "FACTORY_INTERFACE_CONNECTORS",
    "FACTORY_INTERFACE_VENTS",
]
SENSOR_NODES = [
    "J17A_SENSOR_CARRIER_SOURCE",
    "MID360_ADAPTER",
    "MID360_GUARD",
    "MID360_BODY",
    "MID360_HOUSING_EXTERIOR",
    "MID360_OPTICAL_WINDOW",
    "MID360_CONNECTOR",
    "D435I_CAMERA_DIRECT",
    "D435_DIRECT_FASTENER_REFERENCES",
]


def load_mm(name: str) -> trimesh.Trimesh:
    return trimesh.load_mesh(
        DIRECT_MESH_ROOT / f"{name}.stl",
        process=True,
        validate=True,
    )


def export_mm(mesh: trimesh.Trimesh, path: Path) -> dict[str, object]:
    mesh.export(path)
    return {
        "path": str(path.resolve()),
        "bounds_mm": np.asarray(mesh.bounds).round(6).tolist(),
        "extent_mm": np.asarray(mesh.extents).round(6).tolist(),
        "vertex_count": int(len(mesh.vertices)),
        "face_count": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight),
        "volume_mm3": (
            round(float(abs(mesh.volume)), 6)
            if mesh.is_watertight
            else None
        ),
    }


def cylinder_between(
    start_mm: np.ndarray,
    end_mm: np.ndarray,
    radius_mm: float,
    sections: int = 48,
) -> trimesh.Trimesh:
    direction = end_mm - start_mm
    length = float(np.linalg.norm(direction))
    transform = trimesh.geometry.align_vectors(
        [0.0, 0.0, 1.0],
        direction / length,
    )
    transform[:3, 3] = (start_mm + end_mm) / 2.0
    return trimesh.creation.cylinder(
        radius=radius_mm,
        height=length,
        sections=sections,
        transform=transform,
    )


def j17a_mount_fastener_references(
    shift_x_mm: float,
) -> tuple[trimesh.Trimesh, list[list[float]]]:
    centers = [
        np.asarray([x + shift_x_mm, y, 446.0], dtype=float)
        for x in J17A_MOUNT_X_MM
        for y in J17A_MOUNT_Y_MM
    ]
    parts: list[trimesh.Trimesh] = []
    for center in centers:
        parts.extend(
            [
                cylinder_between(
                    center + np.asarray([0.0, 0.0, -10.0]),
                    center + np.asarray([0.0, 0.0, 2.0]),
                    radius_mm=1.5,
                ),
                cylinder_between(
                    center + np.asarray([0.0, 0.0, 0.5]),
                    center + np.asarray([0.0, 0.0, 3.0]),
                    radius_mm=2.75,
                ),
            ]
        )
    return (
        trimesh.util.concatenate(parts),
        [center.round(6).tolist() for center in centers],
    )


def pro_hole_axis_references() -> tuple[trimesh.Trimesh, list[list[float]]]:
    x_values = (
        LITE3_PRO_PATTERN_CENTER_MM[0]
        + np.asarray([-0.5, 0.5]) * LITE3_PRO_PATTERN_MM[0]
    )
    y_values = (
        LITE3_PRO_PATTERN_CENTER_MM[1]
        + np.asarray([-0.5, 0.5]) * LITE3_PRO_PATTERN_MM[1]
    )
    centers = [
        np.asarray([x, y, 428.0], dtype=float)
        for x in x_values
        for y in y_values
    ]
    axes = [
        cylinder_between(
            center + np.asarray([0.0, 0.0, -5.0]),
            center + np.asarray([0.0, 0.0, 6.0]),
            radius_mm=1.75,
        )
        for center in centers
    ]
    return (
        trimesh.util.concatenate(axes),
        [center.round(6).tolist() for center in centers],
    )


def main() -> None:
    MESH_ROOT.mkdir(parents=True, exist_ok=True)
    interface = load_mm("FACTORY_INTERFACE")
    j17a = load_mm("J17A_SENSOR_CARRIER_SOURCE")
    required_shift_x_mm = (
        float(interface.bounds[1, 0])
        + TARGET_CLEARANCE_MM
        - float(j17a.bounds[0, 0])
    )
    if required_shift_x_mm <= 0.0:
        raise RuntimeError("Expected a positive forward clearance shift")

    entries: list[dict[str, object]] = []
    context_meshes: dict[str, trimesh.Trimesh] = {}
    for name in CONTEXT_NODES:
        mesh = load_mm(name)
        context_meshes[name] = mesh
        entries.append(
            {
                "node_name": name,
                "role": "context",
                **export_mm(mesh, MESH_ROOT / f"{name}.stl"),
            }
        )

    original_j17a = j17a.copy()
    entries.append(
        {
            "node_name": "J17A_ORIGINAL_POSITION_GHOST",
            "role": "diagnostic_only",
            **export_mm(
                original_j17a,
                MESH_ROOT / "J17A_ORIGINAL_POSITION_GHOST.stl",
            ),
        }
    )

    shifted_sensor_meshes: dict[str, trimesh.Trimesh] = {}
    for name in SENSOR_NODES:
        mesh = load_mm(name)
        mesh.apply_translation([required_shift_x_mm, 0.0, 0.0])
        shifted_sensor_meshes[name] = mesh
        entries.append(
            {
                "node_name": name,
                "role": "source_sensor_shifted_as_one_rigid_assembly",
                **export_mm(mesh, MESH_ROOT / f"{name}.stl"),
            }
        )

    interface_overlap = trimesh.boolean.intersection(
        [
            shifted_sensor_meshes["J17A_SENSOR_CARRIER_SOURCE"],
            interface,
        ],
        engine="manifold",
    )
    interface_overlap_mm3 = (
        0.0
        if len(interface_overlap.faces) == 0
        else float(abs(interface_overlap.volume))
    )
    if interface_overlap_mm3 > 1.0e-6:
        raise RuntimeError(
            "Minimum-forward-shift candidate still intersects Interface"
        )

    j17a_fasteners, j17a_fastener_centers = (
        j17a_mount_fastener_references(required_shift_x_mm)
    )
    entries.append(
        {
            "node_name": "J17A_FOUR_FASTENER_REFERENCES",
            "role": "official_video_mounting_axis_reference",
            **export_mm(
                j17a_fasteners,
                MESH_ROOT / "J17A_FOUR_FASTENER_REFERENCES.stl",
            ),
        }
    )

    pro_axes, pro_axis_centers = pro_hole_axis_references()
    entries.append(
        {
            "node_name": "LITE3_PRO_74X94_HOLE_AXIS_REFERENCES",
            "role": "official_manual_interface_reference",
            **export_mm(
                pro_axes,
                MESH_ROOT / "LITE3_PRO_74X94_HOLE_AXIS_REFERENCES.stl",
            ),
        }
    )

    torso_top_z_mm = float(context_meshes["TORSO"].bounds[1, 2])
    manifest = {
        "schema_version": 1,
        "purpose": (
            "minimum_forward_shift_placement_review_before_hidden_adapter"
        ),
        "target_interface_clearance_mm": TARGET_CLEARANCE_MM,
        "required_rigid_sensor_shift_mm": [
            round(required_shift_x_mm, 6),
            0.0,
            0.0,
        ],
        "resulting_j17a_interface_aabb_gap_x_mm": round(
            float(
                shifted_sensor_meshes[
                    "J17A_SENSOR_CARRIER_SOURCE"
                ].bounds[0, 0]
                - interface.bounds[1, 0]
            ),
            6,
        ),
        "j17a_interface_boolean_intersection_mm3": round(
            interface_overlap_mm3,
            9,
        ),
        "torso_top_z_mm": round(torso_top_z_mm, 6),
        "shifted_d435_min_z_mm": round(
            float(
                shifted_sensor_meshes[
                    "D435I_CAMERA_DIRECT"
                ].bounds[0, 2]
            ),
            6,
        ),
        "shifted_d435_torso_vertical_aabb_clearance_mm": round(
            float(
                shifted_sensor_meshes[
                    "D435I_CAMERA_DIRECT"
                ].bounds[0, 2]
                - torso_top_z_mm
            ),
            6,
        ),
        "j17a_fastener_centers_mm": j17a_fastener_centers,
        "lite3_pro_hole_axis_centers_mm": pro_axis_centers,
        "accepted_visible_geometry_changes": [],
        "placement_claim_boundary": (
            "The 36 mm-class shift is the minimum derived from the current "
            "160 x 92 x 46 mm image-estimated Interface placeholder plus a "
            "3 mm clearance. It preserves source geometry but is not a "
            "measured physical-robot datum."
        ),
        "fastener_claim_boundary": (
            "The official video proves four J17A mounting locations and the "
            "manual proves the Lite3 Pro 74 x 94 mm pattern. The diagnostic "
            "fastener envelopes do not prove an adapter shape, screw length, "
            "thread engagement, or a load-rated Pro installation."
        ),
        "adapter_state": (
            "not_designed_pending_placement_and_physical_interface_review"
        ),
        "entries": entries,
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"manifest={MANIFEST}")
    print(
        "required_rigid_sensor_shift_mm="
        f"{manifest['required_rigid_sensor_shift_mm']}"
    )
    print(
        "j17a_interface_boolean_intersection_mm3="
        f"{manifest['j17a_interface_boolean_intersection_mm3']}"
    )
    print(
        "shifted_d435_torso_vertical_aabb_clearance_mm="
        f"{manifest['shifted_d435_torso_vertical_aabb_clearance_mm']}"
    )


if __name__ == "__main__":
    main()
