#!/usr/bin/env python3
"""Prepare a printable hidden Pro-to-J17A adapter candidate.

The candidate keeps the published J17A/J20A/S410/Mid-360/D435 geometry rigid,
moves it only by the reviewed Interface-clearance offset, and adds a separately
named skeletal print adapter. The adapter joins the official Lite3 Pro 74 x
94 mm pattern to the four J17A mounting locations without an exposed full
plate or side rails.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh


TASK_ROOT = Path(__file__).resolve().parents[1]
DIRECT_ROOT = TASK_ROOT / "evidence/j17a-direct-camera-candidate"
DIRECT_MESH_ROOT = DIRECT_ROOT / "meshes"
OUTPUT_ROOT = TASK_ROOT / "evidence/pro-hidden-adapter-candidate"
MESH_ROOT = OUTPUT_ROOT / "meshes"
MANIFEST = OUTPUT_ROOT / "manifest.json"

INTERFACE_CLEARANCE_X_MM = 3.0
VERTICAL_EQUIPMENT_SHIFT_MM = 4.0
FRAME_THICKNESS_MM = 6.0
FRAME_TO_TORSO_GAP_MM = 0.2
FRAME_SPINE_WIDTH_MM = 14.0
FRAME_CROSSBAR_WIDTH_MM = 14.0
FRAME_PRO_CROSSBAR_LENGTH_MM = 108.0
FRAME_J17A_CROSSBAR_LENGTH_MM = 98.0
J17A_SPACER_OUTER_DIAMETER_MM = 12.0
J17A_SOURCE_SEATING_PLANE_Z_MM = 446.0
J17A_SPACER_TOP_GAP_MM = 0.05
PRO_HOLE_DIAMETER_MM = 3.5
J17A_HOLE_DIAMETER_MM = 4.5

PRO_X_MM = np.asarray([-17.0, 57.0], dtype=float)
PRO_Y_MM = np.asarray([-47.0, 47.0], dtype=float)
J17A_SOURCE_X_MM = np.asarray([72.676, 182.676], dtype=float)
J17A_Y_MM = np.asarray([-43.0, 43.0], dtype=float)

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
        "connected_components": int(
            len(mesh.split(only_watertight=False))
        ),
        "volume_mm3": (
            round(float(abs(mesh.volume)), 6)
            if mesh.is_watertight
            else None
        ),
    }


def box(
    size_mm: tuple[float, float, float],
    center_mm: tuple[float, float, float],
) -> trimesh.Trimesh:
    transform = np.eye(4)
    transform[:3, 3] = np.asarray(center_mm, dtype=float)
    return trimesh.creation.box(
        extents=np.asarray(size_mm, dtype=float),
        transform=transform,
    )


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


def socket_head_reference(
    axis_center_xy_mm: np.ndarray,
    shaft_z_min_mm: float,
    shaft_z_max_mm: float,
    head_z_min_mm: float,
    head_z_max_mm: float,
) -> trimesh.Trimesh:
    x, y = axis_center_xy_mm
    shaft = cylinder_between(
        np.asarray([x, y, shaft_z_min_mm]),
        np.asarray([x, y, shaft_z_max_mm]),
        radius_mm=1.5,
    )
    head = cylinder_between(
        np.asarray([x, y, head_z_min_mm]),
        np.asarray([x, y, head_z_max_mm]),
        radius_mm=2.75,
    )
    return trimesh.util.concatenate([shaft, head])


def build_adapter(
    torso_top_z_mm: float,
    sensor_shift_x_mm: float,
) -> tuple[trimesh.Trimesh, dict[str, object]]:
    frame_bottom_z_mm = torso_top_z_mm + FRAME_TO_TORSO_GAP_MM
    frame_top_z_mm = frame_bottom_z_mm + FRAME_THICKNESS_MM
    frame_center_z_mm = (frame_bottom_z_mm + frame_top_z_mm) / 2.0
    j17a_x_mm = J17A_SOURCE_X_MM + sensor_shift_x_mm

    spine_x_min_mm = float(PRO_X_MM.min() - FRAME_CROSSBAR_WIDTH_MM / 2.0)
    spine_x_max_mm = float(
        j17a_x_mm.max() + FRAME_CROSSBAR_WIDTH_MM / 2.0
    )
    parts = [
        box(
            (
                spine_x_max_mm - spine_x_min_mm,
                FRAME_SPINE_WIDTH_MM,
                FRAME_THICKNESS_MM,
            ),
            (
                (spine_x_min_mm + spine_x_max_mm) / 2.0,
                0.0,
                frame_center_z_mm,
            ),
        )
    ]
    for x_mm in PRO_X_MM:
        parts.append(
            box(
                (
                    FRAME_CROSSBAR_WIDTH_MM,
                    FRAME_PRO_CROSSBAR_LENGTH_MM,
                    FRAME_THICKNESS_MM,
                ),
                (float(x_mm), 0.0, frame_center_z_mm),
            )
        )
    for x_mm in j17a_x_mm:
        parts.append(
            box(
                (
                    FRAME_CROSSBAR_WIDTH_MM,
                    FRAME_J17A_CROSSBAR_LENGTH_MM,
                    FRAME_THICKNESS_MM,
                ),
                (float(x_mm), 0.0, frame_center_z_mm),
            )
        )

    j17a_seating_z_mm = (
        J17A_SOURCE_SEATING_PLANE_Z_MM
        + VERTICAL_EQUIPMENT_SHIFT_MM
        - J17A_SPACER_TOP_GAP_MM
    )
    spacer_parts = []
    for x_mm in j17a_x_mm:
        for y_mm in J17A_Y_MM:
            spacer_parts.append(
                cylinder_between(
                    np.asarray([x_mm, y_mm, frame_top_z_mm - 0.2]),
                    np.asarray([x_mm, y_mm, j17a_seating_z_mm]),
                    radius_mm=J17A_SPACER_OUTER_DIAMETER_MM / 2.0,
                )
            )
    adapter_solid = trimesh.boolean.union(
        [*parts, *spacer_parts],
        engine="manifold",
    )
    if not isinstance(adapter_solid, trimesh.Trimesh):
        raise RuntimeError("Adapter union did not return one mesh")

    hole_cutters = []
    for x_mm in PRO_X_MM:
        for y_mm in PRO_Y_MM:
            hole_cutters.append(
                cylinder_between(
                    np.asarray(
                        [x_mm, y_mm, frame_bottom_z_mm - 1.0]
                    ),
                    np.asarray([x_mm, y_mm, frame_top_z_mm + 1.0]),
                    radius_mm=PRO_HOLE_DIAMETER_MM / 2.0,
                )
            )
    for x_mm in j17a_x_mm:
        for y_mm in J17A_Y_MM:
            hole_cutters.append(
                cylinder_between(
                    np.asarray(
                        [x_mm, y_mm, frame_bottom_z_mm - 1.0]
                    ),
                    np.asarray(
                        [x_mm, y_mm, j17a_seating_z_mm + 1.0]
                    ),
                    radius_mm=J17A_HOLE_DIAMETER_MM / 2.0,
                )
            )
    cutter_union = trimesh.boolean.union(
        hole_cutters,
        engine="manifold",
    )
    adapter = trimesh.boolean.difference(
        [adapter_solid, cutter_union],
        engine="manifold",
    )
    if not isinstance(adapter, trimesh.Trimesh):
        raise RuntimeError("Adapter hole subtraction did not return one mesh")
    adapter.remove_unreferenced_vertices()

    metrics = {
        "frame_bottom_z_mm": round(frame_bottom_z_mm, 6),
        "frame_top_z_mm": round(frame_top_z_mm, 6),
        "j17a_seating_z_mm": round(j17a_seating_z_mm, 6),
        "j17a_spacer_height_mm": round(
            j17a_seating_z_mm - frame_top_z_mm + 0.2,
            6,
        ),
        "j17a_x_mm": j17a_x_mm.round(6).tolist(),
        "pro_axis_centers_mm": [
            [float(x_mm), float(y_mm), round(frame_center_z_mm, 6)]
            for x_mm in PRO_X_MM
            for y_mm in PRO_Y_MM
        ],
        "j17a_axis_centers_mm": [
            [float(x_mm), float(y_mm), round(j17a_seating_z_mm, 6)]
            for x_mm in j17a_x_mm
            for y_mm in J17A_Y_MM
        ],
    }
    return adapter, metrics


def main() -> None:
    MESH_ROOT.mkdir(parents=True, exist_ok=True)
    torso = load_mm("TORSO")
    interface_original = load_mm("FACTORY_INTERFACE")
    j17a_original = load_mm("J17A_SENSOR_CARRIER_SOURCE")
    sensor_shift_x_mm = (
        float(interface_original.bounds[1, 0])
        + INTERFACE_CLEARANCE_X_MM
        - float(j17a_original.bounds[0, 0])
    )
    sensor_shift = np.asarray(
        [sensor_shift_x_mm, 0.0, VERTICAL_EQUIPMENT_SHIFT_MM],
        dtype=float,
    )
    interface_shift = np.asarray(
        [0.0, 0.0, VERTICAL_EQUIPMENT_SHIFT_MM],
        dtype=float,
    )

    entries: list[dict[str, object]] = []
    context_meshes: dict[str, trimesh.Trimesh] = {}
    for name in CONTEXT_NODES:
        mesh = load_mm(name)
        if name != "TORSO":
            mesh.apply_translation(interface_shift)
        context_meshes[name] = mesh
        entries.append(
            {
                "node_name": name,
                "role": (
                    "source_body_context"
                    if name == "TORSO"
                    else "image_estimated_interface_on_candidate_adapter"
                ),
                **export_mm(mesh, MESH_ROOT / f"{name}.stl"),
            }
        )

    shifted_sensor_meshes: dict[str, trimesh.Trimesh] = {}
    for name in SENSOR_NODES:
        mesh = load_mm(name)
        mesh.apply_translation(sensor_shift)
        shifted_sensor_meshes[name] = mesh
        entries.append(
            {
                "node_name": name,
                "role": "unchanged_source_sensor_rigidly_repositioned",
                **export_mm(mesh, MESH_ROOT / f"{name}.stl"),
            }
        )

    adapter, adapter_contract = build_adapter(
        float(torso.bounds[1, 2]),
        sensor_shift_x_mm,
    )
    adapter_metrics = export_mm(
        adapter,
        MESH_ROOT / "PRO_TO_J17A_HIDDEN_PRINT_ADAPTER.stl",
    )
    entries.append(
        {
            "node_name": "PRO_TO_J17A_HIDDEN_PRINT_ADAPTER",
            "role": "print_adaptation",
            **adapter_metrics,
        }
    )

    j17a_fasteners = []
    for x_mm in adapter_contract["j17a_x_mm"]:
        for y_mm in J17A_Y_MM:
            j17a_fasteners.append(
                socket_head_reference(
                    np.asarray([x_mm, y_mm]),
                    float(adapter_contract["frame_top_z_mm"]) - 1.0,
                    float(adapter_contract["j17a_seating_z_mm"]) + 3.0,
                    float(adapter_contract["j17a_seating_z_mm"]) + 0.5,
                    float(adapter_contract["j17a_seating_z_mm"]) + 3.0,
                )
            )
    j17a_fastener_mesh = trimesh.util.concatenate(j17a_fasteners)
    entries.append(
        {
            "node_name": "J17A_FOUR_MOUNT_FASTENER_REFERENCES",
            "role": "official_video_axis_with_unresolved_length",
            **export_mm(
                j17a_fastener_mesh,
                MESH_ROOT / "J17A_FOUR_MOUNT_FASTENER_REFERENCES.stl",
            ),
        }
    )

    pro_fasteners = []
    for x_mm in PRO_X_MM:
        for y_mm in PRO_Y_MM:
            pro_fasteners.append(
                socket_head_reference(
                    np.asarray([x_mm, y_mm]),
                    float(adapter_contract["frame_bottom_z_mm"]) - 5.0,
                    float(adapter_contract["frame_top_z_mm"]) + 2.5,
                    float(adapter_contract["frame_top_z_mm"]),
                    float(adapter_contract["frame_top_z_mm"]) + 2.5,
                )
            )
    pro_fastener_mesh = trimesh.util.concatenate(pro_fasteners)
    entries.append(
        {
            "node_name": "LITE3_PRO_FOUR_M3_FASTENER_REFERENCES",
            "role": "official_74x94_axis_with_unresolved_length",
            **export_mm(
                pro_fastener_mesh,
                MESH_ROOT / "LITE3_PRO_FOUR_M3_FASTENER_REFERENCES.stl",
            ),
        }
    )

    interface = context_meshes["FACTORY_INTERFACE"]
    j17a = shifted_sensor_meshes["J17A_SENSOR_CARRIER_SOURCE"]
    interface_j17a_gap_x_mm = float(
        j17a.bounds[0, 0] - interface.bounds[1, 0]
    )
    if interface_j17a_gap_x_mm < INTERFACE_CLEARANCE_X_MM - 1.0e-5:
        raise RuntimeError("Final candidate lost the required Interface gap")

    interface_adapter = trimesh.boolean.intersection(
        [interface, adapter],
        engine="manifold",
    )
    interface_adapter_intersection_mm3 = (
        0.0
        if len(interface_adapter.faces) == 0
        else float(abs(interface_adapter.volume))
    )
    j17a_adapter = trimesh.boolean.intersection(
        [j17a, adapter],
        engine="manifold",
    )
    j17a_adapter_intersection_mm3 = (
        0.0
        if len(j17a_adapter.faces) == 0
        else float(abs(j17a_adapter.volume))
    )

    manifest = {
        "schema_version": 1,
        "purpose": "printable_static_replica_hidden_pro_to_j17a_adapter_candidate",
        "rigid_sensor_translation_mm": sensor_shift.round(6).tolist(),
        "interface_translation_mm": interface_shift.round(6).tolist(),
        "interface_to_j17a_gap_x_mm": round(
            interface_j17a_gap_x_mm,
            6,
        ),
        "adapter_contract": {
            **adapter_contract,
            "frame_thickness_mm": FRAME_THICKNESS_MM,
            "frame_spine_width_mm": FRAME_SPINE_WIDTH_MM,
            "frame_crossbar_width_mm": FRAME_CROSSBAR_WIDTH_MM,
            "pro_hole_pattern_mm": [74.0, 94.0],
            "pro_hole_diameter_mm": PRO_HOLE_DIAMETER_MM,
            "j17a_hole_pattern_mm": [110.0, 86.0],
            "j17a_hole_diameter_mm": J17A_HOLE_DIAMETER_MM,
            "spacer_outer_diameter_mm": (
                J17A_SPACER_OUTER_DIAMETER_MM
            ),
        },
        "collision_checks": {
            "interface_to_adapter_intersection_mm3": round(
                interface_adapter_intersection_mm3,
                9,
            ),
            "j17a_to_adapter_intersection_mm3": round(
                j17a_adapter_intersection_mm3,
                9,
            ),
            "adapter_bottom_to_torso_top_gap_mm": (
                FRAME_TO_TORSO_GAP_MM
            ),
        },
        "scale_1_4_print_metrics_mm": {
            "frame_thickness": FRAME_THICKNESS_MM / 4.0,
            "spine_width": FRAME_SPINE_WIDTH_MM / 4.0,
            "crossbar_width": FRAME_CROSSBAR_WIDTH_MM / 4.0,
            "spacer_outer_diameter": (
                J17A_SPACER_OUTER_DIAMETER_MM / 4.0
            ),
            "pro_hole_diameter": PRO_HOLE_DIAMETER_MM / 4.0,
            "j17a_hole_diameter": J17A_HOLE_DIAMETER_MM / 4.0,
        },
        "visible_source_geometry_change": "none",
        "adapter_claim_boundary": (
            "The skeletal frame is a disclosed printable-static-replica "
            "adaptation. It uses the official Pro and J17A hole-axis patterns "
            "but is not factory CAD, a load-rated real-robot bracket, or a "
            "fit claim for Dr Sun's unmeasured industrial computer."
        ),
        "fastener_claim_boundary": (
            "Four Pro M3 axes, four J17A installation locations, and two D435 "
            "M3 axes are represented. The visual shafts do not establish "
            "screw length, thread engagement, torque, or vibration safety."
        ),
        "entries": entries,
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"manifest={MANIFEST}")
    print(
        "rigid_sensor_translation_mm="
        f"{manifest['rigid_sensor_translation_mm']}"
    )
    print(
        "interface_to_j17a_gap_x_mm="
        f"{manifest['interface_to_j17a_gap_x_mm']}"
    )
    print(
        "adapter_components="
        f"{adapter_metrics['connected_components']}"
    )
    print(
        "adapter_volume_mm3="
        f"{adapter_metrics['volume_mm3']}"
    )
    print(
        "collision_checks="
        f"{manifest['collision_checks']}"
    )


if __name__ == "__main__":
    main()
