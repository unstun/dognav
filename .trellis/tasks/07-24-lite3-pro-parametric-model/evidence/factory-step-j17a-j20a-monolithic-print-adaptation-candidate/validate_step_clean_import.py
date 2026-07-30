"""Validate the exported monolithic bracket STEP in a clean FreeCAD import."""

import json
import os

import FreeCAD as App
import Import


EVIDENCE_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-j17a-j20a-monolithic-print-adaptation-candidate"
)
STEP_PATH = os.path.join(
    EVIDENCE_DIR, "j17a-j20a-monolithic-print-adaptation-rev-a.step"
)
REPORT_PATH = os.path.join(EVIDENCE_DIR, "freecad_clean_import_validation.json")


document = App.newDocument("MonolithicStepValidation")
Import.insert(STEP_PATH, document.Name)
document.recompute()

shape_objects = [
    item
    for item in document.Objects
    if hasattr(item, "Shape") and not item.Shape.isNull()
]
solid_count = sum(len(item.Shape.Solids) for item in shape_objects)
shell_count = sum(len(item.Shape.Shells) for item in shape_objects)
face_count = sum(len(item.Shape.Faces) for item in shape_objects)
volume_mm3 = sum(item.Shape.Volume for item in shape_objects)
valid = all(item.Shape.isValid() for item in shape_objects)
closed = all(item.Shape.isClosed() for item in shape_objects)

report = {
    "stage": "experiment_and_analysis",
    "source_step": STEP_PATH,
    "importer": "FreeCAD clean process",
    "shape_object_count": len(shape_objects),
    "shape_types": [item.Shape.ShapeType for item in shape_objects],
    "solid_count": solid_count,
    "shell_count": shell_count,
    "face_count": face_count,
    "volume_mm3": volume_mm3,
    "all_shapes_valid": valid,
    "all_shapes_closed": closed,
    "pass": bool(
        len(shape_objects) == 1
        and solid_count == 1
        and valid
        and closed
        and volume_mm3 > 0.0
    ),
}

with open(REPORT_PATH, "w", encoding="utf-8") as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2)
    stream.write("\n")

print(json.dumps(report, ensure_ascii=False, indent=2))
App.closeDocument(document.Name)

if not report["pass"]:
    raise RuntimeError("Clean STEP import did not resolve to one valid closed solid")
