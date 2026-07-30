#!/usr/bin/env python3
"""Prepare a source-backed FAST-LIVO2 sensor/BZ20 placement candidate.

This candidate removes the incorrect 160 x 92 x 46.8 mm generic Interface
placeholder.  It keeps the unchanged J17A/J20A/S410/Mid-360/D435 assembly in
its reviewed position and places the official 108 x 96 x 30 mm BZ20 STEP
behind J17A with an explicitly image-estimated transform.

No Pro adapter, industrial-PC base, AGX body, or spanning lower plate is added.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[2]
DIRECT_ROOT = TASK_ROOT / "evidence/j17a-direct-camera-candidate"
DIRECT_MESH_ROOT = DIRECT_ROOT / "meshes"
COMPUTE_ROOT = TASK_ROOT / "evidence/official-fast-livo2-compute-parts"
OUTPUT_ROOT = TASK_ROOT / "evidence/official-bz20-layout-candidate"
MESH_ROOT = OUTPUT_ROOT / "meshes"
MANIFEST = OUTPUT_ROOT / "manifest.json"
FULL_BODY_SOURCE = (
    REPO_ROOT
    / "references/derived/2026-07-24_lite3-lidar-printable-replica"
    / "evidence/body-diagnostic/lite3-official-visual-z-up.stl"
)

TARGET_BZ20_TO_J17A_GAP_X_MM = 3.0
TARGET_BZ20_TO_TORSO_GAP_Z_MM = 2.5

J17A_MOUNT_X_MM = np.asarray([72.676, 182.676], dtype=float)
J17A_MOUNT_Y_MM = np.asarray([-43.0, 43.0], dtype=float)
J17A_MOUNT_SEATING_Z_MM = 446.0

SOURCE_SENSOR_NODES = [
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


def load_mm(path: Path) -> trimesh.Trimesh:
    return trimesh.load_mesh(path, process=True, validate=True)


def load_visual_mm(path: Path) -> trimesh.Trimesh:
    return trimesh.load_mesh(
        path,
        process=False,
        maintain_order=True,
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
        "connected_components": int(
            len(mesh.split(only_watertight=False))
        ),
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


def j17a_fastener_references() -> tuple[trimesh.Trimesh, list[list[float]]]:
    centers = [
        np.asarray(
            [x_mm, y_mm, J17A_MOUNT_SEATING_Z_MM],
            dtype=float,
        )
        for x_mm in J17A_MOUNT_X_MM
        for y_mm in J17A_MOUNT_Y_MM
    ]
    parts = []
    for center in centers:
        parts.extend(
            [
                cylinder_between(
                    center + np.asarray([0.0, 0.0, -6.0]),
                    center + np.asarray([0.0, 0.0, 1.0]),
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


def intersection_volume_mm3(
    first: trimesh.Trimesh,
    second: trimesh.Trimesh,
) -> float:
    overlap = trimesh.boolean.intersection(
        [first, second],
        engine="manifold",
    )
    if not isinstance(overlap, trimesh.Trimesh) or len(overlap.faces) == 0:
        return 0.0
    return float(abs(overlap.volume))


def main() -> None:
    MESH_ROOT.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, object]] = []

    torso = load_mm(DIRECT_MESH_ROOT / "TORSO.stl")
    entries.append(
        {
            "node_name": "TORSO",
            "role": "official_lite3_exterior_context",
            **export_mm(torso, MESH_ROOT / "TORSO.stl"),
        }
    )
    full_body = load_visual_mm(FULL_BODY_SOURCE)
    full_body_ground_normalization_mm = -float(full_body.bounds[0, 2])
    full_body.apply_translation(
        np.asarray([0.0, 0.0, full_body_ground_normalization_mm])
    )
    full_body_top_alignment_delta_mm = float(
        torso.bounds[1, 2] - full_body.bounds[1, 2]
    )
    if abs(full_body_top_alignment_delta_mm) > 1.0e-3:
        raise RuntimeError(
            "Official full-body and torso top datums do not align: "
            f"{full_body_top_alignment_delta_mm:.6f} mm"
        )
    entries.append(
        {
            "node_name": "FULL_LITE3_OFFICIAL_VISUAL",
            "role": (
                "official_full_standing_visual_context_not_printable_geometry"
            ),
            **export_mm(
                full_body,
                MESH_ROOT / "FULL_LITE3_OFFICIAL_VISUAL.stl",
            ),
        }
    )

    sensor_meshes: dict[str, trimesh.Trimesh] = {}
    for name in SOURCE_SENSOR_NODES:
        mesh = load_mm(DIRECT_MESH_ROOT / f"{name}.stl")
        sensor_meshes[name] = mesh
        entries.append(
            {
                "node_name": name,
                "role": "unchanged_source_sensor_assembly",
                **export_mm(mesh, MESH_ROOT / f"{name}.stl"),
            }
        )

    bz20_source = load_mm(
        COMPUTE_ROOT / "meshes/BZ20_BACKLOAD_SHELL_SOURCE.stl"
    )
    desired_x_max_mm = (
        float(
            sensor_meshes["J17A_SENSOR_CARRIER_SOURCE"].bounds[0, 0]
        )
        - TARGET_BZ20_TO_J17A_GAP_X_MM
    )
    desired_y_center_mm = 0.0
    desired_z_min_mm = (
        float(torso.bounds[1, 2])
        + TARGET_BZ20_TO_TORSO_GAP_Z_MM
    )
    bz20_translation_mm = np.asarray(
        [
            desired_x_max_mm - float(bz20_source.bounds[1, 0]),
            desired_y_center_mm
            - float(bz20_source.bounds.mean(axis=0)[1]),
            desired_z_min_mm - float(bz20_source.bounds[0, 2]),
        ],
        dtype=float,
    )
    bz20 = bz20_source.copy()
    bz20.apply_translation(bz20_translation_mm)
    entries.append(
        {
            "node_name": "BZ20_BACKLOAD_SHELL_SOURCE",
            "role": (
                "official_source_geometry_with_image_estimated_rigid_transform"
            ),
            **export_mm(
                bz20,
                MESH_ROOT / "BZ20_BACKLOAD_SHELL_SOURCE.stl",
            ),
        }
    )

    j17a_fasteners, j17a_fastener_centers = (
        j17a_fastener_references()
    )
    entries.append(
        {
            "node_name": "J17A_FOUR_MOUNT_FASTENER_REFERENCES",
            "role": (
                "official_video_mounting_axes_with_unresolved_screw_length"
            ),
            **export_mm(
                j17a_fasteners,
                MESH_ROOT / "J17A_FOUR_MOUNT_FASTENER_REFERENCES.stl",
            ),
        }
    )

    j17a = sensor_meshes["J17A_SENSOR_CARRIER_SOURCE"]
    d435 = sensor_meshes["D435I_CAMERA_DIRECT"]
    bz20_to_j17a_gap_x_mm = float(
        j17a.bounds[0, 0] - bz20.bounds[1, 0]
    )
    bz20_to_torso_gap_z_mm = float(
        bz20.bounds[0, 2] - torso.bounds[1, 2]
    )
    d435_to_torso_gap_z_mm = float(
        d435.bounds[0, 2] - torso.bounds[1, 2]
    )

    bz20_to_j17a_intersection_mm3 = intersection_volume_mm3(
        bz20,
        j17a,
    )
    collision_checks = {
        "bz20_to_j17a_intersection_mm3": round(
            bz20_to_j17a_intersection_mm3,
            6,
        ),
        "bz20_to_torso_aabb_overlap": bool(
            bz20_to_torso_gap_z_mm < 0.0
        ),
        "d435_to_torso_aabb_overlap": bool(
            d435_to_torso_gap_z_mm < 0.0
        ),
        "open_visual_torso_boolean_state": (
            "not_run; official torso visual is not a closed solid"
        ),
    }
    if (
        bz20_to_j17a_intersection_mm3 > 1.0e-6
        or collision_checks["bz20_to_torso_aabb_overlap"]
        or collision_checks["d435_to_torso_aabb_overlap"]
    ):
        raise RuntimeError(
            f"Unexpected candidate collision: {collision_checks}"
        )

    manifest = {
        "schema_version": 1,
        "purpose": (
            "official_fast_livo2_sensor_and_bz20_layout_review"
        ),
        "removed_geometry": [
            "160_x_92_x_46.8_mm_generic_FACTORY_INTERFACE_placeholder",
            "pro_to_j17a_spanning_hidden_adapter",
            "invented_camera_rails_plate_yoke",
        ],
        "bz20_source_nominal_extent_mm": [108.0, 96.0, 30.0],
        "bz20_image_estimated_translation_mm": (
            bz20_translation_mm.round(6).tolist()
        ),
        "full_body_source_path": str(FULL_BODY_SOURCE.resolve()),
        "full_body_ground_normalization_mm": round(
            full_body_ground_normalization_mm,
            6,
        ),
        "full_body_top_alignment_delta_mm": round(
            full_body_top_alignment_delta_mm,
            6,
        ),
        "bz20_to_j17a_gap_x_mm": round(
            bz20_to_j17a_gap_x_mm,
            6,
        ),
        "bz20_to_torso_gap_z_mm": round(
            bz20_to_torso_gap_z_mm,
            6,
        ),
        "d435_to_torso_gap_z_mm": round(
            d435_to_torso_gap_z_mm,
            6,
        ),
        "collision_checks": collision_checks,
        "j17a_fastener_centers_mm": j17a_fastener_centers,
        "visible_fastener_contract": {
            "j17a_robot_side_mounting_axis_references": 4,
            "d435_to_j17a_m3_locations": 2,
            "exact_screw_lengths": "unresolved",
            "j17a_robot_side_receiver_structure": (
                "not_modelled_pending_pro_adapter_and_user_ipc_geometry"
            ),
        },
        "industrial_pc_state": (
            "not_modelled; the official rear AGX device and the user's "
            "different industrial PC are separate from BZ20"
        ),
        "pro_adapter_state": (
            "not_designed_pending_user_industrial_pc_geometry_and_mounting_data"
        ),
        "claim_boundary": (
            "This is a source-backed visual placement candidate for the "
            "official Lite3 Venture FAST-LIVO2 extension. BZ20 placement is "
            "estimated from official video frames. It is not a Lite3 Pro "
            "conversion, a measured fit to the user's industrial PC, or a "
            "load-rated real-robot bracket."
        ),
        "entries": entries,
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                key: manifest[key]
                for key in (
                    "bz20_image_estimated_translation_mm",
                    "bz20_to_j17a_gap_x_mm",
                    "bz20_to_torso_gap_z_mm",
                    "d435_to_torso_gap_z_mm",
                    "collision_checks",
                    "industrial_pc_state",
                    "pro_adapter_state",
                )
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
