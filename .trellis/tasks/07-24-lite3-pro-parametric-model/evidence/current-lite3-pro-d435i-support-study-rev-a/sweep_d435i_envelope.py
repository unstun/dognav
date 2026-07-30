#!/usr/bin/env python3
"""Sweep the official D435i nominal envelope in front of the source upper stack."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import FreeCAD as App
import Part


PACKAGE_DIR = Path(__file__).resolve().parent
TASK_DIR = PACKAGE_DIR.parents[1]
REPO_ROOT = TASK_DIR.parents[2]
UPPER_DIR = TASK_DIR / "evidence/current-lite3-pro-source-upper-assembly-rev-a"
UPPER_FCSTD = UPPER_DIR / "cad/current-lite3-pro-source-upper-assembly-rev-a.FCStd"
UPPER_VALIDATION = UPPER_DIR / "validation.json"
INTERFACE_CONTRACT = (
    TASK_DIR
    / "evidence/current-lite3-pro-sensor-interface-contract-rev-a/interface_contract.json"
)
OUTPUT_PATH = PACKAGE_DIR / "envelope_sweep.json"

CAMERA_WIDTH_MM = 90.0
CAMERA_DEPTH_MM = 25.0
CAMERA_HEIGHT_MM = 25.0
CAMERA_DOWNWARD_TILT_DEG = 20.0
NOSE_EDGE_X_MM = 20.0
FRONT_MARGIN_MM = 2.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def camera_rotation() -> list[list[float]]:
    angle = math.radians(CAMERA_DOWNWARD_TILT_DEG)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    # Local +X is optical forward and tilts toward robot -Z.  Local +Y is
    # robot-left, and local +Z remains the camera's upward direction.
    return [
        [cosine, 0.0, sine],
        [0.0, 1.0, 0.0],
        [-sine, 0.0, cosine],
    ]


def matrix(rotation: list[list[float]], translation: list[float]) -> App.Matrix:
    result = App.Matrix()
    result.A11, result.A12, result.A13, result.A14 = (*rotation[0], translation[0])
    result.A21, result.A22, result.A23, result.A24 = (*rotation[1], translation[1])
    result.A31, result.A32, result.A33, result.A34 = (*rotation[2], translation[2])
    result.A41, result.A42, result.A43, result.A44 = 0.0, 0.0, 0.0, 1.0
    return result


def transformed(shape: Part.Shape, rotation: list[list[float]], translation: list[float]) -> Part.Shape:
    result = shape.copy()
    result.transformShape(matrix(rotation, translation), True)
    return result


def rounded_bounds(shape: Part.Shape) -> dict:
    bounds = shape.BoundBox
    return {
        "min": [round(bounds.XMin, 6), round(bounds.YMin, 6), round(bounds.ZMin, 6)],
        "max": [round(bounds.XMax, 6), round(bounds.YMax, 6), round(bounds.ZMax, 6)],
        "size": [round(bounds.XLength, 6), round(bounds.YLength, 6), round(bounds.ZLength, 6)],
    }


def main() -> None:
    for path in (UPPER_FCSTD, UPPER_VALIDATION, INTERFACE_CONTRACT):
        if not path.exists():
            raise FileNotFoundError(path)
    upper_validation = json.loads(UPPER_VALIDATION.read_text(encoding="utf-8"))
    interface_contract = json.loads(INTERFACE_CONTRACT.read_text(encoding="utf-8"))
    if not upper_validation.get("pass") or not interface_contract.get("pass"):
        raise RuntimeError("Input contracts must pass before camera sweep")

    document = App.openDocument(str(UPPER_FCSTD))
    components = {
        "j20a": document.getObject("J20ASourceBRep").Shape,
        "s410": document.getObject("S410SourceBRep").Shape,
        "mid360": document.getObject("Mid360OfficialBRep").Shape,
    }
    upper_compound = Part.makeCompound(list(components.values()))

    local_envelope = Part.makeBox(
        CAMERA_DEPTH_MM,
        CAMERA_WIDTH_MM,
        CAMERA_HEIGHT_MM,
        App.Vector(0.0, -CAMERA_WIDTH_MM * 0.5, -CAMERA_HEIGHT_MM * 0.5),
    )
    rotation = camera_rotation()
    rotated_at_origin = transformed(local_envelope, rotation, [0.0, 0.0, 0.0])
    rear_origin_x = (
        NOSE_EDGE_X_MM - FRONT_MARGIN_MM - rotated_at_origin.BoundBox.XMax
    )

    rows = []
    for sequence in range(33):
        rear_origin_z = 20.0 + 2.5 * sequence
        envelope = transformed(
            local_envelope, rotation, [rear_origin_x, 0.0, rear_origin_z]
        )
        intersections = {
            name: envelope.common(shape).Volume for name, shape in components.items()
        }
        total_intersection = sum(intersections.values())
        minimum_distance = (
            envelope.distToShape(upper_compound)[0]
            if total_intersection < 1.0e-6
            else 0.0
        )
        rows.append(
            {
                "rear_mount_origin_mm": [rear_origin_x, 0.0, rear_origin_z],
                "bounds_mm": rounded_bounds(envelope),
                "intersection_mm3": intersections,
                "total_intersection_mm3": total_intersection,
                "minimum_distance_to_upper_mm": minimum_distance,
                "collision_free": total_intersection < 1.0e-6,
                "above_local_deck": envelope.BoundBox.ZMin >= 0.0,
            }
        )

    fixed_nose_feasible = [
        row for row in rows if row["collision_free"] and row["above_local_deck"]
    ]

    # If the full conservative envelope cannot remain behind the nose edge,
    # solve for the smallest forward edge that clears the fixed source upper
    # assembly at each sampled height.  This quantifies the required overhang
    # instead of silently allowing an intersection.
    forward_search_rows = []
    rotated_front_extent = rotated_at_origin.BoundBox.XMax
    for sequence in range(17):
        rear_origin_z = 20.0 + 5.0 * sequence

        def envelope_at_front(front_edge_x: float):
            candidate_rear_x = front_edge_x - rotated_front_extent
            candidate = transformed(
                local_envelope,
                rotation,
                [candidate_rear_x, 0.0, rear_origin_z],
            )
            collision = candidate.common(upper_compound).Volume
            return candidate_rear_x, candidate, collision

        low_front = 18.0
        high_front = 52.0
        _, _, high_collision = envelope_at_front(high_front)
        if high_collision >= 1.0e-6:
            forward_search_rows.append(
                {
                    "rear_mount_origin_z_mm": rear_origin_z,
                    "feasible_within_search_range": False,
                    "searched_front_edge_range_mm": [low_front, high_front],
                }
            )
            continue
        for _ in range(14):
            middle_front = (low_front + high_front) * 0.5
            _, _, middle_collision = envelope_at_front(middle_front)
            if middle_collision < 1.0e-6:
                high_front = middle_front
            else:
                low_front = middle_front
        candidate_rear_x, candidate, candidate_collision = envelope_at_front(
            high_front
        )
        component_intersections = {
            name: candidate.common(shape).Volume
            for name, shape in components.items()
        }
        forward_search_rows.append(
            {
                "rear_mount_origin_mm": [
                    candidate_rear_x,
                    0.0,
                    rear_origin_z,
                ],
                "bounds_mm": rounded_bounds(candidate),
                "minimum_front_edge_x_mm": high_front,
                "overhang_beyond_measured_nose_mm": high_front - NOSE_EDGE_X_MM,
                "intersection_mm3": component_intersections,
                "total_intersection_mm3": sum(component_intersections.values()),
                "compound_intersection_mm3": candidate_collision,
                "minimum_distance_to_upper_mm": candidate.distToShape(
                    upper_compound
                )[0],
                "above_local_deck": candidate.BoundBox.ZMin >= 0.0,
                "feasible_within_search_range": True,
            }
        )

    forward_feasible = [
        row
        for row in forward_search_rows
        if row.get("feasible_within_search_range")
        and row["above_local_deck"]
        and row["total_intersection_mm3"] < 1.0e-5
    ]
    preferred = (
        min(
            forward_feasible,
            key=lambda row: (
                row["minimum_front_edge_x_mm"],
                row["rear_mount_origin_mm"][2],
            ),
        )
        if forward_feasible
        else None
    )
    report = {
        "schema_version": 1,
        "stage": "experiment_and_analysis",
        "status": (
            "d435i_envelope_sweep_pass_controlled_forward_offset_required"
            if not fixed_nose_feasible and preferred
            else "d435i_envelope_sweep_complete"
        ),
        "source": {
            "upper_fcstd": {
                "path": str(UPPER_FCSTD.relative_to(REPO_ROOT)),
                "sha256": sha256(UPPER_FCSTD),
            },
            "upper_validation": {
                "path": str(UPPER_VALIDATION.relative_to(REPO_ROOT)),
                "sha256": sha256(UPPER_VALIDATION),
            },
            "interface_contract": {
                "path": str(INTERFACE_CONTRACT.relative_to(REPO_ROOT)),
                "sha256": sha256(INTERFACE_CONTRACT),
            },
        },
        "camera_contract": {
            "official_nominal_envelope_mm": [
                CAMERA_WIDTH_MM,
                CAMERA_DEPTH_MM,
                CAMERA_HEIGHT_MM,
            ],
            "downward_optical_tilt_deg": CAMERA_DOWNWARD_TILT_DEG,
            "rotation_local_to_robot": rotation,
            "rear_mount_origin_x_mm": rear_origin_x,
            "front_margin_to_measured_nose_edge_mm": FRONT_MARGIN_MM,
            "two_m3_pitch_mm": interface_contract["interfaces"][
                "d435i_to_custom_camera_face"
            ]["pitch_mm"],
            "maximum_thread_insertion_mm": interface_contract["interfaces"][
                "d435i_to_custom_camera_face"
            ]["maximum_thread_insertion_mm"],
        },
        "fixed_nose_sweep": {
            "rear_origin_z_range_mm": [20.0, 100.0],
            "increment_mm": 2.5,
            "rows": rows,
            "collision_free_count": len(fixed_nose_feasible),
            "conclusion": (
                "no conservative-envelope placement stays behind the measured nose edge"
                if not fixed_nose_feasible
                else "at least one behind-nose placement is collision-free"
            ),
        },
        "forward_clearance_search": {
            "rear_origin_z_range_mm": [20.0, 100.0],
            "increment_mm": 5.0,
            "searched_front_edge_range_mm": [18.0, 52.0],
            "rows": forward_search_rows,
            "feasible_count": len(forward_feasible),
            "preferred_minimum_overhang": preferred,
        },
        "checks": {
            "upper_inputs_pass": True,
            "front_margin_is_exactly_2mm": all(
                abs(row["bounds_mm"]["max"][0] - 18.0) < 1.0e-5 for row in rows
            ),
            "fixed_nose_sweep_completed": len(rows) == 33,
            "forward_clearance_search_completed": len(forward_search_rows) == 17,
            "at_least_one_forward_collision_free_height_exists": bool(
                forward_feasible
            ),
            "preferred_height_is_above_deck": bool(
                preferred and preferred["above_local_deck"]
            ),
            "no_camera_support_solid_created": True,
            "no_print_release": True,
        },
        "claim_boundary": (
            "The sweep uses the official nominal D435i envelope and a selected "
            "20-degree downward optical direction. It determines whether the "
            "camera can remain behind the measured nose and quantifies the "
            "minimum conservative forward offset when it cannot. It does not "
            "validate the "
            "translated manufacturer B-rep, a support structure, FOV, cable bend, "
            "screw length, strength, or print release."
        ),
    }
    report["pass"] = all(report["checks"].values())
    OUTPUT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    App.closeDocument(document.Name)
    print(
        json.dumps(
            {
                "pass": report["pass"],
                "fixed_nose_collision_free_count": len(fixed_nose_feasible),
                "forward_feasible_count": len(forward_feasible),
                "preferred": preferred,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
