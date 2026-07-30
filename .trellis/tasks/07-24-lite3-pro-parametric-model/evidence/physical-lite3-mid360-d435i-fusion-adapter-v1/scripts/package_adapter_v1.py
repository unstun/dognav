"""Package and validate the physical-Lite3 Mid-360 + D435i carrier V1.

The source solid is the separately classified Fusion print adaptation derived
from unchanged J17A/J20A manufacturer B-reps.  This script does not infer or
alter hidden Lite3 threads.  It creates a local editable FreeCAD source,
candidate-only STEP/STL, a parameter spreadsheet, and geometry/load reports.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

import FreeCAD as App
import Import
import Mesh
import Part


PACKAGE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_DIR.parents[4]
PARAMETERS_PATH = PACKAGE_DIR / "parameters.json"
SOURCE_STEP = (
    REPO_ROOT
    / ".trellis/tasks/07-24-lite3-pro-parametric-model/evidence"
    / "factory-step-j17a-j20a-monolithic-rear-web-print-adaptation-rev-b"
    / "j17a-j20a-monolithic-rear-web-print-adaptation-rev-b.step"
)
S410_STEP = (
    REPO_ROOT
    / "references/upstream/2026-07-24_lite3-venture-fast-livo2-hardware"
    / "source/original/1CA5-S410-Lidar protector.STEP"
)

CAD_DIR = PACKAGE_DIR / "cad"
VALIDATION_DIR = PACKAGE_DIR / "validation"
OUT_FCSTD = CAD_DIR / "lite3-mid360-d435i-monolithic-carrier-v1.FCStd"
OUT_STEP = CAD_DIR / "lite3-mid360-d435i-monolithic-carrier-v1.step"
OUT_STL = CAD_DIR / "lite3-mid360-d435i-monolithic-carrier-v1.stl"
GEOMETRY_REPORT = VALIDATION_DIR / "geometry_validation.json"
STRUCTURAL_REPORT = VALIDATION_DIR / "preliminary_structural_screen.json"

COMPONENT_NAME = "LITE3_MID360_D435I_MONOLITHIC_CARRIER_V1_NOT_OFFICIAL_CAD"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_shape(shape: Part.Shape) -> dict[str, int | float | bool | str | list[float]]:
    bounds = shape.BoundBox
    return {
        "shape_type": shape.ShapeType,
        "is_valid": shape.isValid(),
        "is_closed": shape.isClosed(),
        "solid_count": len(shape.Solids),
        "shell_count": len(shape.Shells),
        "face_count": len(shape.Faces),
        "edge_count": len(shape.Edges),
        "volume_mm3": shape.Volume,
        "bounds_mm": {
            "min": [bounds.XMin, bounds.YMin, bounds.ZMin],
            "max": [bounds.XMax, bounds.YMax, bounds.ZMax],
            "size": [bounds.XLength, bounds.YLength, bounds.ZLength],
        },
    }


def add_text_property(obj: App.DocumentObject, name: str, value: str) -> None:
    obj.addProperty("App::PropertyString", name, "Evidence")
    setattr(obj, name, value)


def add_parameter_sheet(document: App.Document, parameters: dict) -> None:
    sheet = document.addObject("Spreadsheet::Sheet", "Parameters")
    sheet.Label = "V1 parameters and evidence status"
    rows = [
        ("Parameter", "Value", "Evidence/status"),
        ("rear_web_width_mm", parameters["geometry_mm"]["rear_web_width"]["value"], parameters["geometry_mm"]["rear_web_width"]["evidence"]),
        ("rear_web_depth_mm", parameters["geometry_mm"]["rear_web_depth"]["value"], parameters["geometry_mm"]["rear_web_depth"]["evidence"]),
        ("rear_web_thickness_mm", parameters["geometry_mm"]["rear_web_thickness"]["value"], parameters["geometry_mm"]["rear_web_thickness"]["evidence"]),
        ("robot_front_pair_pitch_mm", parameters["geometry_mm"]["robot_front_pair_pitch"]["value"], parameters["geometry_mm"]["robot_front_pair_pitch"]["evidence"]),
        ("robot_rear_pair_pitch_mm", parameters["geometry_mm"]["robot_rear_pair_pitch"]["value"], parameters["geometry_mm"]["robot_rear_pair_pitch"]["evidence"]),
        ("interface_keepout_length_mm", parameters["interface_keepout_mm"]["nominal_length"], parameters["interface_keepout_mm"]["status"]),
        ("interface_keepout_width_mm", parameters["interface_keepout_mm"]["nominal_width"], parameters["interface_keepout_mm"]["status"]),
        ("interface_keepout_height_mm", parameters["interface_keepout_mm"]["nominal_height"], parameters["interface_keepout_mm"]["status"]),
        ("robot_usable_thread_depth_mm", "UNMEASURED", parameters["robot_interface"]["status"]),
        ("robot_final_screw_length_mm", "UNMEASURED", parameters["robot_interface"]["status"]),
    ]
    for row_index, row in enumerate(rows, start=1):
        for column_index, value in enumerate(row, start=1):
            column = chr(ord("A") + column_index - 1)
            sheet.set(f"{column}{row_index}", str(value))
    sheet.setColumnWidth("A", 260)
    sheet.setColumnWidth("B", 140)
    sheet.setColumnWidth("C", 420)


def build_structural_screen(parameters: dict, carrier_shape: Part.Shape) -> dict:
    guard_shape = Part.read(str(S410_STEP))
    guard_volume_mm3 = guard_shape.Volume
    carrier_density = parameters["structural_screen"]["carrier_density_g_cm3"]
    guard_density = parameters["structural_screen"]["guard_density_g_cm3"]
    carrier_mass_kg = carrier_shape.Volume * carrier_density * 1.0e-6
    guard_mass_kg = guard_volume_mm3 * guard_density * 1.0e-6
    mid360_mass_kg = 0.265
    d435i_mass_kg = 0.075
    allowance_kg = parameters["structural_screen"]["fastener_and_cable_allowance_kg"]
    total_mass_kg = carrier_mass_kg + guard_mass_kg + mid360_mass_kg + d435i_mass_kg + allowance_kg

    acceleration_g = parameters["structural_screen"]["design_acceleration_g"]
    load_factor = parameters["structural_screen"]["load_factor"]
    lever_arm_mm = parameters["structural_screen"]["cantilever_arm_mm"]
    force_n = total_mass_kg * 9.80665 * acceleration_g * load_factor
    moment_n_mm = force_n * lever_arm_mm

    width_mm = parameters["geometry_mm"]["rear_web_width"]["value"]
    thickness_mm = parameters["geometry_mm"]["rear_web_thickness"]["value"]
    section_modulus_mm3 = width_mm * thickness_mm**2 / 6.0
    nominal_bending_stress_mpa = moment_n_mm / section_modulus_mm3
    shear_area_mm2 = width_mm * thickness_mm
    nominal_average_shear_mpa = force_n / shear_area_mm2
    allowable_mpa = parameters["structural_screen"]["printed_allowable_stress_mpa"]
    nominal_margin = allowable_mpa / nominal_bending_stress_mpa

    return {
        "status": "screening_pass_with_physical_test_required" if nominal_margin >= 2.0 else "screening_redesign_required",
        "claim_boundary": "Simple continuous-web beam screen only; local notch stress, anisotropy, fatigue, impact, heat, creep, fastener pull-out, chassis strength, and real vibration are not validated.",
        "source_masses": {
            "mid360_kg": {"value": mid360_mass_kg, "source": "Livox official product specification"},
            "d435i_kg": {"value": d435i_mass_kg, "source": "RealSense D400 Series datasheet table 3-52"},
            "s410_guard_kg": {"value": guard_mass_kg, "method": "source STEP volume times declared steel density"},
            "printed_carrier_kg": {"value": carrier_mass_kg, "method": "candidate STEP volume times declared PA-CF density"},
            "fastener_and_cable_allowance_kg": allowance_kg,
            "screened_total_kg": total_mass_kg,
        },
        "load_case": {
            "acceleration_g": acceleration_g,
            "load_factor": load_factor,
            "lever_arm_mm": lever_arm_mm,
            "design_force_n": force_n,
            "design_moment_n_mm": moment_n_mm,
        },
        "rear_web_screen": {
            "width_mm": width_mm,
            "thickness_mm": thickness_mm,
            "section_modulus_mm3": section_modulus_mm3,
            "shear_area_mm2": shear_area_mm2,
            "nominal_bending_stress_mpa": nominal_bending_stress_mpa,
            "nominal_average_shear_mpa": nominal_average_shear_mpa,
            "declared_printed_allowable_mpa": allowable_mpa,
            "nominal_bending_margin": nominal_margin,
        },
        "required_before_motion": [
            "measure all four robot threads and usable depths",
            "print orientation and dried-filament coupon tensile/bend tests",
            "stationary 2x proof load for ten minutes",
            "fastener retention and witness-mark inspection",
            "tethered low-speed vibration trial with periodic crack inspection",
        ],
    }


def main() -> None:
    CAD_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    parameters = json.loads(PARAMETERS_PATH.read_text(encoding="utf-8"))
    if not SOURCE_STEP.exists():
        raise FileNotFoundError(SOURCE_STEP)
    if not S410_STEP.exists():
        raise FileNotFoundError(S410_STEP)

    source_shape = Part.read(str(SOURCE_STEP))
    source_metrics = count_shape(source_shape)
    if not (
        source_metrics["is_valid"]
        and source_metrics["is_closed"]
        and source_metrics["solid_count"] == 1
    ):
        raise RuntimeError(f"Source adaptation is not one valid closed solid: {source_metrics}")

    web_bounds = parameters["geometry_mm"]["rear_web_world_bounds"]
    target_web_thickness = parameters["geometry_mm"]["rear_web_thickness"]["value"]
    web_box = Part.makeBox(
        web_bounds["x_max"] - web_bounds["x_min"],
        web_bounds["y_max"] - web_bounds["y_min"],
        target_web_thickness,
        App.Vector(
            web_bounds["x_min"],
            web_bounds["y_min"],
            web_bounds["front_z"] - target_web_thickness,
        ),
    )
    web_source_engagement_mm3 = web_box.common(source_shape).Volume
    carrier_shape = source_shape.fuse(web_box).removeSplitter()
    carrier_metrics = count_shape(carrier_shape)
    if not (
        carrier_metrics["is_valid"]
        and carrier_metrics["is_closed"]
        and carrier_metrics["solid_count"] == 1
    ):
        raise RuntimeError(f"Thickened V1 carrier is not one valid closed solid: {carrier_metrics}")

    document = App.newDocument("Lite3_Mid360_D435i_Carrier_V1")
    carrier = document.addObject("PartDesign::Feature", "CarrierV1")
    carrier.Label = COMPONENT_NAME
    carrier.Shape = carrier_shape.copy()
    add_text_property(carrier, "EvidenceClass", "print_adaptation")
    add_text_property(carrier, "OfficialCAD", "false")
    add_text_property(carrier, "SourceGeometry", str(SOURCE_STEP.relative_to(REPO_ROOT)))
    add_text_property(carrier, "RobotInterfaceStatus", "cad_registration_only_pending_physical_thread_measurement")
    add_text_property(carrier, "ClaimBoundary", "No real-robot fit, strength, torque, fatigue, or motion approval")
    add_parameter_sheet(document, parameters)
    document.recompute()
    document.saveAs(str(OUT_FCSTD))

    Import.export([carrier], str(OUT_STEP))
    Mesh.export([carrier], str(OUT_STL))

    round_trip_shape = Part.read(str(OUT_STEP))
    round_trip_metrics = count_shape(round_trip_shape)
    mesh = Mesh.Mesh(str(OUT_STL))
    mesh_metrics = {
        "facet_count": mesh.CountFacets,
        "point_count": mesh.CountPoints,
        "edge_count": mesh.CountEdges,
        "is_solid": mesh.isSolid(),
        "count_components": mesh.countComponents(),
        "volume_mm3": mesh.Volume,
        "bound_box_mm": {
            "size": [mesh.BoundBox.XLength, mesh.BoundBox.YLength, mesh.BoundBox.ZLength]
        },
    }

    geometry_report = {
        "stage": "experiment_and_analysis",
        "status": "historical_internal_geometry_pass_rejected_for_current_pro_interface",
        "component": COMPONENT_NAME,
        "classification": "print_adaptation",
        "official_cad": False,
        "source": {
            "path": str(SOURCE_STEP.relative_to(REPO_ROOT)),
            "sha256": sha256(SOURCE_STEP),
            "metrics": source_metrics,
        },
        "candidate_metrics": carrier_metrics,
        "outputs": {
            "fcstd": {"path": str(OUT_FCSTD.relative_to(PACKAGE_DIR)), "bytes": OUT_FCSTD.stat().st_size, "sha256": sha256(OUT_FCSTD)},
            "step": {"path": str(OUT_STEP.relative_to(PACKAGE_DIR)), "bytes": OUT_STEP.stat().st_size, "sha256": sha256(OUT_STEP), "clean_import": round_trip_metrics},
            "stl": {"path": str(OUT_STL.relative_to(PACKAGE_DIR)), "bytes": OUT_STL.stat().st_size, "sha256": sha256(OUT_STL), "mesh": mesh_metrics},
        },
        "checks": {
            "source_one_valid_closed_solid": bool(source_metrics["is_valid"] and source_metrics["is_closed"] and source_metrics["solid_count"] == 1),
            "clean_step_one_valid_closed_solid": bool(round_trip_metrics["is_valid"] and round_trip_metrics["is_closed"] and round_trip_metrics["solid_count"] == 1),
            "stl_solid_one_component": bool(mesh_metrics["is_solid"] and mesh_metrics["count_components"] == 1),
            "source_to_candidate_added_volume_mm3": carrier_shape.Volume - source_shape.Volume,
            "volume_round_trip_relative_error": abs(round_trip_shape.Volume - carrier_shape.Volume) / carrier_shape.Volume,
            "stl_volume_relative_error": abs(mesh.Volume - carrier_shape.Volume) / carrier_shape.Volume,
        },
        "parameters_sha256": sha256(PARAMETERS_PATH),
        "claim_boundary": "The exported carrier retains internal V1 topology evidence only. Its Experience-style robot interface is rejected for the purchased current Lite3 Pro; do not fabricate or install it.",
    }
    geometry_report["pass"] = all(
        [
            geometry_report["checks"]["source_one_valid_closed_solid"],
            geometry_report["checks"]["clean_step_one_valid_closed_solid"],
            geometry_report["checks"]["stl_solid_one_component"],
            geometry_report["checks"]["volume_round_trip_relative_error"] < 1.0e-3,
            geometry_report["checks"]["stl_volume_relative_error"] < 5.0e-3,
        ]
    )
    GEOMETRY_REPORT.write_text(json.dumps(geometry_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    geometry_report["engineering_change"] = {
        "operation": "thicken_continuous_rear_web_toward_robot_rear",
        "target_thickness_mm": target_web_thickness,
        "web_source_engagement_mm3": web_source_engagement_mm3,
        "result_metrics": carrier_metrics,
        "source_geometry_preserved": True,
    }
    GEOMETRY_REPORT.write_text(json.dumps(geometry_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    structural_report = build_structural_screen(parameters, carrier_shape)
    STRUCTURAL_REPORT.write_text(json.dumps(structural_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"geometry": geometry_report, "structural": structural_report}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
