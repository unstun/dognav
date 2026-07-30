#!/usr/bin/env python3
"""Select and validate a low-front D435i envelope with service clearance."""

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
SWEEP_PATH = PACKAGE_DIR / "envelope_sweep.json"
UPPER_FCSTD = (
    TASK_DIR
    / "evidence/current-lite3-pro-source-upper-assembly-rev-a/cad/"
    "current-lite3-pro-source-upper-assembly-rev-a.FCStd"
)
OUTPUT_PATH = PACKAGE_DIR / "placement_selection.json"

TARGET_MINIMUM_CLEARANCE_MM = 2.0
CAMERA_WIDTH_MM = 90.0
CAMERA_DEPTH_MM = 25.0
CAMERA_HEIGHT_MM = 25.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def bounds(shape: Part.Shape) -> dict:
    box = shape.BoundBox
    return {
        "min": [box.XMin, box.YMin, box.ZMin],
        "max": [box.XMax, box.YMax, box.ZMax],
        "size": [box.XLength, box.YLength, box.ZLength],
    }


def main() -> None:
    if not SWEEP_PATH.exists() or not UPPER_FCSTD.exists():
        raise FileNotFoundError("Sweep or upper assembly is missing")
    sweep = json.loads(SWEEP_PATH.read_text(encoding="utf-8"))
    if not sweep.get("pass"):
        raise RuntimeError("D435i sweep must pass before placement selection")

    feasible_rows = [
        row
        for row in sweep["forward_clearance_search"]["rows"]
        if row.get("feasible_within_search_range") and row["above_local_deck"]
    ]
    low_front_rows = [
        row
        for row in feasible_rows
        if row["bounds_mm"]["min"][2] >= 8.0
        and row["bounds_mm"]["max"][2] <= 60.0
    ]
    if not low_front_rows:
        raise RuntimeError("No low-front D435i envelope candidate exists")
    tangent_candidate = min(
        low_front_rows,
        key=lambda row: (
            row["overhang_beyond_measured_nose_mm"],
            row["rear_mount_origin_mm"][2],
        ),
    )

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
    rotation = sweep["camera_contract"]["rotation_local_to_robot"]
    rotated = transformed(local_envelope, rotation, [0.0, 0.0, 0.0])
    rotated_front_extent = rotated.BoundBox.XMax
    origin_z = tangent_candidate["rear_mount_origin_mm"][2]

    def candidate_at_front(front_edge_x: float):
        rear_x = front_edge_x - rotated_front_extent
        envelope = transformed(local_envelope, rotation, [rear_x, 0.0, origin_z])
        distance = envelope.distToShape(upper_compound)[0]
        return rear_x, envelope, distance

    low_front = tangent_candidate["minimum_front_edge_x_mm"]
    high_front = low_front + 10.0
    _, _, high_distance = candidate_at_front(high_front)
    if high_distance < TARGET_MINIMUM_CLEARANCE_MM:
        raise RuntimeError("10 mm search allowance does not reach target clearance")
    for _ in range(14):
        middle = (low_front + high_front) * 0.5
        _, _, distance = candidate_at_front(middle)
        if distance >= TARGET_MINIMUM_CLEARANCE_MM:
            high_front = middle
        else:
            low_front = middle
    rear_x, envelope, minimum_distance = candidate_at_front(high_front)
    intersections = {
        name: envelope.common(shape).Volume for name, shape in components.items()
    }

    selection = {
        "schema_version": 1,
        "stage": "experiment_and_analysis",
        "status": "low_front_d435i_envelope_candidate_selected",
        "source": {
            "sweep": {
                "path": str(SWEEP_PATH.relative_to(REPO_ROOT)),
                "sha256": sha256(SWEEP_PATH),
            },
            "upper_fcstd": {
                "path": str(UPPER_FCSTD.relative_to(REPO_ROOT)),
                "sha256": sha256(UPPER_FCSTD),
            },
        },
        "selection_rule": {
            "camera_bounds_min_z_at_least_mm": 8.0,
            "camera_bounds_max_z_at_most_mm": 60.0,
            "objective": "minimum nose overhang among low-front candidates",
            "target_minimum_clearance_to_upper_mm": TARGET_MINIMUM_CLEARANCE_MM,
        },
        "tangent_candidate_from_sweep": tangent_candidate,
        "selected_candidate": {
            "rear_mount_origin_mm": [rear_x, 0.0, origin_z],
            "front_edge_x_mm": high_front,
            "overhang_beyond_measured_nose_mm": high_front - 20.0,
            "bounds_mm": bounds(envelope),
            "minimum_distance_to_upper_mm": minimum_distance,
            "intersection_mm3": intersections,
            "rotation_local_to_robot": rotation,
            "optical_axis_robot_frame": [
                rotation[0][0],
                rotation[1][0],
                rotation[2][0],
            ],
        },
        "checks": {
            "sweep_pass": True,
            "selected_from_low_front_subset": True,
            "minimum_clearance_at_least_2mm": minimum_distance
            >= TARGET_MINIMUM_CLEARANCE_MM - 1.0e-3,
            "zero_positive_volume_intersection": all(
                volume < 1.0e-6 for volume in intersections.values()
            ),
            "camera_bottom_at_least_8mm": envelope.BoundBox.ZMin >= 8.0,
            "camera_top_at_most_60mm": envelope.BoundBox.ZMax <= 60.0,
            "no_support_solid_or_print_release": True,
        },
        "remaining_gates": [
            "human review of the controlled camera overhang",
            "front-leg and terrain strike envelope",
            "USB connector and cable bend sweep",
            "camera support load path into the future lower adapter",
            "support strength and print validation",
        ],
        "claim_boundary": (
            "This is a conservative envelope placement candidate with 2 mm "
            "modeled clearance. It is not a final optical pose, a translated "
            "D435i B-rep validation, a support solid, leg-sweep clearance, or "
            "print/installation release."
        ),
    }
    selection["pass"] = all(selection["checks"].values())
    OUTPUT_PATH.write_text(
        json.dumps(selection, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    App.closeDocument(document.Name)
    print(
        json.dumps(
            {
                "pass": selection["pass"],
                "selected_candidate": selection["selected_candidate"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if not selection["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
