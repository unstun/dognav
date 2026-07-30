#!/usr/bin/env python3
"""Inventory the user-provided Lite3 STEP without modifying the source.

Run this script with FreeCAD's console runtime.  The resulting JSON preserves
the imported assembly labels, parent links, shape complexity, volume, and
bounding boxes so that a later lightweight B-rep export can remove internal
and repetitive detail by evidence rather than by guessing from a screenshot.
"""

from __future__ import annotations

import json
from pathlib import Path

import FreeCAD as App
import Import


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[2]
SOURCE_PATH = (
    REPO_ROOT
    / "references/upstream/2026-07-27_lite3-exploration-assembly-cad"
    / "source/original/lite3-exploration-assembly.step"
)
OUTPUT_PATH = (
    TASK_ROOT
    / "evidence/factory-step-lite3-lightweight-brep"
    / "object_inventory.json"
)


def rounded(value: float) -> float:
    return round(float(value), 6)


def main() -> None:
    if not SOURCE_PATH.is_file():
        raise FileNotFoundError(SOURCE_PATH)

    document = App.newDocument("Lite3_Factory_STEP_Inventory")
    Import.insert(str(SOURCE_PATH), document.Name)
    document.recompute()

    records: list[dict[str, object]] = []
    for obj in document.Objects:
        record: dict[str, object] = {
            "name": obj.Name,
            "label": obj.Label,
            "type_id": obj.TypeId,
            "parents": [
                {"name": parent.Name, "label": parent.Label}
                for parent in obj.InList
            ],
        }
        if hasattr(obj, "Group"):
            record["children"] = [
                {"name": child.Name, "label": child.Label}
                for child in obj.Group
            ]
        if hasattr(obj, "Shape") and not obj.Shape.isNull():
            shape = obj.Shape
            box = shape.BoundBox
            record["shape"] = {
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
        records.append(record)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "source_path": str(SOURCE_PATH),
        "document_object_count": len(document.Objects),
        "records": records,
    }
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT_PATH)
    print(f"objects={len(document.Objects)}")


if __name__ == "__main__":
    main()
