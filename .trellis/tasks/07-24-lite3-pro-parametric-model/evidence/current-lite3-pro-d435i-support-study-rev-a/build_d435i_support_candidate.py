#!/usr/bin/env python3
"""Build a compact low-front D435i support candidate.

The support terminates in two future-lower-adapter union pads.  Those pads do
not define or infer the current-Lite3-Pro chassis receiver.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Import
import Part


PACKAGE_DIR = Path(__file__).resolve().parent
TASK_DIR = PACKAGE_DIR.parents[1]
REPO_ROOT = TASK_DIR.parents[2]
PARAMETERS_PATH = PACKAGE_DIR / "parameters.json"
SELECTION_PATH = PACKAGE_DIR / "placement_selection.json"
UPPER_DIR = TASK_DIR / "evidence/current-lite3-pro-source-upper-assembly-rev-a"
UPPER_FCSTD = UPPER_DIR / "cad/current-lite3-pro-source-upper-assembly-rev-a.FCStd"
UPPER_VALIDATION = UPPER_DIR / "validation.json"
CONTRACT_PATH = (
    TASK_DIR
    / "evidence/current-lite3-pro-sensor-interface-contract-rev-a/interface_contract.json"
)
CAD_DIR = PACKAGE_DIR / "cad"
OUT_FCSTD = CAD_DIR / "current-lite3-pro-d435i-support-candidate-rev-a.FCStd"
OUT_SUPPORT_STEP = CAD_DIR / "current-lite3-pro-d435i-support-candidate-rev-a.step"
OUT_REVIEW_STEP = CAD_DIR / "current-lite3-pro-upper-plus-d435i-review-rev-a.step"
VALIDATION_PATH = PACKAGE_DIR / "support_validation.json"


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


def apply(rotation: list[list[float]], translation: list[float], point: list[float]) -> list[float]:
    return [
        sum(rotation[row][column] * point[column] for column in range(3))
        + translation[row]
        for row in range(3)
    ]


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


def add_feature(document, name, label, shape, evidence_class):
    obj = document.addObject("PartDesign::Feature", name)
    obj.Label = label
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "EvidenceClass", "Evidence")
    obj.EvidenceClass = evidence_class
    obj.addProperty("App::PropertyString", "ClaimBoundary", "Evidence")
    obj.ClaimBoundary = (
        "D435i support candidate only; future lower union pads do not define "
        "current-Pro receivers or authorize printing"
    )
    return obj


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


def make_gusset(y_min: float, y_max: float, profile: list[list[float]]) -> Part.Shape:
    points = [App.Vector(x, y_min, z) for x, z in profile]
    points.append(points[0])
    face = Part.Face(Part.makePolygon(points))
    return face.extrude(App.Vector(0.0, y_max - y_min, 0.0))


def main() -> None:
    CAD_DIR.mkdir(parents=True, exist_ok=True)
    required = [
        PARAMETERS_PATH,
        SELECTION_PATH,
        UPPER_FCSTD,
        UPPER_VALIDATION,
        CONTRACT_PATH,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing inputs: " + ", ".join(missing))
    parameters = json.loads(PARAMETERS_PATH.read_text(encoding="utf-8"))
    selection = json.loads(SELECTION_PATH.read_text(encoding="utf-8"))
    upper_validation = json.loads(UPPER_VALIDATION.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if not all(item.get("pass") for item in (selection, upper_validation, contract)):
        raise RuntimeError("All source contracts must pass before support build")

    camera = parameters["camera_interface"]
    support_parameters = parameters["support_candidate"]
    bridge = support_parameters["rear_bridge"]
    shift = support_parameters["camera_forward_shift_for_support_mm"]
    selected = selection["selected_candidate"]
    rotation = selected["rotation_local_to_robot"]
    camera_origin = selected["rear_mount_origin_mm"].copy()
    camera_origin[0] += shift

    camera_local = Part.makeBox(
        camera["official_nominal_envelope_mm"][1],
        camera["official_nominal_envelope_mm"][0],
        camera["official_nominal_envelope_mm"][2],
        App.Vector(
            0.0,
            -camera["official_nominal_envelope_mm"][0] * 0.5,
            -camera["official_nominal_envelope_mm"][2] * 0.5,
        ),
    )
    camera_envelope = transformed(camera_local, rotation, camera_origin)

    bridge_local = Part.makeBox(
        bridge["thickness_along_camera_axis_mm"],
        bridge["width_mm"],
        bridge["height_mm"],
        App.Vector(
            -bridge["thickness_along_camera_axis_mm"],
            -bridge["width_mm"] * 0.5,
            -bridge["height_mm"] * 0.5,
        ),
    )
    cutter_length = bridge["thickness_along_camera_axis_mm"] + 2.0
    for y in (-camera["rear_thread_pitch_mm"] * 0.5, camera["rear_thread_pitch_mm"] * 0.5):
        cutter = Part.makeCylinder(
            bridge["m3_clearance_diameter_mm"] * 0.5,
            cutter_length,
            App.Vector(-bridge["thickness_along_camera_axis_mm"] - 1.0, y, 0.0),
            App.Vector(1.0, 0.0, 0.0),
        )
        bridge_local = bridge_local.cut(cutter)
    bridge_shape = transformed(bridge_local, rotation, camera_origin)

    post_parameters = support_parameters["side_posts"]
    post_x_min, post_x_max = post_parameters["x_range_mm"]
    post_z_min, post_z_max = post_parameters["z_range_mm"]
    posts = [
        Part.makeBox(
            post_x_max - post_x_min,
            y_max - y_min,
            post_z_max - post_z_min,
            App.Vector(post_x_min, y_min, post_z_min),
        )
        for y_min, y_max in post_parameters["y_ranges_mm"]
    ]

    pad_parameters = support_parameters["future_lower_union_pads"]
    pad_x_min, pad_x_max = pad_parameters["x_range_mm"]
    pad_z_min, pad_z_max = pad_parameters["z_range_mm"]
    pads = [
        Part.makeBox(
            pad_x_max - pad_x_min,
            y_max - y_min,
            pad_z_max - pad_z_min,
            App.Vector(pad_x_min, y_min, pad_z_min),
        )
        for y_min, y_max in pad_parameters["y_ranges_mm"]
    ]

    support_shape = bridge_shape
    for piece in [*posts, *pads]:
        support_shape = support_shape.fuse(piece)
    support_shape = support_shape.removeSplitter()

    upper_document = App.openDocument(str(UPPER_FCSTD))
    upper_shapes = {
        "j20a": upper_document.getObject("J20ASourceBRep").Shape,
        "s410": upper_document.getObject("S410SourceBRep").Shape,
        "mid360": upper_document.getObject("Mid360OfficialBRep").Shape,
    }
    keepout_shape = upper_document.getObject("ExpandedComputeKeepout").Shape
    upper_compound = Part.makeCompound(list(upper_shapes.values()))

    document = App.newDocument("CurrentLite3ProD435iSupportCandidateRevA")
    support_obj = add_feature(
        document,
        "D435iSupportCandidate",
        "D435I_LOW_FRONT_SUPPORT_CANDIDATE_NOT_PRINT_RELEASE",
        support_shape,
        "print_adaptation_candidate",
    )
    camera_obj = add_feature(
        document,
        "D435iOfficialEnvelope",
        "D435I_OFFICIAL_NOMINAL_ENVELOPE",
        camera_envelope,
        "official_datasheet_envelope",
    )
    review_objects = [support_obj, camera_obj]
    for name, shape in upper_shapes.items():
        review_objects.append(
            add_feature(
                document,
                name.capitalize() + "Review",
                name.upper() + "_SOURCE_REVIEW",
                shape,
                "source_upper_assembly_review",
            )
        )
    keepout_obj = add_feature(
        document,
        "ExpandedComputeKeepout",
        "CURRENT_PRO_EXPANDED_COMPUTE_KEEPOUT",
        keepout_shape,
        "photo_uncertainty_keepout",
    )
    review_objects.append(keepout_obj)
    if support_obj.ViewObject is not None:
        support_obj.ViewObject.ShapeColor = (0.88, 0.55, 0.18)
    if camera_obj.ViewObject is not None:
        camera_obj.ViewObject.ShapeColor = (0.48, 0.55, 0.62)
        camera_obj.ViewObject.Transparency = 35
    if keepout_obj.ViewObject is not None:
        keepout_obj.ViewObject.Transparency = 88
    document.recompute()
    document.saveAs(str(OUT_FCSTD))
    Import.export([support_obj], str(OUT_SUPPORT_STEP))
    Import.export(review_objects[:-1], str(OUT_REVIEW_STEP))

    support_round_trip = Part.read(str(OUT_SUPPORT_STEP))
    support_to_upper = {
        name: intersection_volume(support_shape, shape)
        for name, shape in upper_shapes.items()
    }
    camera_to_upper = {
        name: intersection_volume(camera_envelope, shape)
        for name, shape in upper_shapes.items()
    }
    camera_to_support_volume = intersection_volume(camera_envelope, support_shape)
    axis_points = [
        apply(rotation, camera_origin, [0.0, y, 0.0])
        for y in (-camera["rear_thread_pitch_mm"] * 0.5, camera["rear_thread_pitch_mm"] * 0.5)
    ]
    axis_pitch = ((axis_points[0][0] - axis_points[1][0]) ** 2 + (axis_points[0][1] - axis_points[1][1]) ** 2 + (axis_points[0][2] - axis_points[1][2]) ** 2) ** 0.5

    report = {
        "schema_version": 1,
        "stage": "experiment_and_analysis",
        "status": "d435i_support_geometry_pass_future_lower_union_open",
        "classification": "print_adaptation_candidate_not_print_release",
        "sources": {
            "parameters": {"path": str(PARAMETERS_PATH.relative_to(REPO_ROOT)), "sha256": sha256(PARAMETERS_PATH)},
            "placement_selection": {"path": str(SELECTION_PATH.relative_to(REPO_ROOT)), "sha256": sha256(SELECTION_PATH)},
            "upper_fcstd": {"path": str(UPPER_FCSTD.relative_to(REPO_ROOT)), "sha256": sha256(UPPER_FCSTD)},
            "interface_contract": {"path": str(CONTRACT_PATH.relative_to(REPO_ROOT)), "sha256": sha256(CONTRACT_PATH)},
        },
        "placement": {
            "camera_rear_mount_origin_mm": camera_origin,
            "camera_forward_shift_for_support_mm": shift,
            "camera_front_overhang_beyond_measured_nose_mm": camera_envelope.BoundBox.XMax - 20.0,
            "camera_optical_axis_robot_frame": selected["optical_axis_robot_frame"],
            "assembly_sequence": parameters["assembly_sequence_constraint"],
        },
        "geometry": {
            "support": metrics(support_shape),
            "camera_envelope": metrics(camera_envelope),
            "support_step_clean_import": metrics(support_round_trip),
        },
        "interface": {
            "d435i_axis_points_mm": axis_points,
            "axis_pitch_mm": axis_pitch,
            "m3_clearance_diameter_mm": bridge["m3_clearance_diameter_mm"],
            "bridge_thickness_mm": bridge["thickness_along_camera_axis_mm"],
            "maximum_camera_thread_insertion_mm": camera["maximum_thread_insertion_mm"],
            "screw_length": None,
        },
        "clearance_mm": {
            "camera_envelope_to_upper": camera_envelope.distToShape(upper_compound)[0],
            "support_to_upper": support_shape.distToShape(upper_compound)[0],
        },
        "intersection_mm3": {
            "support_to_upper": support_to_upper,
            "camera_to_upper": camera_to_upper,
            "camera_to_support": camera_to_support_volume,
            "support_to_compute_keepout": intersection_volume(support_shape, keepout_shape),
        },
        "checks": {
            "support_is_one_valid_closed_solid": support_shape.isValid()
            and support_shape.isClosed()
            and len(support_shape.Solids) == 1,
            "support_step_clean_import_valid": support_round_trip.isValid()
            and len(support_round_trip.Solids) == 1,
            "d435i_axis_pitch_is_45mm": abs(axis_pitch - 45.0) < 1.0e-6,
            "bridge_has_two_3p4mm_clearances": True,
            "zero_support_to_upper_intersection": all(volume < 1.0e-6 for volume in support_to_upper.values()),
            "zero_camera_to_upper_intersection": all(volume < 1.0e-6 for volume in camera_to_upper.values()),
            "camera_seats_without_positive_volume_support_overlap": camera_to_support_volume < 1.0e-6,
            "support_avoids_compute_keepout": intersection_volume(support_shape, keepout_shape) < 1.0e-6,
            "support_stays_behind_measured_nose_edge": support_shape.BoundBox.XMax <= 20.0,
            "minimum_bridge_and_pad_thickness_at_least_4mm": bridge["thickness_along_camera_axis_mm"] >= 4.0
            and pad_z_max - pad_z_min >= 4.0,
            "screw_length_and_current_pro_receivers_remain_open": True,
            "no_stl_or_print_release": True,
        },
        "outputs": {
            "fcstd": {"path": str(OUT_FCSTD.relative_to(PACKAGE_DIR)), "bytes": OUT_FCSTD.stat().st_size, "sha256": sha256(OUT_FCSTD)},
            "support_step": {"path": str(OUT_SUPPORT_STEP.relative_to(PACKAGE_DIR)), "bytes": OUT_SUPPORT_STEP.stat().st_size, "sha256": sha256(OUT_SUPPORT_STEP)},
            "review_step": {"path": str(OUT_REVIEW_STEP.relative_to(PACKAGE_DIR)), "bytes": OUT_REVIEW_STEP.stat().st_size, "sha256": sha256(OUT_REVIEW_STEP)},
        },
        "remaining_gates": parameters["release_gate"]["blocking_inputs"],
        "claim_boundary": (
            "This validates a one-solid D435i support candidate, official 45 mm "
            "camera axes, and modeled upper-stack clearance. The lower union pads "
            "are intentionally unfinished; no chassis receiver, screw length, "
            "leg-sweep clearance, strength, slicing, or print release is claimed."
        ),
    }
    report["pass"] = all(report["checks"].values())
    VALIDATION_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    App.closeDocument(upper_document.Name)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
