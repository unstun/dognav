"""Open only the standalone D435i cloud design, export STEP, and close it.

This script is intentionally conservative for Fusion stability.  It does not
open the robot assembly, change the source document, save it, or leave it open.
Run it from Fusion's Python text-command field while the Home tab is active.
"""

from __future__ import annotations

import hashlib
import json
import traceback
from pathlib import Path

import adsk.core
import adsk.fusion


PACKAGE_DIR = Path(
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "current-lite3-pro-d435i-official-brep-export-rev-a"
)
SOURCE_SLDPRT = Path(
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/references/upstream/"
    "2026-07-25_realsense-d435i-cad/source/original/D435i_Solid.SLDPRT"
)
CAD_DIR = PACKAGE_DIR / "cad"
OUTPUT_STEP = CAD_DIR / "d435i-official-manufacturer-brep-from-standalone-cloud.step"
REPORT_PATH = PACKAGE_DIR / "fusion_export_report.json"
FAILURE_PATH = PACKAGE_DIR / "fusion_export_failure.json"

PROJECT_NAME = "Default Project"
FOLDER_NAME = "Lite3 CAD source imports"
DATA_FILE_NAME = "D435i_Solid"
DATA_FILE_EXTENSION = "f3d"
DATA_FILE_LINEAGE_ID = "urn:adsk.wipprod:dm.lineage:elFpDAAPTv-vsPMhVZt0dw"
EXPECTED_SLDPRT_SHA256 = "9cdbfdc7085ea5430ec9007eb1d895c7ff513c40b77c298a275ded33edf65525"
EXPECTED_SORTED_DIMS_CM = [2.499996, 2.505, 8.99045]
DIM_TOLERANCE_CM = 0.05


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collection_items(collection):
    return [collection.item(index) for index in range(collection.count)]


def find_named(items, name: str):
    return [item for item in items if item.name == name]


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


def combined_bounds_cm(bodies: list[adsk.fusion.BRepBody]) -> dict[str, list[float]]:
    boxes = [body.boundingBox for body in bodies]
    mins = [
        min(getattr(box.minPoint, axis) for box in boxes)
        for axis in ("x", "y", "z")
    ]
    maxs = [
        max(getattr(box.maxPoint, axis) for box in boxes)
        for axis in ("x", "y", "z")
    ]
    return {"min": mins, "max": maxs}


def locate_data_file(app: adsk.core.Application):
    projects = collection_items(app.data.dataProjects)
    project_matches = find_named(projects, PROJECT_NAME)
    if len(project_matches) != 1:
        raise RuntimeError(
            f"Expected one project {PROJECT_NAME!r}; found {[project.name for project in projects]}"
        )
    project = project_matches[0]

    folders = collection_items(project.rootFolder.dataFolders)
    folder_matches = find_named(folders, FOLDER_NAME)
    if len(folder_matches) != 1:
        raise RuntimeError(
            f"Expected one folder {FOLDER_NAME!r}; found {[folder.name for folder in folders]}"
        )
    folder = folder_matches[0]

    files = collection_items(folder.dataFiles)
    file_matches = [
        item
        for item in files
        if item.name == DATA_FILE_NAME and item.fileExtension.lower() == DATA_FILE_EXTENSION
    ]
    if len(file_matches) != 1:
        raise RuntimeError(
            "Expected one standalone D435i data file; found "
            + repr([(item.name, item.fileExtension, item.id) for item in files])
        )
    data_file = file_matches[0]
    if data_file.id != DATA_FILE_LINEAGE_ID:
        raise RuntimeError(
            f"Unexpected D435i lineage id {data_file.id!r}; expected {DATA_FILE_LINEAGE_ID!r}"
        )
    return project, folder, data_file


def component_record(component: adsk.fusion.Component) -> dict[str, object]:
    bodies = collection_items(component.bRepBodies)
    meshes = collection_items(component.meshBodies)
    return {
        "name": component.name,
        "brep_body_count": len(bodies),
        "solid_body_count": sum(1 for body in bodies if body.isSolid),
        "mesh_body_count": len(meshes),
    }


def main() -> None:
    app = adsk.core.Application.get()
    opened_document = None
    try:
        project, folder, data_file = locate_data_file(app)
        print("D435I_EXPORT: opening standalone cloud design only")
        opened_document = app.documents.open(data_file)
        if opened_document is None:
            raise RuntimeError("Fusion returned no document for the standalone D435i data file")
        adsk.doEvents()

        design = adsk.fusion.Design.cast(app.activeProduct)
        if design is None:
            raise RuntimeError("The opened standalone data file is not a Fusion design")

        components = collection_items(design.allComponents)
        component_records = [component_record(component) for component in components]
        total_mesh_count = sum(record["mesh_body_count"] for record in component_records)
        candidates = []
        for component in components:
            bodies = collection_items(component.bRepBodies)
            if len(bodies) == 2 and all(body.isSolid for body in bodies):
                candidates.append((component, bodies))
        if len(candidates) != 1:
            raise RuntimeError(
                "Expected exactly one two-solid B-rep component; component topology: "
                + repr(component_records)
            )
        target, bodies = candidates[0]
        bounds = combined_bounds_cm(bodies)
        dims_cm = [
            bounds["max"][index] - bounds["min"][index]
            for index in range(3)
        ]
        sorted_dims_cm = sorted(dims_cm)
        dims_match = all(
            abs(actual - expected) <= DIM_TOLERANCE_CM
            for actual, expected in zip(sorted_dims_cm, EXPECTED_SORTED_DIMS_CM)
        )
        if not dims_match:
            raise RuntimeError(
                f"Unexpected standalone D435i envelope {sorted_dims_cm!r} cm; "
                f"expected {EXPECTED_SORTED_DIMS_CM!r} cm"
            )
        if total_mesh_count != 0:
            raise RuntimeError(f"Expected zero mesh bodies; found {total_mesh_count}")

        CAD_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_STEP.unlink(missing_ok=True)
        REPORT_PATH.unlink(missing_ok=True)
        FAILURE_PATH.unlink(missing_ok=True)
        options = design.exportManager.createSTEPExportOptions(str(OUTPUT_STEP), target)
        if options is None or not design.exportManager.execute(options):
            raise RuntimeError("Fusion STEP export failed")
        if not OUTPUT_STEP.is_file() or OUTPUT_STEP.stat().st_size == 0:
            raise RuntimeError("Fusion reported success but wrote no STEP file")

        source_hash = sha256(SOURCE_SLDPRT)
        report = {
            "schema_version": 2,
            "stage": "experiment_and_analysis",
            "status": "official_manufacturer_d435i_brep_exported_from_standalone_cloud_translation",
            "fusion_stability_strategy": {
                "opened_only": "standalone D435i_Solid cloud data file",
                "robot_assembly_opened": False,
                "source_document_edited": False,
                "source_document_saved": False,
                "close_without_save": True,
            },
            "cloud_source": {
                "project": project.name,
                "folder": folder.name,
                "name": data_file.name,
                "file_extension": data_file.fileExtension,
                "lineage_id": data_file.id,
                "version_id": data_file.versionId,
                "version_number": data_file.versionNumber,
            },
            "manufacturer_source": {
                "path": str(SOURCE_SLDPRT),
                "bytes": SOURCE_SLDPRT.stat().st_size,
                "sha256": source_hash,
                "identity_note": "The standalone cloud file is the Fusion translation named D435i_Solid retained in the dedicated source-import folder; the original manufacturer SLDPRT is retained locally by hash.",
            },
            "component": {
                "name": target.name,
                "brep_body_count": len(bodies),
                "solid_body_count": sum(1 for body in bodies if body.isSolid),
                "mesh_body_count_all_components": total_mesh_count,
                "bounds_cm": bounds,
                "dims_cm": dims_cm,
                "sorted_dims_cm": sorted_dims_cm,
                "bodies": [body_metrics(body) for body in bodies],
                "all_component_topology": component_records,
            },
            "output": {
                "path": str(OUTPUT_STEP.relative_to(PACKAGE_DIR)),
                "bytes": OUTPUT_STEP.stat().st_size,
                "sha256": sha256(OUTPUT_STEP),
            },
            "checks": {
                "cloud_project_exact": project.name == PROJECT_NAME,
                "cloud_folder_exact": folder.name == FOLDER_NAME,
                "cloud_name_exact": data_file.name == DATA_FILE_NAME,
                "cloud_extension_exact": data_file.fileExtension.lower() == DATA_FILE_EXTENSION,
                "cloud_lineage_exact": data_file.id == DATA_FILE_LINEAGE_ID,
                "manufacturer_sldprt_hash_exact": source_hash == EXPECTED_SLDPRT_SHA256,
                "one_two_solid_brep_component": len(candidates) == 1,
                "zero_mesh_bodies": total_mesh_count == 0,
                "manufacturer_envelope_match": dims_match,
                "step_written": OUTPUT_STEP.is_file() and OUTPUT_STEP.stat().st_size > 0,
            },
            "claim_boundary": "This proves a standalone STEP export of the retained manufacturer-derived D435i B-rep. It does not validate the current-Pro camera pose, support, robot interface, screw length, human tool access, or print release.",
        }
        report["pass"] = all(report["checks"].values())
        REPORT_PATH.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print("D435I_EXPORT_RESULT=" + json.dumps({"pass": report["pass"], "output": report["output"]}, ensure_ascii=False))
        if not report["pass"]:
            raise RuntimeError("Fusion export checks failed")
    except Exception as exc:
        failure = {
            "schema_version": 1,
            "status": "fusion_export_failed",
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "claim_boundary": "No D435i STEP export claim is made from this failed run.",
        }
        FAILURE_PATH.write_text(
            json.dumps(failure, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print("D435I_EXPORT_ERROR=" + str(exc))
        raise
    finally:
        if opened_document is not None and opened_document.isValid:
            print("D435I_EXPORT: closing standalone design without saving")
            opened_document.close(False)


main()
