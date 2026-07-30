"""Build a non-printable current-Pro compact sensor layout with source B-reps."""

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
PROXY_DIR = TASK_DIR / "evidence/current-lite3-pro-measured-proxy-rev-a"
PROXY_STEP = PROXY_DIR / "cad/current-lite3-pro-photo-measured-proxy-rev-a.step"
KEEPOUT_STEP = PROXY_DIR / "cad/current-lite3-pro-expanded-enclosure-keepout-rev-a.step"
CAD_DIR = PACKAGE_DIR / "cad"
OUT_FCSTD = CAD_DIR / "current-lite3-pro-compact-sensor-layout-rev-a.FCStd"
OUT_STEP = CAD_DIR / "current-lite3-pro-compact-sensor-layout-rev-a.step"
VALIDATION_PATH = PACKAGE_DIR / "validation.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def rigid_source_to_robot_matrix(tx: float, ty: float, tz: float) -> App.Matrix:
    # new x = source z; new y = source x; new z = source y. This cyclic
    # permutation has determinant +1 and maps the source +Y mounting normal to
    # robot +Z.
    matrix = App.Matrix()
    matrix.A11, matrix.A12, matrix.A13, matrix.A14 = 0.0, 0.0, 1.0, tx
    matrix.A21, matrix.A22, matrix.A23, matrix.A24 = 1.0, 0.0, 0.0, ty
    matrix.A31, matrix.A32, matrix.A33, matrix.A34 = 0.0, 1.0, 0.0, tz
    matrix.A41, matrix.A42, matrix.A43, matrix.A44 = 0.0, 0.0, 0.0, 1.0
    return matrix


def transformed(shape: Part.Shape, matrix: App.Matrix) -> Part.Shape:
    result = shape.copy()
    result.transformShape(matrix, True)
    return result


def add_feature(document, name, label, shape, evidence_class, source_path=""):
    obj = document.addObject("PartDesign::Feature", name)
    obj.Label = label
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "EvidenceClass", "Evidence")
    obj.EvidenceClass = evidence_class
    obj.addProperty("App::PropertyString", "SourcePath", "Evidence")
    obj.SourcePath = source_path
    obj.addProperty("App::PropertyString", "ClaimBoundary", "Evidence")
    obj.ClaimBoundary = "Layout evidence only; no current-Pro printable support or physical-fit claim"
    return obj


def aabb_gap_x(first: Part.Shape, second: Part.Shape) -> float:
    a = first.BoundBox
    b = second.BoundBox
    if a.XMax < b.XMin:
        return b.XMin - a.XMax
    if b.XMax < a.XMin:
        return a.XMin - b.XMax
    return 0.0


def main() -> None:
    CAD_DIR.mkdir(parents=True, exist_ok=True)
    parameters = json.loads(PARAMETERS_PATH.read_text(encoding="utf-8"))
    mid_path = REPO_ROOT / parameters["source_geometry"]["mid360"]["path"]
    guard_path = REPO_ROOT / parameters["source_geometry"]["s410"]["path"]

    proxy_shape = Part.read(str(PROXY_STEP))
    keepout_shape = Part.read(str(KEEPOUT_STEP))
    mid_source = Part.read(str(mid_path))
    guard_source = Part.read(str(guard_path))

    guard_matrix = rigid_source_to_robot_matrix(-37.5, 0.0, 8.342020143325702)
    guard_shape = transformed(guard_source, guard_matrix)

    mid_bounds = mid_source.BoundBox
    mid_tx = -37.5 - (mid_bounds.ZMin + mid_bounds.ZMax) * 0.5
    mid_ty = -(mid_bounds.XMin + mid_bounds.XMax) * 0.5
    mid_tz = 8.0 - mid_bounds.YMin
    mid_matrix = rigid_source_to_robot_matrix(mid_tx, mid_ty, mid_tz)
    mid_shape = transformed(mid_source, mid_matrix)

    d435_shape = Part.makeBox(25.0, 90.0, 25.0, App.Vector(-7.5, -45.0, 84.0))
    support_wire = Part.makePolygon(
        [
            App.Vector(-92.0, -57.5, 6.0),
            App.Vector(18.0, -57.5, 6.0),
            App.Vector(18.0, 57.5, 6.0),
            App.Vector(-92.0, 57.5, 6.0),
            App.Vector(-92.0, -57.5, 6.0),
        ]
    )
    support_surface = Part.Face(support_wire)

    document = App.newDocument("CurrentLite3ProCompactSensorLayoutRevA")
    proxy = add_feature(document, "CurrentProMeasuredProxy", "CURRENT_PRO_PHOTO_MEASURED_PROXY", proxy_shape, "photo_measured_proxy", str(PROXY_STEP.relative_to(REPO_ROOT)))
    keepout = add_feature(document, "ExpandedComputeKeepout", "EXPANDED_COMPUTE_ENCLOSURE_KEEPOUT", keepout_shape, "uncertainty_expanded_keepout", str(KEEPOUT_STEP.relative_to(REPO_ROOT)))
    support = add_feature(document, "CompactSupportPlanningSurface", "ZERO_THICKNESS_COMPACT_SUPPORT_PLANNING_SURFACE_NOT_PRINTABLE", support_surface, "planning_surface_not_printable")
    guard = add_feature(document, "S410SourceBRep", "S410_SOURCE_BREP_RELATED_VENTURE_COMPONENT", guard_shape, "official_related_source_brep", str(guard_path.relative_to(REPO_ROOT)))
    mid = add_feature(document, "Mid360OfficialBRep", "MID360_OFFICIAL_BREP", mid_shape, "official_visual_and_interface_cad", str(mid_path.relative_to(REPO_ROOT)))
    d435 = add_feature(document, "D435iOfficialEnvelope", "D435I_OFFICIAL_90x25x25_ENVELOPE_NOT_TRANSLATED_CAD", d435_shape, "official_datasheet_envelope", parameters["source_geometry"]["d435i"]["path"])
    document.recompute()
    document.saveAs(str(OUT_FCSTD))
    Import.export([proxy, support, guard, mid, d435], str(OUT_STEP))

    round_trip = Part.read(str(OUT_STEP))
    sensor_shapes = {"s410": guard_shape, "mid360": mid_shape, "d435i_envelope": d435_shape}
    keepout_intersections = {name: shape.common(keepout_shape).Volume for name, shape in sensor_shapes.items()}
    report = {
        "schema_version": 1,
        "stage": "experiment_and_analysis",
        "status": "compact_source_brep_layout_pass_receiver_contract_open",
        "classification": "layout_assembly_not_printable",
        "source": {
            "parameters_sha256": sha256(PARAMETERS_PATH),
            "proxy_step_sha256": sha256(PROXY_STEP),
            "keepout_step_sha256": sha256(KEEPOUT_STEP),
            "mid360_sha256": sha256(mid_path),
            "s410_sha256": sha256(guard_path),
        },
        "transform_contract": {
            "source_to_robot_mapping": "new_x=source_z,new_y=source_x,new_z=source_y",
            "rotation_determinant": 1.0,
            "mid360_matrix": list(mid_matrix.A),
            "s410_matrix": list(guard_matrix.A),
        },
        "geometry": {
            "proxy": metrics(proxy_shape),
            "keepout": metrics(keepout_shape),
            "support_planning_surface": metrics(support_surface),
            "s410_source_brep": metrics(guard_shape),
            "mid360_official_brep": metrics(mid_shape),
            "d435i_official_envelope": metrics(d435_shape),
            "layout_step_clean_import": metrics(round_trip),
        },
        "clearance_mm": {
            "s410_to_expanded_compute_keepout_x": aabb_gap_x(guard_shape, keepout_shape),
            "mid360_to_expanded_compute_keepout_x": aabb_gap_x(mid_shape, keepout_shape),
            "d435i_front_to_measured_nose_edge": 20.0 - d435_shape.BoundBox.XMax,
        },
        "intersection_mm3": {
            "sensor_to_expanded_compute_keepout": keepout_intersections,
        },
        "checks": {
            "source_hashes_match_records": sha256(mid_path) == parameters["source_geometry"]["mid360"]["sha256"] and sha256(guard_path) == parameters["source_geometry"]["s410"]["sha256"],
            "rotation_is_proper": True,
            "all_source_and_envelope_shapes_valid": all(shape.isValid() for shape in [guard_shape, mid_shape, d435_shape]),
            "no_sensor_intersects_expanded_compute_keepout": all(value < 1.0e-6 for value in keepout_intersections.values()),
            "s410_has_at_least_5mm_fore_aft_clearance": aabb_gap_x(guard_shape, keepout_shape) >= 5.0,
            "d435i_stays_behind_measured_nose_edge": d435_shape.BoundBox.XMax <= 20.0,
            "support_is_zero_thickness_non_solid": len(support_surface.Solids) == 0 and support_surface.Volume == 0.0,
            "printable_lower_adapter_absent": True,
        },
        "outputs": {
            "fcstd": {"path": str(OUT_FCSTD.relative_to(PACKAGE_DIR)), "bytes": OUT_FCSTD.stat().st_size, "sha256": sha256(OUT_FCSTD)},
            "step": {"path": str(OUT_STEP.relative_to(PACKAGE_DIR)), "bytes": OUT_STEP.stat().st_size, "sha256": sha256(OUT_STEP)},
        },
        "claim_boundary": "The layout uses the official Mid-360 B-rep, the related-source S410 B-rep, and the official D435i nominal envelope. It proves only a compact collision-free plan against the photo keepout, not a carrier, fastener path, strength, optical validation, or physical fit.",
    }
    report["pass"] = all(report["checks"].values())
    VALIDATION_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
