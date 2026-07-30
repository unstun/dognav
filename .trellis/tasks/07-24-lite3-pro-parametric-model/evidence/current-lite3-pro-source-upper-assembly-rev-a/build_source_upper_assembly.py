#!/usr/bin/env python3
"""Build a rigid source-backed J20A + MID-360 + S410 upper assembly.

The assembly is registered from source hole axes and seating planes.  It is
kept independent of the unresolved current-Lite3-Pro chassis receiver and is
not exported as a print-release mesh.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import FreeCAD as App
import Import
import Part


PACKAGE_DIR = Path(__file__).resolve().parent
TASK_DIR = PACKAGE_DIR.parents[1]
REPO_ROOT = TASK_DIR.parents[2]
CONTRACT_DIR = TASK_DIR / "evidence/current-lite3-pro-sensor-interface-contract-rev-a"
CONTRACT_PATH = CONTRACT_DIR / "interface_contract.json"
PROXY_DIR = TASK_DIR / "evidence/current-lite3-pro-measured-proxy-rev-a"
KEEPOUT_STEP = PROXY_DIR / "cad/current-lite3-pro-expanded-enclosure-keepout-rev-a.step"

J20_STEP = REPO_ROOT / (
    "references/upstream/2026-07-24_lite3-venture-fast-livo2-hardware/"
    "source/original/1T21-J20A-small lidar base.STEP"
)
S410_STEP = REPO_ROOT / (
    "references/upstream/2026-07-24_lite3-venture-fast-livo2-hardware/"
    "source/original/1CA5-S410-Lidar protector.STEP"
)
MID_STEP = REPO_ROOT / (
    "references/upstream/2026-07-24_livox-mid360-cad/source/original/"
    "mid-360-asm.stp"
)

CAD_DIR = PACKAGE_DIR / "cad"
OUT_FCSTD = CAD_DIR / "current-lite3-pro-source-upper-assembly-rev-a.FCStd"
OUT_STEP = CAD_DIR / "current-lite3-pro-source-upper-assembly-rev-a.step"
VALIDATION_PATH = PACKAGE_DIR / "validation.json"

# The 15-degree source tilt pushes the S410 arch forward relative to its foot
# pattern.  A 5.5 mm rearward cluster shift keeps both the guard and J20A
# inside the photo-measured [-96, +20] mm front zone.
TARGET_PLAN_CENTRE_X_MM = -43.0
TARGET_PLAN_CENTRE_Y_MM = 0.0
TARGET_J20_MIN_Z_MM = 8.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mat_vec(rotation: list[list[float]], values: list[float]) -> list[float]:
    return [
        sum(rotation[row][column] * values[column] for column in range(3))
        for row in range(3)
    ]


def add(first: list[float], second: list[float]) -> list[float]:
    return [a + b for a, b in zip(first, second)]


def subtract(first: list[float], second: list[float]) -> list[float]:
    return [a - b for a, b in zip(first, second)]


def scale(values: list[float], factor: float) -> list[float]:
    return [factor * value for value in values]


def dot(first: list[float], second: list[float]) -> float:
    return sum(a * b for a, b in zip(first, second))


def norm(values: list[float]) -> float:
    return math.sqrt(dot(values, values))


def apply(rotation: list[list[float]], translation: list[float], point: list[float]) -> list[float]:
    return add(mat_vec(rotation, point), translation)


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


def determinant(rotation: list[list[float]]) -> float:
    return (
        rotation[0][0]
        * (rotation[1][1] * rotation[2][2] - rotation[1][2] * rotation[2][1])
        - rotation[0][1]
        * (rotation[1][0] * rotation[2][2] - rotation[1][2] * rotation[2][0])
        + rotation[0][2]
        * (rotation[1][0] * rotation[2][1] - rotation[1][1] * rotation[2][0])
    )


def metrics(shape: Part.Shape) -> dict:
    bounds = shape.BoundBox
    return {
        "shape_type": shape.ShapeType,
        "is_valid": shape.isValid(),
        "is_closed": shape.isClosed(),
        "solid_count": len(shape.Solids),
        "shell_count": len(shape.Shells),
        "face_count": len(shape.Faces),
        "volume_mm3": shape.Volume,
        "bounds_mm": {
            "min": [bounds.XMin, bounds.YMin, bounds.ZMin],
            "max": [bounds.XMax, bounds.YMax, bounds.ZMax],
            "size": [bounds.XLength, bounds.YLength, bounds.ZLength],
        },
    }


def add_feature(document, name, label, shape, evidence_class, source_path=""):
    obj = document.addObject("PartDesign::Feature", name)
    obj.Label = label
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "EvidenceClass", "Evidence")
    obj.EvidenceClass = evidence_class
    obj.addProperty("App::PropertyString", "SourcePath", "Evidence")
    obj.SourcePath = source_path
    obj.addProperty("App::PropertyString", "ClaimBoundary", "Evidence")
    obj.ClaimBoundary = (
        "Source-backed upper assembly only; no current-Pro lower receiver, "
        "screw-length, strength, or print-release claim"
    )
    return obj


def plane_point(tangent: list[float], normal: list[float], u: float, v: float, n: float) -> list[float]:
    # J20 source width axis is source +Z.
    return add(add(scale(tangent, u), [0.0, 0.0, v]), scale(normal, n))


def maximum_nearest_residual(first: list[list[float]], second: list[list[float]]) -> float:
    return max(min(norm(subtract(point, target)) for target in second) for point in first)


def maximum_nearest_axis_line_residual(
    first: list[list[float]], second: list[list[float]], axis: list[float]
) -> float:
    axis_length = norm(axis)
    unit_axis = [value / axis_length for value in axis]
    residuals = []
    for point in first:
        candidates = []
        for target in second:
            delta = subtract(point, target)
            lateral = subtract(delta, scale(unit_axis, dot(delta, unit_axis)))
            candidates.append(norm(lateral))
        residuals.append(min(candidates))
    return max(residuals)


def intersection_volume(first: Part.Shape, second: Part.Shape) -> float:
    first_bounds = first.BoundBox
    second_bounds = second.BoundBox
    if (
        first_bounds.XMax < second_bounds.XMin
        or second_bounds.XMax < first_bounds.XMin
        or first_bounds.YMax < second_bounds.YMin
        or second_bounds.YMax < first_bounds.YMin
        or first_bounds.ZMax < second_bounds.ZMin
        or second_bounds.ZMax < first_bounds.ZMin
    ):
        return 0.0
    return first.common(second).Volume


def aabb_x_gap(first: Part.Shape, second: Part.Shape) -> float:
    a = first.BoundBox
    b = second.BoundBox
    if a.XMax < b.XMin:
        return b.XMin - a.XMax
    if b.XMax < a.XMin:
        return a.XMin - b.XMax
    return 0.0


def main() -> None:
    CAD_DIR.mkdir(parents=True, exist_ok=True)
    required = [CONTRACT_PATH, KEEPOUT_STEP, J20_STEP, S410_STEP, MID_STEP]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing inputs: " + ", ".join(missing))

    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if not contract.get("pass"):
        raise RuntimeError("Sensor-side interface contract is not passing")

    j20_source = Part.read(str(J20_STEP))
    s410_source = Part.read(str(S410_STEP))
    mid_source = Part.read(str(MID_STEP))
    keepout_shape = Part.read(str(KEEPOUT_STEP))

    # Proper rotation: J20 source +X -> robot +X, source +Z -> robot -Y,
    # source +Y -> robot +Z.  Its 15-degree mounting normal therefore tilts
    # toward robot-forward +X.
    j20_rotation = [
        [1.0, 0.0, 0.0],
        [0.0, 0.0, -1.0],
        [0.0, 1.0, 0.0],
    ]
    j20_unshifted = transformed(j20_source, j20_rotation, [0.0, 0.0, 0.0])
    j20_bounds = j20_unshifted.BoundBox
    j20_translation = [
        TARGET_PLAN_CENTRE_X_MM - (j20_bounds.XMin + j20_bounds.XMax) * 0.5,
        TARGET_PLAN_CENTRE_Y_MM - (j20_bounds.YMin + j20_bounds.YMax) * 0.5,
        TARGET_J20_MIN_Z_MM - j20_bounds.ZMin,
    ]
    j20_shape = transformed(j20_source, j20_rotation, j20_translation)

    angle = math.radians(15.0)
    tangent = [math.cos(angle), -math.sin(angle), 0.0]
    normal = [math.sin(angle), math.cos(angle), 0.0]
    source_to_j20_plane_rotation = [
        [math.cos(angle), math.sin(angle), 0.0],
        [-math.sin(angle), math.cos(angle), 0.0],
        [0.0, 0.0, 1.0],
    ]

    # Compose J20 source-to-robot and sensor-source-to-J20-plane rotations.
    sensor_rotation = [
        [
            sum(
                j20_rotation[row][inner]
                * source_to_j20_plane_rotation[inner][column]
                for inner in range(3)
            )
            for column in range(3)
        ]
        for row in range(3)
    ]

    mid_contract = contract["interfaces"]["mid360_to_j20a"]
    s410_contract = contract["interfaces"]["s410_to_j20a"]

    j20_mid_u = mid_contract["j20a_pattern"]["centre_mm"][0]
    j20_mid_v = mid_contract["j20a_pattern"]["centre_mm"][1]
    j20_mid_n = mid_contract["seating_planes_source_projection_mm"][
        "j20a_outer_plane_along_normal"
    ]
    mid_gap = mid_contract["seating_planes_source_projection_mm"][
        "preserved_modeled_gap_mm"
    ]
    mid_source_u = mid_contract["mid360_pattern"]["centre_mm"][0]
    mid_source_v = mid_contract["mid360_pattern"]["centre_mm"][1]
    mid_source_y = mid_contract["seating_planes_source_projection_mm"][
        "mid360_mount_face_along_source_y"
    ]
    mid_target_j20 = plane_point(
        tangent, normal, j20_mid_u, j20_mid_v, j20_mid_n + mid_gap
    )
    mid_target_robot = apply(j20_rotation, j20_translation, mid_target_j20)
    mid_source_seat = [mid_source_u, mid_source_y, mid_source_v]
    mid_translation = subtract(
        mid_target_robot, mat_vec(sensor_rotation, mid_source_seat)
    )
    mid_shape = transformed(mid_source, sensor_rotation, mid_translation)

    j20_s410_u = s410_contract["j20a_pattern"]["centre_mm"][0]
    j20_s410_v = s410_contract["j20a_pattern"]["centre_mm"][1]
    j20_s410_n = s410_contract["seating_planes_source_projection_mm"][
        "j20a_outer_plane_along_normal"
    ]
    s410_source_u = s410_contract["s410_pattern"]["centre_mm"][0]
    s410_source_v = s410_contract["s410_pattern"]["centre_mm"][1]
    s410_source_y = s410_contract["seating_planes_source_projection_mm"][
        "s410_foot_seat_plane_along_source_y"
    ]
    s410_target_j20 = plane_point(
        tangent, normal, j20_s410_u, j20_s410_v, j20_s410_n
    )
    s410_target_robot = apply(j20_rotation, j20_translation, s410_target_j20)
    s410_source_seat = [s410_source_u, s410_source_y, s410_source_v]
    s410_translation = subtract(
        s410_target_robot, mat_vec(sensor_rotation, s410_source_seat)
    )
    s410_shape = transformed(s410_source, sensor_rotation, s410_translation)

    # Axis registration is evaluated on the source-backed pattern centres.
    j20_mid_axis_points = [
        apply(
            j20_rotation,
            j20_translation,
            plane_point(tangent, normal, point[0], point[1], j20_mid_n),
        )
        for point in mid_contract["j20a_pattern"]["points_mm"]
    ]
    mid_axis_points = [
        apply(sensor_rotation, mid_translation, [point[0], mid_source_y, point[1]])
        for point in mid_contract["mid360_pattern"]["points_mm"]
    ]
    j20_s410_axis_points = [
        apply(
            j20_rotation,
            j20_translation,
            plane_point(tangent, normal, point[0], point[1], j20_s410_n),
        )
        for point in s410_contract["j20a_pattern"]["points_mm"]
    ]
    s410_axis_points = [
        apply(sensor_rotation, s410_translation, [point[0], s410_source_y, point[1]])
        for point in s410_contract["s410_pattern"]["points_mm"]
    ]
    mount_normal_robot = mat_vec(j20_rotation, normal)
    mid_axis_residual = maximum_nearest_axis_line_residual(
        mid_axis_points, j20_mid_axis_points, mount_normal_robot
    )
    s410_axis_residual = maximum_nearest_axis_line_residual(
        s410_axis_points, j20_s410_axis_points, mount_normal_robot
    )

    document = App.newDocument("CurrentLite3ProSourceUpperAssemblyRevA")
    j20_obj = add_feature(
        document,
        "J20ASourceBRep",
        "J20A_RELATED_SOURCE_SECOND_LAYER",
        j20_shape,
        "official_related_venture_source_brep",
        str(J20_STEP.relative_to(REPO_ROOT)),
    )
    s410_obj = add_feature(
        document,
        "S410SourceBRep",
        "S410_RELATED_SOURCE_GUARD",
        s410_shape,
        "official_related_venture_source_brep",
        str(S410_STEP.relative_to(REPO_ROOT)),
    )
    mid_obj = add_feature(
        document,
        "Mid360OfficialBRep",
        "MID360_OFFICIAL_BREP",
        mid_shape,
        "official_visual_and_interface_cad",
        str(MID_STEP.relative_to(REPO_ROOT)),
    )
    keepout_obj = add_feature(
        document,
        "ExpandedComputeKeepout",
        "CURRENT_PRO_EXPANDED_COMPUTE_KEEPOUT_NOT_EXPORT_PART",
        keepout_shape,
        "photo_uncertainty_keepout",
        str(KEEPOUT_STEP.relative_to(REPO_ROOT)),
    )
    for obj, color in (
        (j20_obj, (0.72, 0.70, 0.64)),
        (s410_obj, (0.20, 0.22, 0.25)),
        (mid_obj, (0.28, 0.42, 0.66)),
        (keepout_obj, (0.85, 0.25, 0.20)),
    ):
        if obj.ViewObject is not None:
            obj.ViewObject.ShapeColor = color
    if keepout_obj.ViewObject is not None:
        keepout_obj.ViewObject.Transparency = 85
    document.recompute()
    document.saveAs(str(OUT_FCSTD))
    Import.export([j20_obj, s410_obj, mid_obj], str(OUT_STEP))

    combined_shape = Part.makeCompound([j20_shape, s410_shape, mid_shape])
    round_trip = Part.read(str(OUT_STEP))
    component_intersections = {
        "j20a_mid360": intersection_volume(j20_shape, mid_shape),
        "j20a_s410": intersection_volume(j20_shape, s410_shape),
        "mid360_s410": intersection_volume(mid_shape, s410_shape),
    }
    keepout_intersections = {
        "j20a": intersection_volume(j20_shape, keepout_shape),
        "mid360": intersection_volume(mid_shape, keepout_shape),
        "s410": intersection_volume(s410_shape, keepout_shape),
    }
    combined_bounds = combined_shape.BoundBox
    report = {
        "schema_version": 1,
        "stage": "experiment_and_analysis",
        "status": "source_upper_assembly_geometry_pass_lower_interface_open",
        "classification": "source_backed_upper_assembly_not_print_release",
        "sources": {
            "interface_contract": {
                "path": str(CONTRACT_PATH.relative_to(REPO_ROOT)),
                "sha256": sha256(CONTRACT_PATH),
            },
            "j20a": {"path": str(J20_STEP.relative_to(REPO_ROOT)), "sha256": sha256(J20_STEP)},
            "s410": {"path": str(S410_STEP.relative_to(REPO_ROOT)), "sha256": sha256(S410_STEP)},
            "mid360": {"path": str(MID_STEP.relative_to(REPO_ROOT)), "sha256": sha256(MID_STEP)},
            "current_pro_keepout": {"path": str(KEEPOUT_STEP.relative_to(REPO_ROOT)), "sha256": sha256(KEEPOUT_STEP)},
        },
        "transform_contract": {
            "j20a_rotation": j20_rotation,
            "j20a_translation_mm": j20_translation,
            "sensor_rotation": sensor_rotation,
            "mid360_translation_mm": mid_translation,
            "s410_translation_mm": s410_translation,
            "rotation_determinants": {
                "j20a": determinant(j20_rotation),
                "mid360_and_s410": determinant(sensor_rotation),
            },
            "mount_normal_robot_frame": mount_normal_robot,
        },
        "axis_registration": {
            "mid360_to_j20a_maximum_residual_mm": mid_axis_residual,
            "s410_to_j20a_maximum_residual_mm": s410_axis_residual,
            "mid360_modeled_seating_gap_mm": mid_gap,
        },
        "geometry": {
            "j20a": metrics(j20_shape),
            "s410": metrics(s410_shape),
            "mid360": metrics(mid_shape),
            "combined_upper_assembly": metrics(combined_shape),
            "step_clean_import": metrics(round_trip),
        },
        "intersection_mm3": {
            "between_upper_components": component_intersections,
            "to_current_pro_expanded_compute_keepout": keepout_intersections,
        },
        "clearance_mm": {
            "combined_upper_to_expanded_compute_keepout_x": aabb_x_gap(
                combined_shape, keepout_shape
            ),
            "combined_front_to_measured_nose_edge": 20.0 - combined_bounds.XMax,
        },
        "checks": {
            "source_hashes_match_interface_contract": (
                sha256(J20_STEP) == contract["source_files"]["j20a_step"]["sha256"]
                and sha256(S410_STEP) == contract["source_files"]["s410_step"]["sha256"]
                and sha256(MID_STEP) == contract["source_files"]["mid360_step"]["sha256"]
            ),
            "proper_rotations": abs(determinant(j20_rotation) - 1.0) < 1.0e-9
            and abs(determinant(sensor_rotation) - 1.0) < 1.0e-9,
            "all_source_shapes_valid": all(
                shape.isValid() for shape in (j20_shape, s410_shape, mid_shape)
            ),
            "mid360_axes_registered_below_0p01mm": mid_axis_residual < 0.01,
            "s410_axes_registered_below_0p01mm": s410_axis_residual < 0.01,
            "no_positive_volume_upper_component_collision": all(
                volume < 1.0e-4 for volume in component_intersections.values()
            ),
            "no_upper_component_hits_compute_keepout": all(
                volume < 1.0e-4 for volume in keepout_intersections.values()
            ),
            "upper_assembly_stays_behind_measured_nose_edge": combined_bounds.XMax <= 20.0,
            "upper_assembly_stays_ahead_of_expanded_compute_keepout": combined_bounds.XMin >= -96.0,
            "upper_assembly_stays_inside_compact_width": combined_bounds.YMin >= -57.5
            and combined_bounds.YMax <= 57.5,
            "step_clean_import_valid": round_trip.isValid(),
            "no_stl_or_screw_length_released": True,
        },
        "outputs": {
            "fcstd": {
                "path": str(OUT_FCSTD.relative_to(PACKAGE_DIR)),
                "bytes": OUT_FCSTD.stat().st_size,
                "sha256": sha256(OUT_FCSTD),
            },
            "step": {
                "path": str(OUT_STEP.relative_to(PACKAGE_DIR)),
                "bytes": OUT_STEP.stat().st_size,
                "sha256": sha256(OUT_STEP),
            },
        },
        "remaining_gates": [
            "design a separate compact D435i support around its 2 x M3 contract",
            "confirm current-Pro receiver threads and usable depths",
            "select and validate the lower structural load path",
            "validate driver and cable service corridors",
            "validate print adaptation strength and slicing before release",
        ],
        "claim_boundary": (
            "This validates a rigid, source-backed J20A/MID-360/S410 upper "
            "assembly against source axes and the measured current-Pro keepout. "
            "It is not a current-Pro lower adapter, screw-length decision, "
            "strength result, printable part release, or physical-fit validation."
        ),
    }
    report["pass"] = all(report["checks"].values())
    VALIDATION_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
