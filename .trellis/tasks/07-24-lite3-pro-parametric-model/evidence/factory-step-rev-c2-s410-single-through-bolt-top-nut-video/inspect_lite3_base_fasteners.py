"""Inspect the retained Lite3 base fasteners in the active Fusion scene."""

import adsk.core
import adsk.fusion
import json


TARGET_NAMES = {
    "BASE_TO_LITE3_FRONT_2X_M3X8_SOCKET_HEAD_SCREWS_REAL_BREP",
    "BASE_TO_LITE3_REAR_2X_OD8_ID3P5_LOCATING_SPACERS_REAL_BREP",
    "BASE_TO_LITE3_REAR_2X_M3X12_SOCKET_HEAD_SCREWS_REAL_BREP",
}


def xyz(value):
    return [value.x, value.y, value.z]


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")

    root = design.rootComponent
    report = {
        "document": application.activeDocument.name,
        "root_occurrence_count": root.occurrences.count,
        "targets": [],
    }
    for occurrence_index in range(root.occurrences.count):
        occurrence = root.occurrences.item(occurrence_index)
        if occurrence.component.name not in TARGET_NAMES:
            continue
        target = {
            "root_index": occurrence_index,
            "name": occurrence.name,
            "component": occurrence.component.name,
            "body_count": occurrence.bRepBodies.count,
            "transform": list(occurrence.transform2.asArray()),
            "bodies": [],
        }
        for body_index in range(occurrence.bRepBodies.count):
            body = occurrence.bRepBodies.item(body_index)
            bounds = body.boundingBox
            body_row = {
                "body_index": body_index,
                "name": body.name,
                "volume_cm3": body.volume,
                "bounds_cm": {
                    "minimum": xyz(bounds.minPoint),
                    "maximum": xyz(bounds.maxPoint),
                    "center": [
                        (bounds.minPoint.x + bounds.maxPoint.x) * 0.5,
                        (bounds.minPoint.y + bounds.maxPoint.y) * 0.5,
                        (bounds.minPoint.z + bounds.maxPoint.z) * 0.5,
                    ],
                    "size": [
                        bounds.maxPoint.x - bounds.minPoint.x,
                        bounds.maxPoint.y - bounds.minPoint.y,
                        bounds.maxPoint.z - bounds.minPoint.z,
                    ],
                },
                "cylinders": [],
            }
            for face_index in range(body.faces.count):
                face = body.faces.item(face_index)
                cylinder = adsk.core.Cylinder.cast(face.geometry)
                if cylinder is None:
                    continue
                body_row["cylinders"].append(
                    {
                        "face_index": face_index,
                        "origin_cm": xyz(cylinder.origin),
                        "axis": xyz(cylinder.axis),
                        "radius_cm": cylinder.radius,
                        "area_cm2": face.area,
                    }
                )
            target["bodies"].append(body_row)
        report["targets"].append(target)

    if len(report["targets"]) != 3:
        raise RuntimeError(
            "Expected three retained Lite3 base-fastener groups, found %d"
            % len(report["targets"])
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))

