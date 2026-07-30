#!/usr/bin/env python3
"""Rebuild the source-backed upper assembly against the scan Rev B body.

The proven J20A/MID-360/S410 transforms remain unchanged.  This wrapper swaps
in the scan-registered conservative keep-out and adds the nominal two-recess
compute enclosure for review.  It still creates no current-Pro lower adapter.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import FreeCAD as App


PACKAGE_DIR = Path(__file__).resolve().parent
TASK_DIR = PACKAGE_DIR.parents[1]
REPO_ROOT = TASK_DIR.parents[2]
REV_A_SCRIPT = (
    TASK_DIR
    / "evidence/current-lite3-pro-source-upper-assembly-rev-a/build_source_upper_assembly.py"
)
INTERFACE_DIR = TASK_DIR / "evidence/current-lite3-pro-scan-registered-interface-rev-b"
INTERFACE_FCSTD = (
    INTERFACE_DIR / "cad/current-lite3-pro-scan-registered-interface-rev-b.FCStd"
)
KEEPOUT_STEP = (
    INTERFACE_DIR
    / "cad/current-lite3-pro-scan-expanded-enclosure-keepout-rev-b.step"
)
CAD_DIR = PACKAGE_DIR / "cad"
OUT_FCSTD = CAD_DIR / "current-lite3-pro-source-upper-assembly-rev-b.FCStd"
OUT_STEP = CAD_DIR / "current-lite3-pro-source-upper-assembly-rev-b.step"
VALIDATION_PATH = PACKAGE_DIR / "validation.json"


def load_rev_a_builder():
    spec = importlib.util.spec_from_file_location("source_upper_rev_a_builder", REV_A_SCRIPT)
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
    required = [REV_A_SCRIPT, INTERFACE_FCSTD, KEEPOUT_STEP]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing inputs: " + ", ".join(missing))

    CAD_DIR.mkdir(parents=True, exist_ok=True)
    builder = load_rev_a_builder()
    builder.PACKAGE_DIR = PACKAGE_DIR
    builder.CAD_DIR = CAD_DIR
    builder.KEEPOUT_STEP = KEEPOUT_STEP
    builder.OUT_FCSTD = OUT_FCSTD
    builder.OUT_STEP = OUT_STEP
    builder.VALIDATION_PATH = VALIDATION_PATH
    builder.main()

    upper_document = App.activeDocument()
    if upper_document is None:
        raise RuntimeError("Rev A source assembly builder did not leave a document open")
    upper_document.Label = "Current Lite3 Pro Source Upper Assembly Rev B"

    keepout = upper_document.getObject("ExpandedComputeKeepout")
    keepout.Label = "SCAN_REGISTERED_EXPANDED_COMPUTE_KEEPOUT_NOT_EXPORT_PART"
    keepout.EvidenceClass = "scan_registered_uncertainty_expanded_keepout"
    if keepout.ViewObject is not None:
        keepout.ViewObject.Transparency = 91

    interface_document = App.openDocument(str(INTERFACE_FCSTD))
    nominal = copy_reference(
        upper_document,
        interface_document.getObject("ComputeEnclosureScanNominal"),
        "ComputeEnclosureScanNominal",
        "COMPUTE_ENCLOSURE_SCAN_REGISTERED_TWO_FRONT_RECESSES",
        "scan_registered_notched_xy_photo_height_envelope",
        (0.82, 0.84, 0.88),
        18,
    )
    deck = copy_reference(
        upper_document,
        interface_document.getObject("DeckPlanarProxy"),
        "DeckPlanarProxy",
        "DECK_PLANAR_PROXY_NOT_OFFICIAL_CAD",
        "photo_scan_planar_silhouette",
        (0.91, 0.92, 0.94),
        55,
    )
    for source_name, color in (
        ("FrontLeftAxis", (0.10, 0.42, 0.90)),
        ("FrontRightAxis", (0.10, 0.42, 0.90)),
        ("CentreCandidateAxis", (0.96, 0.66, 0.08)),
    ):
        source = interface_document.getObject(source_name)
        copy_reference(
            upper_document,
            source,
            source_name,
            source.Label,
            source.EvidenceClass,
            color,
            5,
        )
    copy_reference(
        upper_document,
        interface_document.getObject("UsableNoseEdge"),
        "UsableNoseEdge",
        "USABLE_NOSE_EDGE_X_PLUS_20",
        "photo_scan_corroborated_edge_marker",
        (0.12, 0.70, 0.28),
        0,
    )
    upper_document.recompute()
    upper_document.saveAs(str(OUT_FCSTD))

    report = json.loads(VALIDATION_PATH.read_text(encoding="utf-8"))
    report["status"] = "source_upper_assembly_scan_registered_geometry_pass_lower_interface_open"
    report["classification"] = "source_backed_upper_assembly_scan_review_not_print_release"
    report["sources"]["scan_registered_interface"] = {
        "path": str(INTERFACE_FCSTD.relative_to(REPO_ROOT)),
        "sha256": builder.sha256(INTERFACE_FCSTD),
    }
    report["geometry"]["compute_enclosure_scan_nominal"] = builder.metrics(nominal.Shape)
    report["geometry"]["deck_planar_proxy"] = builder.metrics(deck.Shape)
    report["checks"]["scan_registered_rev_b_keepout_used"] = (
        Path(report["sources"]["current_pro_keepout"]["path"]) == KEEPOUT_STEP.relative_to(REPO_ROOT)
    )
    report["checks"]["nominal_compute_enclosure_has_two_front_recesses"] = (
        len(nominal.Shape.Faces) == 10
        and nominal.Shape.Volume < nominal.Shape.BoundBox.XLength
        * nominal.Shape.BoundBox.YLength
        * nominal.Shape.BoundBox.ZLength
    )
    report["checks"]["notched_nominal_body_is_visual_reference_only"] = True
    report["outputs"]["fcstd"] = {
        "path": str(OUT_FCSTD.relative_to(PACKAGE_DIR)),
        "bytes": OUT_FCSTD.stat().st_size,
        "sha256": builder.sha256(OUT_FCSTD),
    }
    report["claim_boundary"] = (
        "This validates the unchanged source-backed J20A/MID-360/S410 transforms "
        "against the scan Rev B conservative keep-out and shows the nominal "
        "two-recess compute enclosure. It does not establish a lower adapter, "
        "receiver thread/depth, screw length, strength, or printable release."
    )
    report["pass"] = all(report["checks"].values())
    VALIDATION_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    App.closeDocument(interface_document.Name)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
