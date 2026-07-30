#!/usr/bin/env python3
"""Prepare a source-backed J17A/D435 direct-mount evidence candidate.

This script does not modify the accepted replica build. It:

1. aligns the published J17A STEP-derived mesh to the current J20A placement;
2. removes the rejected 17 mm artificial camera standoff;
3. places the official D435 visual mesh directly on J17A's two-hole face;
4. adds only two evidence-level M3 fastener references; and
5. reports the collision between J17A and the current Interface placeholder.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[2]
REPLICA_ROOT = (
    REPO_ROOT
    / "references/derived/2026-07-24_lite3-lidar-printable-replica"
)
CURRENT_GLB = REPLICA_ROOT / "models/reference/lite3_lidar_1_1_reference.glb"
J17A_HISTORY_GLB = (
    REPLICA_ROOT
    / "rebuild-check-j17a-ipc-base/models/reference/"
    "lite3_lidar_1_1_reference.glb"
)
OUTPUT_ROOT = TASK_ROOT / "evidence/j17a-direct-camera-candidate"
MESH_ROOT = OUTPUT_ROOT / "meshes"
MANIFEST = OUTPUT_ROOT / "manifest.json"

CAMERA_AXIS_ROBOT = np.asarray(
    [0.9396926207859084, 0.0, -0.3420201433256687],
    dtype=float,
)
CAMERA_WIDTH_AXIS_ROBOT = np.asarray([0.0, 1.0, 0.0], dtype=float)
REJECTED_STANDOFF_MM = 17.0
CAMERA_HOLE_SPACING_MM = 45.0
CAMERA_MOUNT_CENTER_ROBOT_MM = np.asarray(
    [193.9615, 0.0, 451.3423],
    dtype=float,
)

CURRENT_SOURCE_NODES = [
    "TORSO",
    "FACTORY_INTERFACE",
    "FACTORY_INTERFACE_CONNECTORS",
    "FACTORY_INTERFACE_VENTS",
    "MID360_ADAPTER",
    "MID360_GUARD",
    "MID360_BODY",
    "MID360_HOUSING_EXTERIOR",
    "MID360_OPTICAL_WINDOW",
    "MID360_CONNECTOR",
]


def world_mesh(scene: trimesh.Scene, node_name: str) -> trimesh.Trimesh:
    transform, geometry_name = scene.graph.get(node_name)
    mesh = scene.geometry[geometry_name].copy()
    mesh.apply_transform(transform)
    return mesh


def export_mm(mesh: trimesh.Trimesh, path: Path) -> dict[str, object]:
    mesh_mm = mesh.copy()
    mesh_mm.apply_scale(1000.0)
    mesh_mm.export(path)
    return {
        "path": str(path.resolve()),
        "bounds_mm": np.asarray(mesh_mm.bounds).round(6).tolist(),
        "extent_mm": np.asarray(mesh_mm.extents).round(6).tolist(),
        "vertex_count": int(len(mesh_mm.vertices)),
        "face_count": int(len(mesh_mm.faces)),
        "watertight": bool(mesh_mm.is_watertight),
        "volume_mm3": (
            round(float(abs(mesh_mm.volume)), 6)
            if mesh_mm.is_watertight
            else None
        ),
    }


def cylinder_between(
    start_m: np.ndarray,
    end_m: np.ndarray,
    radius_m: float,
    sections: int = 48,
) -> trimesh.Trimesh:
    direction = end_m - start_m
    length = float(np.linalg.norm(direction))
    if length <= 0.0:
        raise ValueError("Cylinder length must be positive")
    transform = trimesh.geometry.align_vectors(
        [0.0, 0.0, 1.0],
        direction / length,
    )
    transform[:3, 3] = (start_m + end_m) / 2.0
    return trimesh.creation.cylinder(
        radius=radius_m,
        height=length,
        sections=sections,
        transform=transform,
    )


def direct_fastener_references() -> tuple[trimesh.Trimesh, list[list[float]]]:
    mount_center_m = CAMERA_MOUNT_CENTER_ROBOT_MM / 1000.0
    hole_centers_m = [
        mount_center_m
        + CAMERA_WIDTH_AXIS_ROBOT * y_sign * CAMERA_HOLE_SPACING_MM / 2000.0
        for y_sign in (-1.0, 1.0)
    ]
    parts: list[trimesh.Trimesh] = []
    for hole_center_m in hole_centers_m:
        # The official evidence proves two M3 axes and visible screw heads.
        # The 7 mm reference shaft is deliberately not a manufacturing-length
        # claim; it only makes the direct load path inspectable in the render.
        shaft_start_m = hole_center_m - CAMERA_AXIS_ROBOT * 0.0030
        shaft_end_m = hole_center_m + CAMERA_AXIS_ROBOT * 0.0040
        head_start_m = hole_center_m - CAMERA_AXIS_ROBOT * 0.0050
        head_end_m = hole_center_m - CAMERA_AXIS_ROBOT * 0.0030
        parts.extend(
            [
                cylinder_between(
                    shaft_start_m,
                    shaft_end_m,
                    radius_m=0.0015,
                ),
                cylinder_between(
                    head_start_m,
                    head_end_m,
                    radius_m=0.00275,
                ),
            ]
        )
    return (
        trimesh.util.concatenate(parts),
        [(center * 1000.0).round(6).tolist() for center in hole_centers_m],
    )


def sampled_minimum_distance_mm(
    first: trimesh.Trimesh,
    second: trimesh.Trimesh,
) -> float:
    np.random.seed(20260726)
    points, _ = trimesh.sample.sample_surface(first, 20000)
    _, distances, _ = trimesh.proximity.closest_point(second, points)
    return round(float(np.min(distances) * 1000.0), 6)


def main() -> None:
    MESH_ROOT.mkdir(parents=True, exist_ok=True)
    current = trimesh.load(CURRENT_GLB, force="scene", process=False)
    history = trimesh.load(J17A_HISTORY_GLB, force="scene", process=False)

    current_adapter = world_mesh(current, "MID360_ADAPTER")
    history_adapter = world_mesh(history, "MID360_ADAPTER")
    alignment_m = (
        current_adapter.bounding_box.centroid
        - history_adapter.bounding_box.centroid
    )

    entries: list[dict[str, object]] = []
    current_meshes: dict[str, trimesh.Trimesh] = {}
    for node_name in CURRENT_SOURCE_NODES:
        mesh = world_mesh(current, node_name)
        current_meshes[node_name] = mesh
        entries.append(
            {
                "node_name": node_name,
                "source": (
                    "current_image_estimated_context"
                    if node_name.startswith("FACTORY_INTERFACE")
                    else "current_source_geometry"
                ),
                **export_mm(mesh, MESH_ROOT / f"{node_name}.stl"),
            }
        )

    j17a = world_mesh(history, "J17A_SENSOR_CARRIER")
    j17a.apply_translation(alignment_m)
    entries.append(
        {
            "node_name": "J17A_SENSOR_CARRIER_SOURCE",
            "source": "official_lite3_venture_fast_livo2_j17a_step",
            **export_mm(
                j17a,
                MESH_ROOT / "J17A_SENSOR_CARRIER_SOURCE.stl",
            ),
        }
    )

    camera_original = world_mesh(current, "D435I_CAMERA")
    camera_direct = camera_original.copy()
    camera_translation_m = (
        -CAMERA_AXIS_ROBOT * REJECTED_STANDOFF_MM / 1000.0
    )
    camera_direct.apply_translation(camera_translation_m)
    entries.append(
        {
            "node_name": "D435I_CAMERA_DIRECT",
            "source": "official_realsense_visual_directly_seated_on_j17a",
            **export_mm(
                camera_direct,
                MESH_ROOT / "D435I_CAMERA_DIRECT.stl",
            ),
        }
    )

    fasteners, hole_centers_mm = direct_fastener_references()
    entries.append(
        {
            "node_name": "D435_DIRECT_FASTENER_REFERENCES",
            "source": (
                "two_m3_axes_from_j17a_view_a_and_realsense_45_mm_pattern"
            ),
            **export_mm(
                fasteners,
                MESH_ROOT / "D435_DIRECT_FASTENER_REFERENCES.stl",
            ),
        }
    )

    interface = current_meshes["FACTORY_INTERFACE"]
    overlap = trimesh.boolean.intersection(
        [j17a, interface],
        engine="manifold",
    )
    if not isinstance(overlap, trimesh.Trimesh) or len(overlap.faces) == 0:
        raise RuntimeError(
            "Expected current Interface placeholder to intersect J17A"
        )
    overlap_metrics = export_mm(
        overlap,
        MESH_ROOT / "CURRENT_INTERFACE_J17A_OVERLAP.stl",
    )
    entries.append(
        {
            "node_name": "CURRENT_INTERFACE_J17A_OVERLAP",
            "source": "derived_collision_diagnostic",
            **overlap_metrics,
        }
    )

    manifest = {
        "schema_version": 1,
        "purpose": "source_backed_j17a_d435_direct_mount_evidence_candidate",
        "current_glb": str(CURRENT_GLB.resolve()),
        "j17a_history_glb": str(J17A_HISTORY_GLB.resolve()),
        "primary_evidence": [
            str(
                (
                    REPO_ROOT
                    / "references/upstream/"
                    "2026-07-26_lite3-official-fast-livo2-install-video/"
                    "derived/sensor-install/frame-284s.jpg"
                ).resolve()
            ),
            str(
                (
                    REPO_ROOT
                    / "references/upstream/"
                    "2026-07-26_lite3-official-fast-livo2-install-video/"
                    "derived/sensor-install/frame-292s.jpg"
                ).resolve()
            ),
            str(
                (
                    REPO_ROOT
                    / "references/upstream/"
                    "2026-07-24_lite3-venture-fast-livo2-hardware/"
                    "derived/j17a-drawing.png"
                ).resolve()
            ),
        ],
        "alignment_method": (
            "rigid translation aligning the source J17A assembly J20A "
            "bounding-box centroid to the current source-backed J20A centroid"
        ),
        "j17a_alignment_translation_mm": (
            alignment_m * 1000.0
        ).round(6).tolist(),
        "camera_axis_robot": CAMERA_AXIS_ROBOT.round(9).tolist(),
        "rejected_camera_standoff_mm": REJECTED_STANDOFF_MM,
        "direct_camera_translation_mm": (
            camera_translation_m * 1000.0
        ).round(6).tolist(),
        "camera_hole_centers_robot_mm": hole_centers_mm,
        "camera_hole_spacing_mm": CAMERA_HOLE_SPACING_MM,
        "direct_camera_to_j17a_sampled_minimum_distance_mm": (
            sampled_minimum_distance_mm(camera_direct, j17a)
        ),
        "current_interface_placeholder_collision": {
            "volume_mm3": overlap_metrics["volume_mm3"],
            "bounds_mm": overlap_metrics["bounds_mm"],
            "interpretation": (
                "The current image-estimated Interface placeholder intersects "
                "the unchanged J17A source mesh. This proves the current CAD "
                "layout is invalid, not the dimensions of Dr Sun's hardware."
            ),
        },
        "forbidden_current_nodes": [
            "CAMERA_MOUNT_BRACKET",
            "CAMERA_CARRIER_PLATE",
            "CAMERA_RECEIVER_YOKE",
            "CAMERA_FASTENERS",
            "FACTORY_LIDAR_MOUNTS",
        ],
        "fastener_claim_boundary": (
            "The two M3 axes and 45 mm spacing are source-backed. Rendered "
            "head/shaft envelopes expose the direct assembly path only; exact "
            "screw head standard, length, thread engagement, and torque remain "
            "unresolved."
        ),
        "base_claim_boundary": (
            "The original J17A is proven for Lite3 Venture. The Pro 74 x 94 mm "
            "robot interface and the user's different Interface enclosure "
            "require a separately labeled hidden print adaptation."
        ),
        "entries": entries,
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"manifest={MANIFEST}")
    print(
        "direct_camera_translation_mm="
        f"{manifest['direct_camera_translation_mm']}"
    )
    print(
        "direct_camera_to_j17a_sampled_minimum_distance_mm="
        f"{manifest['direct_camera_to_j17a_sampled_minimum_distance_mm']}"
    )
    print(
        "current_interface_collision_volume_mm3="
        f"{manifest['current_interface_placeholder_collision']['volume_mm3']}"
    )
    print(f"mesh_count={len(entries)}")


if __name__ == "__main__":
    main()
