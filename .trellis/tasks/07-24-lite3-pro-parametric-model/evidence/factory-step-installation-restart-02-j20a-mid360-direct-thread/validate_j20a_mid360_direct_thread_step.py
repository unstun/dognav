"""Validate the isolated J20A + MID360 restart-step subassembly in Fusion."""

import adsk.core
import adsk.fusion
import json
import math


MOUNT_NORMAL = (0.0, 0.9659258262890683, 0.25881904510252074)
PLATE_UP = (0.0, -0.25881904510252074, 0.9659258262890683)
J20A_INDEX = 2
MID360_INDEX = 4
SCREW_INDICES = (11, 12, 13, 14)


def matrix_from_values(values):
    matrix = adsk.core.Matrix3D.create()
    if not matrix.setWithArray(values):
        raise RuntimeError("Could not set occurrence transform")
    return matrix


def component_bodies(component):
    bodies = []
    seen = set()

    def walk(current):
        for index in range(current.bRepBodies.count):
            body = current.bRepBodies.item(index)
            if body.entityToken not in seen:
                seen.add(body.entityToken)
                bodies.append(body)
        for index in range(current.occurrences.count):
            walk(current.occurrences.item(index).component)

    walk(component)
    return bodies


def component_mesh_count(component):
    total = component.meshBodies.count
    for index in range(component.occurrences.count):
        total += component_mesh_count(component.occurrences.item(index).component)
    return total


def cylinders(occurrence, radius_min, radius_max):
    rows = []
    seen = set()
    for body in occurrence.bRepBodies:
        for face in body.faces:
            geometry = face.geometry
            if (
                geometry
                and geometry.objectType == adsk.core.Cylinder.classType()
                and radius_min <= geometry.radius <= radius_max
            ):
                origin = geometry.origin
                axis = [geometry.axis.x, geometry.axis.y, geometry.axis.z]
                if sum(axis[i] * MOUNT_NORMAL[i] for i in range(3)) < 0.0:
                    axis = [-value for value in axis]
                row = {
                    "origin_cm": [origin.x, origin.y, origin.z],
                    "axis": axis,
                    "radius_mm": geometry.radius * 10.0,
                }
                key = tuple(
                    round(value, 6)
                    for value in row["origin_cm"] + row["axis"] + [row["radius_mm"]]
                )
                if key not in seen:
                    seen.add(key)
                    rows.append(row)
    return rows


def line_residual_mm(first, second):
    delta = [second[i] - first[i] for i in range(3)]
    axial = sum(delta[i] * MOUNT_NORMAL[i] for i in range(3))
    perpendicular = [
        delta[i] - axial * MOUNT_NORMAL[i] for i in range(3)
    ]
    return math.sqrt(sum(value * value for value in perpendicular)) * 10.0


def interference(design, first, second):
    entities = adsk.core.ObjectCollection.create()
    entities.add(first)
    entities.add(second)
    results = design.analyzeInterference(design.createInterferenceInput(entities))
    return {
        "result_count": results.count,
        "volume_mm3": sum(
            results.item(index).interferenceBody.volume * 1000.0
            for index in range(results.count)
        ),
    }


def minimum_distance_mm(application, first, second):
    return application.measureManager.measureMinimumDistance(first, second).value * 10.0


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    occurrences = design.rootComponent.occurrences
    if occurrences.count != 34:
        raise RuntimeError("Expected 34 root occurrences")

    j20a = occurrences.item(J20A_INDEX)
    mid360 = occurrences.item(MID360_INDEX)
    screws = {index: occurrences.item(index) for index in SCREW_INDICES}

    j20_cylinders = cylinders(j20a, 0.174, 0.176)
    mid_cylinders = cylinders(mid360, 0.149, 0.151)
    screw_cylinders = {
        index: cylinders(occurrence, 0.149, 0.151)
        for index, occurrence in screws.items()
    }
    if len(j20_cylinders) != 4 or len(mid_cylinders) != 4:
        raise RuntimeError("Expected four J20A and four MID360 mounting cylinders")

    matches = []
    for j20_cylinder in j20_cylinders:
        origin = j20_cylinder["origin_cm"]
        mid_match = min(
            mid_cylinders,
            key=lambda row: line_residual_mm(origin, row["origin_cm"]),
        )
        screw_candidates = []
        for index, rows in screw_cylinders.items():
            for row in rows:
                screw_candidates.append(
                    (line_residual_mm(origin, row["origin_cm"]), index)
                )
        screw_residual, screw_index = min(screw_candidates)
        matches.append(
            {
                "j20_origin_cm": origin,
                "mid_axis_residual_mm": line_residual_mm(
                    origin, mid_match["origin_cm"]
                ),
                "screw_occurrence": screw_index,
                "screw_axis_residual_mm": screw_residual,
            }
        )

    x_values = sorted(
        set(round(row["origin_cm"][0], 6) for row in j20_cylinders)
    )
    tangent_values = sorted(
        set(
            round(
                sum(row["origin_cm"][i] * PLATE_UP[i] for i in range(3)),
                6,
            )
            for row in j20_cylinders
        )
    )

    modeled_measurement = application.measureManager.measureMinimumDistance(
        j20a, mid360
    )
    modeled_clearance_mm = modeled_measurement.value * 10.0
    separation = [
        modeled_measurement.positionTwo.x - modeled_measurement.positionOne.x,
        modeled_measurement.positionTwo.y - modeled_measurement.positionOne.y,
        modeled_measurement.positionTwo.z - modeled_measurement.positionOne.z,
    ]
    projected_clearance_cm = sum(
        separation[i] * MOUNT_NORMAL[i] for i in range(3)
    )
    original_mid360_transform = list(mid360.transform.asArray())
    try:
        forced_transform = list(original_mid360_transform)
        forced_transform[3] -= MOUNT_NORMAL[0] * projected_clearance_cm
        forced_transform[7] -= MOUNT_NORMAL[1] * projected_clearance_cm
        forced_transform[11] -= MOUNT_NORMAL[2] * projected_clearance_cm
        mid360.transform = matrix_from_values(forced_transform)
        forced_contact = {
            "translation_mm": -projected_clearance_cm * 10.0,
            "minimum_distance_mm": minimum_distance_mm(application, j20a, mid360),
            "interference": interference(design, j20a, mid360),
        }
    finally:
        mid360.transform = matrix_from_values(original_mid360_transform)

    report = {
        "document": application.activeDocument.name,
        "root_occurrence_count": occurrences.count,
        "components": {
            "j20a": {
                "index": J20A_INDEX,
                "name": j20a.name,
                "brep_body_count": len(component_bodies(j20a.component)),
                "mesh_body_count": component_mesh_count(j20a.component),
            },
            "mid360": {
                "index": MID360_INDEX,
                "name": mid360.name,
                "brep_body_count": len(component_bodies(mid360.component)),
                "mesh_body_count": component_mesh_count(mid360.component),
            },
            "screws": {
                str(index): {
                    "name": occurrence.name,
                    "brep_body_count": len(component_bodies(occurrence.component)),
                    "mesh_body_count": component_mesh_count(occurrence.component),
                }
                for index, occurrence in screws.items()
            },
        },
        "hole_pattern": {
            "j20_clearance_cylinder_count": len(j20_cylinders),
            "mid360_mount_cylinder_count": len(mid_cylinders),
            "width_mm": (x_values[-1] - x_values[0]) * 10.0,
            "height_along_plate_mm": (
                tangent_values[-1] - tangent_values[0]
            ) * 10.0,
            "matches": matches,
        },
        "modeled_mount_position": {
            "minimum_clearance_mm": modeled_clearance_mm,
            "interference": interference(design, j20a, mid360),
            "forced_contact_test": forced_contact,
        },
        "screw_to_j20a": {
            str(index): {
                "minimum_distance_mm": minimum_distance_mm(
                    application, j20a, occurrence
                ),
                "interference": interference(design, j20a, occurrence),
            }
            for index, occurrence in screws.items()
        },
        "animation_contract": {
            "only_visible_indices": [2, 4, 11, 12, 13, 14],
            "tightening_order": [11, 13, 12, 14],
            "nuts": 0,
            "tool_model": False,
        },
        "fusion_state": {
            "pending_snapshot": bool(design.snapshots.hasPendingSnapshot),
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
