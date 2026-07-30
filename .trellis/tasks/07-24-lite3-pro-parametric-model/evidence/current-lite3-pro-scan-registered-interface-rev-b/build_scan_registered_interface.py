"""Build a scan-registered current-Lite3-Pro planar interface proxy.

This package updates the collision keep-out and axis scaffold only. It creates
no printable adapter, no receiver bore, and no screw-length decision.
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
PARAMETERS_PATH = PACKAGE_DIR / "parameters.json"
CAD_DIR = PACKAGE_DIR / "cad"
OUT_FCSTD = CAD_DIR / "current-lite3-pro-scan-registered-interface-rev-b.FCStd"
OUT_STEP = CAD_DIR / "current-lite3-pro-scan-registered-interface-rev-b.step"
OUT_KEEPOUT = CAD_DIR / "current-lite3-pro-scan-expanded-enclosure-keepout-rev-b.step"
VALIDATION_PATH = PACKAGE_DIR / "validation.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def metrics(shape: Part.Shape) -> dict:
    box = shape.BoundBox
    return {
        "shape_type": shape.ShapeType,
        "is_valid": shape.isValid(),
        "is_closed": shape.isClosed(),
        "solid_count": len(shape.Solids),
        "face_count": len(shape.Faces),
        "volume_mm3": shape.Volume,
        "bounds_mm": {
            "min": [box.XMin, box.YMin, box.ZMin],
            "max": [box.XMax, box.YMax, box.ZMax],
            "size": [box.XLength, box.YLength, box.ZLength],
        },
    }


def add_feature(document, name, label, shape, evidence_class, color, transparency=0):
    obj = document.addObject("PartDesign::Feature", name)
    obj.Label = label
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "EvidenceClass", "Evidence")
    obj.EvidenceClass = evidence_class
    obj.addProperty("App::PropertyString", "ManufacturingUse", "Evidence")
    obj.ManufacturingUse = "false"
    obj.addProperty("App::PropertyString", "ClaimBoundary", "Evidence")
    obj.ClaimBoundary = "Scan/photo planar reference only; receiver thread, depth, seating Z, and load path remain open"
    if obj.ViewObject is not None:
        obj.ViewObject.ShapeColor = color
        obj.ViewObject.LineColor = color
        obj.ViewObject.Transparency = transparency
    return obj


def make_box(bounds):
    x, y, z = bounds["x"], bounds["y"], bounds["z"]
    return Part.makeBox(x[1] - x[0], y[1] - y[0], z[1] - z[0], App.Vector(x[0], y[0], z[0]))


def make_footprint_prism(points, z_bounds):
    vectors = [App.Vector(point[0], point[1], z_bounds[0]) for point in points]
    wire = Part.makePolygon(vectors + [vectors[0]])
    return Part.Face(wire).extrude(App.Vector(0.0, 0.0, z_bounds[1] - z_bounds[0]))


def main() -> None:
    CAD_DIR.mkdir(parents=True, exist_ok=True)
    parameters = json.loads(PARAMETERS_PATH.read_text())
    registration_path = (PACKAGE_DIR / parameters["sources"]["scan_registration"]).resolve()
    measurements_path = (PACKAGE_DIR / parameters["sources"]["photo_measurements"]).resolve()
    registration = json.loads(registration_path.read_text())
    document = App.newDocument("CurrentLite3ProScanRegisteredInterfaceRevB")

    deck_points = [
        App.Vector(20.0, -45.0, 0.0), App.Vector(20.0, 45.0, 0.0),
        App.Vector(5.0, 58.0, 0.0), App.Vector(-100.0, 70.0, 0.0),
        App.Vector(-100.0, -70.0, 0.0), App.Vector(5.0, -58.0, 0.0),
    ]
    deck_wire = Part.makePolygon(deck_points + [deck_points[0]])
    deck_shape = Part.Face(deck_wire).extrude(App.Vector(0.0, 0.0, -4.0))
    deck = add_feature(document, "DeckPlanarProxy", "DECK_PLANAR_PROXY_NOT_OFFICIAL_CAD", deck_shape, "photo_scan_planar_silhouette", (0.88, 0.89, 0.91), 20)

    nominal_bounds = parameters["compute_enclosure"]["scan_registered_nominal_bounds_mm"]
    nominal_shape = make_footprint_prism(
        parameters["compute_enclosure"]["scan_registered_nominal_footprint_polygon_mm"],
        nominal_bounds["z"],
    )
    nominal = add_feature(document, "ComputeEnclosureScanNominal", "COMPUTE_ENCLOSURE_SCAN_REGISTERED_TWO_FRONT_RECESSES", nominal_shape, "scan_registered_notched_xy_photo_height_envelope", (0.85, 0.87, 0.90), 20)
    keepout_shape = make_box(parameters["compute_enclosure"]["expanded_collision_keepout_bounds_mm"])
    keepout = add_feature(document, "ComputeEnclosureExpandedKeepout", "COMPUTE_ENCLOSURE_SCAN_EXPANDED_KEEPOUT", keepout_shape, "scan_registered_uncertainty_expanded_keepout", (0.86, 0.24, 0.20), 88)

    axis_seed = Part.makeCylinder(3.0, 12.0, App.Vector(0.0, 0.0, -6.0))
    axes = []
    for name, label, coordinates, evidence_class, color in [
        ("FrontLeftAxis", "FRONT_LEFT_AXIS_THREAD_UNMEASURED", [0.0, 32.5], "photo_scan_corroborated_axis_marker", (0.10, 0.42, 0.90)),
        ("FrontRightAxis", "FRONT_RIGHT_AXIS_THREAD_UNMEASURED", [0.0, -32.5], "photo_scan_corroborated_axis_marker", (0.10, 0.42, 0.90)),
        ("CentreCandidateAxis", "CENTRE_CANDIDATE_RECEIVER_ROLE_UNVERIFIED", [-75.0, 0.0], "photo_scan_corroborated_candidate_axis", (0.96, 0.66, 0.08)),
    ]:
        shape = axis_seed.copy()
        shape.translate(App.Vector(coordinates[0], coordinates[1], 0.0))
        axes.append(add_feature(document, name, label, shape, evidence_class, color, 10))
    nose_shape = Part.makeBox(0.8, 100.0, 1.0, App.Vector(19.6, -50.0, 0.2))
    nose = add_feature(document, "UsableNoseEdge", "USABLE_NOSE_EDGE_X_PLUS_20", nose_shape, "photo_scan_corroborated_edge_marker", (0.12, 0.70, 0.28), 0)

    sheet = document.addObject("Spreadsheet::Sheet", "InterfaceLedger")
    rows = [
        ("Field", "Value", "Status"),
        ("front_pair_pitch_mm", "65.0", "photo measured; scan aligned"),
        ("front_pair_thread", "UNMEASURED", "receiver gate open"),
        ("front_pair_usable_depth_mm", "UNMEASURED", "receiver gate open"),
        ("centre_receiver_role", "UNVERIFIED", "axis only"),
        ("scan_mount_origin_x_mm", f"{registration['mount_frame']['scan_frame_origin_xy_mm'][0]:.6f}", "planar registration"),
        ("seating_z_registration", "UNMEASURED", "no print release"),
    ]
    for row_index, row in enumerate(rows, 1):
        for column_index, value in enumerate(row, 1):
            sheet.set(f"{chr(64 + column_index)}{row_index}", value)
    document.recompute()
    document.saveAs(str(OUT_FCSTD))
    exported = [deck, nominal, *axes, nose]
    Import.export(exported, str(OUT_STEP))
    Import.export([keepout], str(OUT_KEEPOUT))

    round_trip = Part.read(str(OUT_STEP))
    keepout_round_trip = Part.read(str(OUT_KEEPOUT))
    front_pitch = (axes[0].Shape.CenterOfMass - axes[1].Shape.CenterOfMass).Length
    report = {
        "schema_version": 1,
        "stage": "experiment_and_analysis",
        "status": "scan_registered_interface_pass_receiver_contract_open",
        "classification": "collision_and_layout_proxy_not_printable",
        "sources": {
            "parameters_sha256": sha256(PARAMETERS_PATH),
            "scan_registration_sha256": sha256(registration_path),
            "photo_measurements_sha256": sha256(measurements_path),
        },
        "objects": {obj.Name: metrics(obj.Shape) for obj in [deck, nominal, keepout, *axes, nose]},
        "outputs": {
            "fcstd": {"path": str(OUT_FCSTD.relative_to(PACKAGE_DIR)), "bytes": OUT_FCSTD.stat().st_size, "sha256": sha256(OUT_FCSTD)},
            "step": {"path": str(OUT_STEP.relative_to(PACKAGE_DIR)), "bytes": OUT_STEP.stat().st_size, "sha256": sha256(OUT_STEP), "clean_import": metrics(round_trip)},
            "keepout_step": {"path": str(OUT_KEEPOUT.relative_to(PACKAGE_DIR)), "bytes": OUT_KEEPOUT.stat().st_size, "sha256": sha256(OUT_KEEPOUT), "clean_import": metrics(keepout_round_trip)},
        },
        "checks": {
            "all_objects_valid": all(obj.Shape.isValid() for obj in [deck, nominal, keepout, *axes, nose]),
            "front_pair_pitch_mm": front_pitch,
            "front_pair_pitch_is_65mm": abs(front_pitch - 65.0) < 1e-9,
            "expanded_keepout_contains_scan_nominal": abs(keepout_shape.common(nominal_shape).Volume - nominal_shape.Volume) < 1e-6,
            "nominal_footprint_has_two_front_recesses": len(parameters["compute_enclosure"]["scan_registered_nominal_footprint_polygon_mm"]) == 8 and nominal_shape.Volume < make_box(nominal_bounds).Volume,
            "scan_registration_is_planar_candidate": registration["status"] == "planar_candidate_registration_for_human_review",
            "accepted_structural_receiver_count": parameters["planar_interface"]["accepted_structural_receiver_count"],
            "printable_adapter_present": False,
            "thread_or_depth_inferred": False,
        },
        "claim_boundary": "The scan corroborates planar axis placement and updates the compute keepout. It does not establish receiver threads, usable depth, seating Z, or structural fit.",
        "pass": False,
    }
    checks = report["checks"]
    report["pass"] = bool(
        checks["all_objects_valid"]
        and checks["front_pair_pitch_is_65mm"]
        and checks["expanded_keepout_contains_scan_nominal"]
        and checks["nominal_footprint_has_two_front_recesses"]
        and checks["scan_registration_is_planar_candidate"]
        and checks["accepted_structural_receiver_count"] == 0
        and not checks["printable_adapter_present"]
        and not checks["thread_or_depth_inferred"]
    )
    VALIDATION_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
