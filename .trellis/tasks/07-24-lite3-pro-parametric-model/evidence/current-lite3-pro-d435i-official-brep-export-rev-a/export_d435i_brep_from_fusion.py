"""Export the verified official-manufacturer D435i B-rep from a small F3D archive.

Run inside Fusion's Python text-command context after opening the archived F3D.
The script is deliberately export-only: it does not edit or save the document.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import adsk.core
import adsk.fusion


PACKAGE_DIR = Path(
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "current-lite3-pro-d435i-official-brep-export-rev-a"
)
SOURCE_F3D = Path(
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "official-d435i-brep-on-accepted-j17a/"
    "lite3-venture-j17a-j20a-mid360-d435i-brep.f3d"
)
SOURCE_SLDPRT = Path(
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/references/upstream/"
    "2026-07-25_realsense-d435i-cad/source/original/D435i_Solid.SLDPRT"
)
CAD_DIR = PACKAGE_DIR / "cad"
OUTPUT_STEP = CAD_DIR / "d435i-official-manufacturer-brep-from-verified-f3d.step"
REPORT_PATH = PACKAGE_DIR / "fusion_export_report.json"
TARGET_COMPONENT_NAME = "D435I_REAL_BREP_OFFICIAL_MANUFACTURER_CAD"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def body_metrics(body: adsk.fusion.BRepBody) -> dict[str, object]:
    box = body.boundingBox
    return {
        "name": body.name,
        "is_solid": bool(body.isSolid),
        "faces": body.faces.count,
        "volume_cm3": body.volume if body.isSolid else 0.0,
        "bounds_cm": {
            "min": [box.minPoint.x, box.minPoint.y, box.minPoint.z],
            "max": [box.maxPoint.x, box.maxPoint.y, box.maxPoint.z],
        },
    }


def main() -> None:
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")

    components = [design.allComponents.item(index) for index in range(design.allComponents.count)]
    exact = [component for component in components if component.name == TARGET_COMPONENT_NAME]
    if len(exact) != 1:
        candidates = [component.name for component in components if "D435" in component.name.upper()]
        raise RuntimeError(
            f"Expected one {TARGET_COMPONENT_NAME!r}; found {len(exact)}. "
            f"D435 candidates: {candidates}"
        )
    target = exact[0]
    bodies = [target.bRepBodies.item(index) for index in range(target.bRepBodies.count)]
    solid_count = sum(1 for body in bodies if body.isSolid)
    mesh_count = target.meshBodies.count
    if len(bodies) != 2 or solid_count != 2 or mesh_count != 0:
        raise RuntimeError(
            f"Unexpected target topology: brep={len(bodies)}, solid={solid_count}, mesh={mesh_count}"
        )

    CAD_DIR.mkdir(parents=True, exist_ok=True)
    if OUTPUT_STEP.exists():
        OUTPUT_STEP.unlink()
    options = design.exportManager.createSTEPExportOptions(str(OUTPUT_STEP), target)
    if options is None or not design.exportManager.execute(options):
        raise RuntimeError("Fusion STEP export failed")
    if not OUTPUT_STEP.is_file() or OUTPUT_STEP.stat().st_size == 0:
        raise RuntimeError("Fusion reported success but no STEP was written")

    report = {
        "schema_version": 1,
        "stage": "experiment_and_analysis",
        "status": "official_manufacturer_d435i_brep_exported_from_verified_f3d",
        "active_document": app.activeDocument.name,
        "source": {
            "fusion_archive": {
                "path": str(SOURCE_F3D),
                "bytes": SOURCE_F3D.stat().st_size,
                "sha256": sha256(SOURCE_F3D),
            },
            "manufacturer_sldprt": {
                "path": str(SOURCE_SLDPRT),
                "bytes": SOURCE_SLDPRT.stat().st_size,
                "sha256": sha256(SOURCE_SLDPRT),
            },
            "conversion": "Fusion cloud translation of the official manufacturer D435i_Solid.SLDPRT, preserved inside the verified F3D archive",
        },
        "component": {
            "name": target.name,
            "brep_body_count": len(bodies),
            "solid_body_count": solid_count,
            "mesh_body_count": mesh_count,
            "bodies": [body_metrics(body) for body in bodies],
        },
        "output": {
            "path": str(OUTPUT_STEP.relative_to(PACKAGE_DIR)),
            "bytes": OUTPUT_STEP.stat().st_size,
            "sha256": sha256(OUTPUT_STEP),
        },
        "checks": {
            "source_f3d_matches_archived_hash": sha256(SOURCE_F3D)
            == "71efccf66aa8d5dd676c32d1d711251847ae013849dfa96596097c12b15b7908",
            "manufacturer_sldprt_matches_archived_hash": sha256(SOURCE_SLDPRT)
            == "9cdbfdc7085ea5430ec9007eb1d895c7ff513c40b77c298a275ded33edf65525",
            "target_name_exact": target.name == TARGET_COMPONENT_NAME,
            "two_solid_brep_bodies": len(bodies) == 2 and solid_count == 2,
            "zero_mesh_bodies": mesh_count == 0,
            "step_written": OUTPUT_STEP.is_file() and OUTPUT_STEP.stat().st_size > 0,
        },
        "claim_boundary": "This exports the manufacturer-derived D435i B-rep already verified inside the archived Fusion assembly. It does not validate the current-Pro camera pose, support, robot interface, screw length, or print release.",
    }
    report["pass"] = all(report["checks"].values())
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "output": report["output"]}, ensure_ascii=False))
    if not report["pass"]:
        raise RuntimeError("Export report checks failed")


main()
