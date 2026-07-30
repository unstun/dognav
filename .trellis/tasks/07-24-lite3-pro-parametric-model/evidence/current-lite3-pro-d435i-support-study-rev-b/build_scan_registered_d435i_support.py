#!/usr/bin/env python3
"""Rebuild the D435i support study against the scan Rev B upper assembly."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import FreeCAD as App
import Import
import Part


PACKAGE_DIR = Path(__file__).resolve().parent
TASK_DIR = PACKAGE_DIR.parents[1]
REPO_ROOT = TASK_DIR.parents[2]
REV_A_DIR = TASK_DIR / "evidence/current-lite3-pro-d435i-support-study-rev-a"
REV_A_SCRIPT = REV_A_DIR / "build_d435i_support_candidate.py"
UPPER_DIR = TASK_DIR / "evidence/current-lite3-pro-source-upper-assembly-rev-b"
UPPER_FCSTD = UPPER_DIR / "cad/current-lite3-pro-source-upper-assembly-rev-b.FCStd"
UPPER_VALIDATION = UPPER_DIR / "validation.json"
CAD_DIR = PACKAGE_DIR / "cad"
OUT_FCSTD = CAD_DIR / "current-lite3-pro-d435i-support-study-rev-b.FCStd"
OUT_SUPPORT_STEP = CAD_DIR / "current-lite3-pro-d435i-support-candidate-rev-b.step"
OUT_REVIEW_STEP = CAD_DIR / "current-lite3-pro-combined-sensor-review-rev-b.step"
VALIDATION_PATH = PACKAGE_DIR / "validation.json"


def load_rev_a_builder():
    spec = importlib.util.spec_from_file_location("d435i_support_rev_a_builder", REV_A_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {REV_A_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_reference(document, source, name, label, evidence_class, color, transparency):
    obj = document.addObject("PartDesign::Feature", name)
    obj.Label = label
    obj.Shape = source.Shape.copy()
    obj.addProperty("App::PropertyString", "EvidenceClass", "Evidence")
    obj.EvidenceClass = evidence_class
    obj.addProperty("App::PropertyString", "ManufacturingUse", "Evidence")
    obj.ManufacturingUse = "false"
    obj.addProperty("App::PropertyString", "ClaimBoundary", "Evidence")
    obj.ClaimBoundary = (
        "Scan/photo review reference only; receiver thread, usable depth, "
        "seating Z, and structural load path remain open"
    )
    if obj.ViewObject is not None:
        obj.ViewObject.ShapeColor = color
        obj.ViewObject.LineColor = color
        obj.ViewObject.Transparency = transparency
    return obj


def main() -> None:
    required = [REV_A_SCRIPT, UPPER_FCSTD, UPPER_VALIDATION]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing inputs: " + ", ".join(missing))

    CAD_DIR.mkdir(parents=True, exist_ok=True)
    builder = load_rev_a_builder()
    builder.PACKAGE_DIR = PACKAGE_DIR
    builder.PARAMETERS_PATH = REV_A_DIR / "parameters.json"
    builder.SELECTION_PATH = REV_A_DIR / "placement_selection.json"
    builder.UPPER_DIR = UPPER_DIR
    builder.UPPER_FCSTD = UPPER_FCSTD
    builder.UPPER_VALIDATION = UPPER_VALIDATION
    builder.CAD_DIR = CAD_DIR
    builder.OUT_FCSTD = OUT_FCSTD
    builder.OUT_SUPPORT_STEP = OUT_SUPPORT_STEP
    builder.OUT_REVIEW_STEP = OUT_REVIEW_STEP
    builder.VALIDATION_PATH = VALIDATION_PATH
    builder.main()

    support_document = App.activeDocument()
    if support_document is None:
        raise RuntimeError("Rev A support builder did not leave a document open")
    support_document.Label = "Current Lite3 Pro D435i Support Study Rev B"
    upper_document = App.openDocument(str(UPPER_FCSTD))
    nominal = copy_reference(
        support_document,
        upper_document.getObject("ComputeEnclosureScanNominal"),
        "ComputeEnclosureScanNominal",
        "COMPUTE_ENCLOSURE_SCAN_REGISTERED_TWO_FRONT_RECESSES",
        "scan_registered_notched_xy_photo_height_envelope",
        (0.82, 0.84, 0.88),
        25,
    )
    deck = copy_reference(
        support_document,
        upper_document.getObject("DeckPlanarProxy"),
        "DeckPlanarProxy",
        "DECK_PLANAR_PROXY_NOT_OFFICIAL_CAD",
        "photo_scan_planar_silhouette",
        (0.91, 0.92, 0.94),
        62,
    )
    support_document.recompute()
    support_document.saveAs(str(OUT_FCSTD))
    Import.export(
        [
            support_document.getObject("D435iSupportCandidate"),
            support_document.getObject("D435iOfficialEnvelope"),
            support_document.getObject("J20aReview"),
            support_document.getObject("S410Review"),
            support_document.getObject("Mid360Review"),
            nominal,
        ],
        str(OUT_REVIEW_STEP),
    )
    review_round_trip = Part.read(str(OUT_REVIEW_STEP))

    report = json.loads(VALIDATION_PATH.read_text(encoding="utf-8"))
    report["status"] = "d435i_support_scan_registered_geometry_pass_lower_union_open"
    report["classification"] = "scan_registered_print_adaptation_candidate_not_print_release"
    report["sources"]["upper_validation"] = {
        "path": str(UPPER_VALIDATION.relative_to(REPO_ROOT)),
        "sha256": builder.sha256(UPPER_VALIDATION),
    }
    report["geometry"]["compute_enclosure_scan_nominal"] = builder.metrics(nominal.Shape)
    report["geometry"]["deck_planar_proxy"] = builder.metrics(deck.Shape)
    report["geometry"]["review_step_clean_import"] = builder.metrics(review_round_trip)
    upper_validation = json.loads(UPPER_VALIDATION.read_text(encoding="utf-8"))
    report["checks"]["scan_registered_rev_b_upper_used"] = bool(
        upper_validation.get("pass")
        and upper_validation["checks"].get("scan_registered_rev_b_keepout_used")
        and Path(report["sources"]["upper_fcstd"]["path"]) == UPPER_FCSTD.relative_to(REPO_ROOT)
    )
    report["checks"]["nominal_two_recess_body_is_visual_reference_only"] = True
    report["checks"]["full_review_step_clean_import_valid"] = review_round_trip.isValid()
    report["outputs"]["fcstd"] = {
        "path": str(OUT_FCSTD.relative_to(PACKAGE_DIR)),
        "bytes": OUT_FCSTD.stat().st_size,
        "sha256": builder.sha256(OUT_FCSTD),
    }
    report["outputs"]["review_step"] = {
        "path": str(OUT_REVIEW_STEP.relative_to(PACKAGE_DIR)),
        "bytes": OUT_REVIEW_STEP.stat().st_size,
        "sha256": builder.sha256(OUT_REVIEW_STEP),
    }
    report["claim_boundary"] = (
        "This validates a one-solid D435i support candidate and its official "
        "45 mm rear M3 axes against the scan Rev B keep-out and source-backed "
        "upper stack. The D435i object remains a collision envelope in this "
        "headless study; the official visual B-rep is retained in the Fusion "
        "review assembly. No lower receiver, screw length, strength, or print "
        "release is established."
    )
    report["pass"] = all(report["checks"].values())
    VALIDATION_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    App.closeDocument(upper_document.Name)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
