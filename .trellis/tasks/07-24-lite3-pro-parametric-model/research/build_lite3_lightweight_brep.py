#!/usr/bin/env python3
"""Flatten the real Lite3 full robot into a lightweight B-rep deliverable.

The source STEP is imported unchanged.  Only the robot-base root component is
copied with all four leg branches; the separate exploration backload branch
and duplicated assembly-tree representations are excluded.  The output remains
analytic B-rep geometry and is never tessellated into a mesh.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Import
import Part


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[2]
SOURCE_PATH = (
    REPO_ROOT
    / "references/upstream/2026-07-27_lite3-exploration-assembly-cad"
    / "source/original/lite3-exploration-assembly.step"
)
OUTPUT_ROOT = (
    TASK_ROOT
    / "evidence/factory-step-lite3-lightweight-brep"
)
FCSTD_PATH = OUTPUT_ROOT / "lite3-real-brep-lightweight.FCStd"
STEP_PATH = OUTPUT_ROOT / "lite3-real-brep-lightweight.step"
REPORT_PATH = OUTPUT_ROOT / "validation_report.json"


def descendants(root: App.DocumentObject) -> list[App.DocumentObject]:
    result: list[App.DocumentObject] = []
    pending = list(getattr(root, "Group", []))
    while pending:
        obj = pending.pop()
        children = list(getattr(obj, "Group", []))
        if children:
            pending.extend(children)
        else:
            result.append(obj)
    return result


def find_visible_robot_root(
    document: App.Document,
) -> App.DocumentObject:
    top_level_parts = [
        obj
        for obj in document.Objects
        if obj.TypeId == "App::Part" and not obj.InList
    ]
    if len(top_level_parts) != 1:
        raise RuntimeError(
            f"Expected one top-level assembly, found {len(top_level_parts)}"
        )
    candidates = [
        child
        for child in top_level_parts[0].Group
        if child.TypeId == "App::Part"
        and hasattr(child, "Shape")
        and len(child.Shape.Solids) > 200
        and len(getattr(child, "Group", [])) == 5
    ]
    if len(candidates) != 1:
        raise RuntimeError(
            f"Expected one visible full-robot branch, found {len(candidates)}"
        )
    return candidates[0]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rounded(value: float) -> float:
    return round(float(value), 6)


def shape_metrics(shape: Part.Shape) -> dict[str, object]:
    box = shape.BoundBox
    return {
        "solid_count": len(shape.Solids),
        "shell_count": len(shape.Shells),
        "face_count": len(shape.Faces),
        "edge_count": len(shape.Edges),
        "volume_mm3": rounded(shape.Volume),
        "bbox_min_mm": [
            rounded(box.XMin),
            rounded(box.YMin),
            rounded(box.ZMin),
        ],
        "bbox_max_mm": [
            rounded(box.XMax),
            rounded(box.YMax),
            rounded(box.ZMax),
        ],
        "bbox_size_mm": [
            rounded(box.XLength),
            rounded(box.YLength),
            rounded(box.ZLength),
        ],
        "is_valid": bool(shape.isValid()),
    }


def main() -> None:
    if not SOURCE_PATH.is_file():
        raise FileNotFoundError(SOURCE_PATH)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    source_document = App.newDocument("Lite3_Source_Assembly")
    Import.insert(str(SOURCE_PATH), source_document.Name)
    source_document.recompute()

    source_root = find_visible_robot_root(source_document)
    source_metrics = shape_metrics(source_root.Shape)
    leaves = [
        obj
        for obj in descendants(source_root)
        if hasattr(obj, "Shape") and not obj.Shape.isNull()
    ]
    global_shapes: list[Part.Shape] = []
    leaf_records: list[dict[str, object]] = []
    for obj in leaves:
        shape = Part.getShape(
            obj,
            "",
            needSubElement=False,
            refine=False,
        )
        if shape.isNull():
            raise RuntimeError(f"Resolved empty leaf shape: {obj.Name}")
        global_shapes.append(shape)
        leaf_records.append(
            {
                "name": obj.Name,
                "label": obj.Label,
                "metrics": shape_metrics(shape),
            }
        )

    lightweight_shape = Part.makeCompound(global_shapes)
    lightweight_metrics = shape_metrics(lightweight_shape)
    if len(leaves) < 250:
        raise RuntimeError(
            f"Expected the torso and four leg branches, found {len(leaves)} leaves"
        )
    if max(lightweight_metrics["bbox_size_mm"]) > 1000.0:
        raise RuntimeError(
            "Resolved full-robot bounding box is implausibly large: "
            f"{lightweight_metrics['bbox_size_mm']}"
        )
    if min(lightweight_metrics["bbox_size_mm"]) < 150.0:
        raise RuntimeError(
            "Resolved full-robot bounding box is implausibly small: "
            f"{lightweight_metrics['bbox_size_mm']}"
        )

    output_document = App.newDocument("Lite3_Real_BRep_Lightweight")
    robot = output_document.addObject(
        "Part::Feature",
        "LITE3_REAL_BREP_LIGHTWEIGHT",
    )
    robot.Label = "Lite3 real B-rep lightweight robot"
    robot.Shape = lightweight_shape
    robot.addProperty("App::PropertyString", "GeometryClass", "Evidence")
    robot.GeometryClass = "source_brep_flattened_not_mesh"
    robot.addProperty("App::PropertyString", "SourceRoot", "Evidence")
    robot.SourceRoot = source_root.Name
    robot.addProperty("App::PropertyString", "ExcludedBranch", "Evidence")
    robot.ExcludedBranch = "separate exploration backload module"
    robot.addProperty("App::PropertyString", "SourceSHA256", "Evidence")
    robot.SourceSHA256 = sha256(SOURCE_PATH)
    output_document.recompute()
    output_document.saveAs(str(FCSTD_PATH))
    Part.export([robot], str(STEP_PATH))

    if not FCSTD_PATH.is_file() or FCSTD_PATH.stat().st_size == 0:
        raise RuntimeError(f"FreeCAD did not write {FCSTD_PATH}")
    if not STEP_PATH.is_file() or STEP_PATH.stat().st_size == 0:
        raise RuntimeError(f"FreeCAD did not write {STEP_PATH}")

    validation_document = App.newDocument("Lite3_Lightweight_Validation")
    validation_shape = Part.read(str(STEP_PATH))
    validation_metrics = shape_metrics(validation_shape)
    if validation_metrics["solid_count"] != lightweight_metrics["solid_count"]:
        raise RuntimeError("STEP round trip changed solid count")
    if validation_metrics["face_count"] != lightweight_metrics["face_count"]:
        raise RuntimeError("STEP round trip changed face count")

    step_text = STEP_PATH.read_text(
        encoding="latin-1",
        errors="ignore",
    )
    triangulated_face_set_count = step_text.count("TRIANGULATED_FACE_SET")
    if triangulated_face_set_count:
        raise RuntimeError("Lightweight STEP unexpectedly contains mesh faces")

    report = {
        "schema_version": 1,
        "status": "validated",
        "purpose": "lite3_real_brep_lightweight_fusion_foundation",
        "source": {
            "path": str(SOURCE_PATH),
            "size_bytes": SOURCE_PATH.stat().st_size,
            "sha256": sha256(SOURCE_PATH),
            "robot_root_name": source_root.Name,
            "robot_root_label": source_root.Label,
            "robot_root_metrics": source_metrics,
        },
        "operation": {
            "geometry_changed": False,
            "mesh_conversion": False,
            "assembly_tree_flattened": True,
            "global_assembly_placements_applied": True,
            "full_robot_leaf_count": len(leaves),
            "separate_exploration_backload_excluded": True,
            "duplicate_parent_representations_excluded": True,
            "leaf_records": leaf_records,
        },
        "outputs": {
            "fcstd": {
                "path": str(FCSTD_PATH),
                "size_bytes": FCSTD_PATH.stat().st_size,
                "sha256": sha256(FCSTD_PATH),
            },
            "step": {
                "path": str(STEP_PATH),
                "size_bytes": STEP_PATH.stat().st_size,
                "sha256": sha256(STEP_PATH),
                "triangulated_face_set_count": triangulated_face_set_count,
                "round_trip_metrics": validation_metrics,
            },
        },
        "claim_boundary": (
            "The output is a flattened copy of the real source full-robot "
            "B-rep with torso and four leg branches. It excludes the separate "
            "backload branch and duplicated assembly hierarchy, but does not "
            "prove physical sensor fit, robot variant identity, or a mounting "
            "interface."
        ),
    }
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(REPORT_PATH)
    print(json.dumps(validation_metrics, ensure_ascii=False))


if __name__ == "__main__":
    main()
