"""Build a lightweight current-Lite3-Pro physical proxy from photo measurements.

This is measurement and collision-layout geometry, not official robot CAD and
not a printable adapter.  Hole-like objects are axis markers only: the user
photographs do not establish a thread, usable depth, receiver material, or
load path.
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
GATE_DIR = TASK_DIR / "evidence/current-lite3-pro-lower-adapter-measurement-gate"
MEASUREMENTS_PATH = GATE_DIR / "measurement_results.json"
SOURCE_INDEX_PATH = (
    GATE_DIR
    / "source/2026-07-30-user-physical-measurements/source_index.json"
)
CAD_DIR = PACKAGE_DIR / "cad"
VALIDATION_PATH = PACKAGE_DIR / "validation.json"
OUT_FCSTD = CAD_DIR / "current-lite3-pro-photo-measured-proxy-rev-a.FCStd"
OUT_STEP = CAD_DIR / "current-lite3-pro-photo-measured-proxy-rev-a.step"
OUT_KEEPOUT_STEP = CAD_DIR / "current-lite3-pro-expanded-enclosure-keepout-rev-a.step"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def shape_metrics(shape: Part.Shape) -> dict:
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


def add_string(obj: App.DocumentObject, name: str, value: str) -> None:
    obj.addProperty("App::PropertyString", name, "Evidence")
    setattr(obj, name, value)


def add_feature(
    document: App.Document,
    name: str,
    label: str,
    shape: Part.Shape,
    evidence_class: str,
    color: tuple[float, float, float],
    transparency: int = 0,
) -> App.DocumentObject:
    obj = document.addObject("PartDesign::Feature", name)
    obj.Label = label
    obj.Shape = shape
    add_string(obj, "EvidenceClass", evidence_class)
    add_string(obj, "OfficialCAD", "false")
    add_string(obj, "ClaimBoundary", "Photo-measured proxy or axis marker only; not a printable part or receiver contract")
    # ``freecadcmd`` has no GUI view provider.  Preserve the requested display
    # metadata when a GUI provider exists, while keeping headless CAD export
    # authoritative.
    if obj.ViewObject is not None:
        obj.ViewObject.ShapeColor = color
        obj.ViewObject.LineColor = color
        obj.ViewObject.Transparency = transparency
    return obj


def add_parameter_sheet(document: App.Document, measurements: dict) -> None:
    values = measurements["measurements"]
    sheet = document.addObject("Spreadsheet::Sheet", "MeasuredParameters")
    sheet.Label = "Current Lite3 Pro photo-measured parameters"
    rows = [
        ("Parameter", "Value mm", "Uncertainty mm", "Evidence status"),
        ("front_pair_lateral_pitch", 65.0, 1.0, "two-view photo-measured axis pitch"),
        ("nose_edge_x", 20.0, 2.0, "photo-measured edge datum"),
        ("centre_candidate_axis_x", -75.0, 3.0, "axis visible; receiver role unverified"),
        ("compute_enclosure_front_x", -100.0, 4.0, "photo-measured external edge"),
        ("compute_enclosure_length", values["compute_enclosure_length_mm"]["value"], values["compute_enclosure_length_mm"]["uncertainty_mm"], "external envelope"),
        ("compute_enclosure_width", values["compute_enclosure_width_mm"]["value"], values["compute_enclosure_width_mm"]["uncertainty_mm"], "external envelope"),
        ("compute_enclosure_height", values["compute_enclosure_height_mm"]["value"], values["compute_enclosure_height_mm"]["uncertainty_mm"], "external envelope"),
        ("front_pair_thread", "UNMEASURED", "", "print release blocked"),
        ("front_pair_usable_depth", "UNMEASURED", "", "print release blocked"),
        ("centre_candidate_receiver_role", "UNVERIFIED", "", "not accepted as a fastener point"),
    ]
    for row_number, row in enumerate(rows, 1):
        for column_number, value in enumerate(row, 1):
            column = chr(ord("A") + column_number - 1)
            sheet.set(f"{column}{row_number}", str(value))
    sheet.setColumnWidth("A", 260)
    sheet.setColumnWidth("B", 150)
    sheet.setColumnWidth("C", 170)
    sheet.setColumnWidth("D", 360)


def main() -> None:
    CAD_DIR.mkdir(parents=True, exist_ok=True)
    measurements = json.loads(MEASUREMENTS_PATH.read_text(encoding="utf-8"))

    document = App.newDocument("CurrentLite3ProMeasuredProxyRevA")

    deck_points = [
        App.Vector(20.0, -45.0, 0.0),
        App.Vector(20.0, 45.0, 0.0),
        App.Vector(5.0, 58.0, 0.0),
        App.Vector(-100.0, 70.0, 0.0),
        App.Vector(-100.0, -70.0, 0.0),
        App.Vector(5.0, -58.0, 0.0),
    ]
    deck_wire = Part.makePolygon(deck_points + [deck_points[0]])
    deck_shape = Part.Face(deck_wire).extrude(App.Vector(0.0, 0.0, -4.0))
    deck = add_feature(
        document,
        "PhotoDeckEnvelope",
        "PHOTO_DECK_SILHOUETTE_PROXY_NOT_OFFICIAL_CAD",
        deck_shape,
        "photo_measured_silhouette_proxy",
        (0.88, 0.88, 0.90),
        18,
    )

    nominal_enclosure = Part.makeBox(
        200.0,
        100.0,
        50.0,
        App.Vector(-300.0, -50.0, 0.0),
    )
    enclosure = add_feature(
        document,
        "ComputeEnclosureNominal",
        "COMPUTE_ENCLOSURE_200x100x50_PHOTO_PROXY",
        nominal_enclosure,
        "photo_measured_external_envelope",
        (0.92, 0.92, 0.94),
        35,
    )

    expanded_keepout = Part.makeBox(
        209.0,
        108.0,
        54.0,
        App.Vector(-305.0, -54.0, 0.0),
    )
    keepout = add_feature(
        document,
        "ComputeEnclosureExpandedKeepout",
        "COMPUTE_ENCLOSURE_EXPANDED_MEASUREMENT_KEEPOUT",
        expanded_keepout,
        "uncertainty_expanded_collision_keepout",
        (0.86, 0.24, 0.20),
        88,
    )

    axis_shape = Part.makeCylinder(3.0, 12.0, App.Vector(0.0, 0.0, -6.0))
    axis_objects = []
    for name, label, x, y in [
        ("FrontLeftAxis", "FRONT_LEFT_AXIS_THREAD_UNMEASURED", 0.0, 32.5),
        ("FrontRightAxis", "FRONT_RIGHT_AXIS_THREAD_UNMEASURED", 0.0, -32.5),
    ]:
        shape = axis_shape.copy()
        shape.translate(App.Vector(x, y, 0.0))
        axis_objects.append(
            add_feature(
                document,
                name,
                label,
                shape,
                "photo_measured_axis_marker",
                (0.10, 0.42, 0.90),
                10,
            )
        )

    centre_shape = axis_shape.copy()
    centre_shape.translate(App.Vector(-75.0, 0.0, 0.0))
    centre = add_feature(
        document,
        "CentreCandidateAxis",
        "CENTRE_CANDIDATE_AXIS_RECEIVER_ROLE_UNVERIFIED",
        centre_shape,
        "photo_measured_candidate_axis_marker",
        (0.96, 0.66, 0.08),
        10,
    )
    axis_objects.append(centre)

    nose_marker = Part.makeBox(0.8, 100.0, 1.0, App.Vector(19.6, -50.0, 0.2))
    nose = add_feature(
        document,
        "NoseEdgeDatum",
        "NOSE_EDGE_DATUM_X_PLUS_20",
        nose_marker,
        "photo_measured_edge_marker",
        (0.12, 0.70, 0.28),
        0,
    )

    add_parameter_sheet(document, measurements)
    for obj in [deck, enclosure, keepout, *axis_objects, nose]:
        add_string(obj, "MeasurementSource", str(MEASUREMENTS_PATH.relative_to(TASK_DIR)))
    document.recompute()
    document.saveAs(str(OUT_FCSTD))

    Import.export([deck, enclosure, *axis_objects, nose], str(OUT_STEP))
    Import.export([keepout], str(OUT_KEEPOUT_STEP))

    round_trip = Part.read(str(OUT_STEP))
    keepout_round_trip = Part.read(str(OUT_KEEPOUT_STEP))
    objects = [deck, enclosure, keepout, *axis_objects, nose]
    report = {
        "schema_version": 1,
        "stage": "experiment_and_analysis",
        "status": "photo_measured_proxy_pass_receiver_contract_open",
        "classification": "collision_and_layout_proxy_not_printable",
        "official_cad": False,
        "source": {
            "measurement_results": str(MEASUREMENTS_PATH.relative_to(TASK_DIR)),
            "measurement_results_sha256": sha256(MEASUREMENTS_PATH),
            "source_index": str(SOURCE_INDEX_PATH.relative_to(TASK_DIR)),
            "source_index_sha256": sha256(SOURCE_INDEX_PATH),
        },
        "objects": {
            obj.Name: {
                "label": obj.Label,
                "evidence_class": obj.EvidenceClass,
                "metrics": shape_metrics(obj.Shape),
            }
            for obj in objects
        },
        "outputs": {
            "fcstd": {"path": str(OUT_FCSTD.relative_to(PACKAGE_DIR)), "bytes": OUT_FCSTD.stat().st_size, "sha256": sha256(OUT_FCSTD)},
            "step": {"path": str(OUT_STEP.relative_to(PACKAGE_DIR)), "bytes": OUT_STEP.stat().st_size, "sha256": sha256(OUT_STEP), "clean_import": shape_metrics(round_trip)},
            "expanded_keepout_step": {"path": str(OUT_KEEPOUT_STEP.relative_to(PACKAGE_DIR)), "bytes": OUT_KEEPOUT_STEP.stat().st_size, "sha256": sha256(OUT_KEEPOUT_STEP), "clean_import": shape_metrics(keepout_round_trip)},
        },
        "checks": {
            "all_proxy_objects_valid": all(obj.Shape.isValid() for obj in objects),
            "front_pair_axis_pitch_mm": (axis_objects[0].Shape.CenterOfMass - axis_objects[1].Shape.CenterOfMass).Length,
            "front_pair_axis_pitch_matches_measurement": abs((axis_objects[0].Shape.CenterOfMass - axis_objects[1].Shape.CenterOfMass).Length - 65.0) < 1.0e-9,
            "nominal_enclosure_bounds_match_measurement": shape_metrics(enclosure.Shape)["bounds_mm"] == {
                "min": [-300.0, -50.0, 0.0],
                "max": [-100.0, 50.0, 50.0],
                "size": [200.0, 100.0, 50.0],
            },
            "expanded_keepout_contains_nominal": expanded_keepout.common(nominal_enclosure).Volume == nominal_enclosure.Volume,
            "printable_adapter_present": False,
            "thread_or_depth_inferred": False,
        },
        "release_gate": {
            "printable_geometry_allowed": False,
            "blocking_inputs": [
                "front-pair thread designation",
                "front-pair usable thread depth",
                "centre candidate mounting role, thread, depth, and load path",
                "remaining cable, connector, vent, foot, and service sweeps",
            ],
        },
        "claim_boundary": "This package validates only the photo-measured proxy and axis scaffold. It is not official CAD, a printable adapter, or physical-fit evidence.",
    }
    report["pass"] = bool(
        report["checks"]["all_proxy_objects_valid"]
        and report["checks"]["front_pair_axis_pitch_matches_measurement"]
        and report["checks"]["nominal_enclosure_bounds_match_measurement"]
        and report["checks"]["expanded_keepout_contains_nominal"]
        and not report["checks"]["printable_adapter_present"]
        and not report["checks"]["thread_or_depth_inferred"]
    )
    VALIDATION_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
