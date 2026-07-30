"""Validate restart step 03 in the active 34-occurrence Fusion assembly."""

import adsk.core
import adsk.fusion
import json
import math


MOUNT_NORMAL = (0.0, 0.9659258262890683, 0.25881904510252074)
LAYER_AXIS = (0.0, 1.0, 0.0)
UPPER_SEPARATION = (0.0, 8.0, 0.0)

S410_TOOL_ANGLE_RANGES_DEG = {
    28: (240.0, 330.0),
    31: (60.0, 150.0),
    29: (210.0, 300.0),
    30: (30.0, 120.0),
}


def matrix_from_values(values):
    matrix = adsk.core.Matrix3D.create()
    if not matrix.setWithArray(values):
        raise RuntimeError("Could not set occurrence transform")
    return matrix


def translated_values(values, vector, amount=1.0):
    translated = list(values)
    translated[3] += vector[0] * amount
    translated[7] += vector[1] * amount
    translated[11] += vector[2] * amount
    return translated


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
    count = component.meshBodies.count
    for index in range(component.occurrences.count):
        count += component_mesh_count(component.occurrences.item(index).component)
    return count


def cylinders(occurrence):
    rows = []
    seen = set()
    for body in occurrence.bRepBodies:
        for face in body.faces:
            geometry = face.geometry
            if geometry and geometry.objectType == adsk.core.Cylinder.classType():
                origin = geometry.origin
                axis = [geometry.axis.x, geometry.axis.y, geometry.axis.z]
                length = math.sqrt(sum(value * value for value in axis))
                axis = [value / length for value in axis]
                row = {
                    "radius_mm": geometry.radius * 10.0,
                    "origin_cm": [origin.x, origin.y, origin.z],
                    "axis": axis,
                }
                key = tuple(
                    round(value, 5)
                    for value in [row["radius_mm"]]
                    + row["origin_cm"]
                    + row["axis"]
                )
                reverse_key = tuple(
                    round(value, 5)
                    for value in [row["radius_mm"]]
                    + row["origin_cm"]
                    + [-value for value in row["axis"]]
                )
                if key not in seen and reverse_key not in seen:
                    seen.add(key)
                    rows.append(row)
    return rows


def line_residual_mm(first, second):
    axis = first["axis"]
    direction_dot = sum(axis[i] * second["axis"][i] for i in range(3))
    if abs(direction_dot) < 0.9999:
        return None
    delta = [second["origin_cm"][i] - first["origin_cm"][i] for i in range(3)]
    axial = sum(delta[i] * axis[i] for i in range(3))
    transverse = [delta[i] - axial * axis[i] for i in range(3)]
    return math.sqrt(sum(value * value for value in transverse)) * 10.0


def cylinder_near_radius(occurrence, radius_mm):
    return min(cylinders(occurrence), key=lambda row: abs(row["radius_mm"] - radius_mm))


def expected_axis_match(fastener_cylinder, occurrence, expected_radius_mm):
    candidates = []
    for cylinder in cylinders(occurrence):
        residual = line_residual_mm(fastener_cylinder, cylinder)
        if residual is not None:
            candidates.append(
                (
                    residual,
                    abs(cylinder["radius_mm"] - expected_radius_mm),
                    cylinder,
                )
            )
    residual, _, cylinder = min(candidates, key=lambda item: (item[0], item[1]))
    return {
        "axis_residual_mm": residual,
        "matched_radius_mm": cylinder["radius_mm"],
    }


def cross_interference(design, first, second):
    count = 0
    volume_mm3 = 0.0
    for first_index in range(first.bRepBodies.count):
        for second_index in range(second.bRepBodies.count):
            entities = adsk.core.ObjectCollection.create()
            entities.add(first.bRepBodies.item(first_index))
            entities.add(second.bRepBodies.item(second_index))
            results = design.analyzeInterference(
                design.createInterferenceInput(entities)
            )
            for result_index in range(results.count):
                count += 1
                volume_mm3 += (
                    results.item(result_index).interferenceBody.volume * 1000.0
                )
    return {"result_count": count, "volume_mm3": volume_mm3}


def minimum_distance_mm(application, first, second):
    return application.measureManager.measureMinimumDistance(first, second).value * 10.0


def rodrigues(axis, angle):
    x, y, z = axis
    cosine = math.cos(angle)
    sine = math.sin(angle)
    one_minus = 1.0 - cosine
    return (
        (
            cosine + x * x * one_minus,
            x * y * one_minus - z * sine,
            x * z * one_minus + y * sine,
        ),
        (
            y * x * one_minus + z * sine,
            cosine + y * y * one_minus,
            y * z * one_minus - x * sine,
        ),
        (
            z * x * one_minus - y * sine,
            z * y * one_minus + x * sine,
            cosine + z * z * one_minus,
        ),
    )


def tool_matrix(screw_values, insertion_offset, angle):
    rotation = rodrigues(MOUNT_NORMAL, angle)
    values = [0.0] * 16
    for row in range(3):
        for column in range(3):
            values[row * 4 + column] = rotation[row][column]
    values[3] = (
        screw_values[3]
        + UPPER_SEPARATION[0]
        + MOUNT_NORMAL[0] * insertion_offset
    )
    values[7] = (
        screw_values[7]
        + UPPER_SEPARATION[1]
        + MOUNT_NORMAL[1] * insertion_offset
    )
    values[11] = (
        screw_values[11]
        + UPPER_SEPARATION[2]
        + MOUNT_NORMAL[2] * insertion_offset
    )
    values[15] = 1.0
    return matrix_from_values(values)


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    occurrences = design.rootComponent.occurrences
    if occurrences.count != 34:
        raise RuntimeError("Expected 34 root occurrences")

    component_indices = [1, 2, 3, 4, 15]
    component_report = {
        str(index): {
            "name": occurrences.item(index).name,
            "brep_body_count": len(
                component_bodies(occurrences.item(index).component)
            ),
            "mesh_body_count": component_mesh_count(
                occurrences.item(index).component
            ),
        }
        for index in component_indices
    }

    fastener_contracts = {
        7: {"radius_mm": 1.5, "targets": {1: 1.75, 2: 1.25}},
        8: {"radius_mm": 1.5, "targets": {1: 1.75, 2: 1.25}},
        18: {"radius_mm": 2.0, "targets": {1: 2.25, 2: 1.65}},
        19: {"radius_mm": 2.0, "targets": {1: 2.25, 2: 1.65}},
        28: {"radius_mm": 2.5, "targets": {2: 2.10, 3: 2.60}},
        29: {"radius_mm": 2.5, "targets": {2: 2.10, 3: 2.60}},
        30: {"radius_mm": 2.5, "targets": {2: 2.10, 3: 2.60}},
        31: {"radius_mm": 2.5, "targets": {2: 2.10, 3: 2.60}},
    }
    axis_report = {}
    fastener_cylinders = {}
    for index, contract in fastener_contracts.items():
        fastener_cylinder = cylinder_near_radius(
            occurrences.item(index), contract["radius_mm"]
        )
        fastener_cylinders[index] = fastener_cylinder
        axis_report[str(index)] = {
            "shaft_radius_mm": fastener_cylinder["radius_mm"],
            "targets": {
                str(target_index): expected_axis_match(
                    fastener_cylinder,
                    occurrences.item(target_index),
                    target_radius,
                )
                for target_index, target_radius in contract["targets"].items()
            },
        }

    closure_pairs = {
        "7_to_9": (7, 9, 1.6),
        "8_to_10": (8, 10, 1.6),
        "18_to_20": (18, 20, 2.15),
        "18_to_22": (18, 22, 1.65),
        "19_to_21": (19, 21, 2.15),
        "19_to_23": (19, 23, 1.65),
    }
    closure_axis_residuals = {}
    for label, (fastener_index, closure_index, closure_radius) in closure_pairs.items():
        closure_cylinder = cylinder_near_radius(
            occurrences.item(closure_index), closure_radius
        )
        closure_axis_residuals[label] = line_residual_mm(
            fastener_cylinders[fastener_index], closure_cylinder
        )

    pair_indices = {
        "j17a_j20a": (1, 2),
        "j17a_s410": (1, 3),
        "j17a_mid360": (1, 4),
        "j17a_d435i": (1, 15),
        "j20a_s410": (2, 3),
        "j20a_mid360": (2, 4),
        "s410_mid360": (3, 4),
    }
    final_relations = {
        label: {
            "minimum_distance_mm": minimum_distance_mm(
                application, occurrences.item(first), occurrences.item(second)
            ),
            "cross_interference": cross_interference(
                design, occurrences.item(first), occurrences.item(second)
            ),
        }
        for label, (first, second) in pair_indices.items()
    }

    transformed_indices = [2, 3, 4, 33]
    original_transforms = {
        index: list(occurrences.item(index).transform.asArray())
        for index in transformed_indices
    }
    screw_transforms = {
        index: list(occurrences.item(index).transform.asArray())
        for index in S410_TOOL_ANGLE_RANGES_DEG
    }
    guard_approach = []
    upper_join = []
    tool_samples = []
    try:
        for offset_cm in [5.5, 4.4, 3.3, 2.2, 1.1, 0.0]:
            occurrences.item(3).transform = matrix_from_values(
                translated_values(
                    original_transforms[3], MOUNT_NORMAL, offset_cm
                )
            )
            guard_approach.append(
                {
                    "offset_cm": offset_cm,
                    "s410_j20a": cross_interference(
                        design, occurrences.item(3), occurrences.item(2)
                    ),
                    "s410_mid360": cross_interference(
                        design, occurrences.item(3), occurrences.item(4)
                    ),
                }
            )

        occurrences.item(3).transform = matrix_from_values(original_transforms[3])
        for offset_cm in [8.0, 6.0, 4.0, 2.0, 1.0, 0.5, 0.2, 0.0]:
            for index in [2, 3, 4]:
                occurrences.item(index).transform = matrix_from_values(
                    translated_values(
                        original_transforms[index], LAYER_AXIS, offset_cm
                    )
                )
            relations = []
            for upper_index in [2, 3, 4]:
                for lower_index in [1, 15]:
                    relations.append(
                        {
                            "pair": [upper_index, lower_index],
                            "cross_interference": cross_interference(
                                design,
                                occurrences.item(upper_index),
                                occurrences.item(lower_index),
                            ),
                        }
                    )
            upper_join.append({"offset_cm": offset_cm, "relations": relations})

        for index in [2, 3, 4]:
            occurrences.item(index).transform = matrix_from_values(
                translated_values(original_transforms[index], UPPER_SEPARATION)
            )
        for screw_index, (begin_deg, end_deg) in S410_TOOL_ANGLE_RANGES_DEG.items():
            sample_states = [
                ("start_begin", 0.8, begin_deg),
                ("start_mid", 0.575, (begin_deg + end_deg) / 2.0),
                ("start_end", 0.35, end_deg),
                ("tighten_begin", 0.35, begin_deg),
                ("tighten_mid", 0.175, (begin_deg + end_deg) / 2.0),
                ("tighten_end", 0.0, end_deg),
            ]
            for label, insertion_offset, angle_deg in sample_states:
                occurrences.item(33).transform = tool_matrix(
                    screw_transforms[screw_index],
                    insertion_offset,
                    math.radians(angle_deg),
                )
                tool_samples.append(
                    {
                        "screw_index": screw_index,
                        "sample": label,
                        "external_relations": {
                            str(part_index): cross_interference(
                                design,
                                occurrences.item(33),
                                occurrences.item(part_index),
                            )
                            for part_index in [2, 3, 4]
                        },
                    }
                )
    finally:
        for index, values in original_transforms.items():
            occurrences.item(index).transform = matrix_from_values(values)

    report = {
        "document": application.activeDocument.name,
        "root_occurrence_count": occurrences.count,
        "components": component_report,
        "axis_alignment": axis_report,
        "closure_axis_residuals_mm": closure_axis_residuals,
        "final_relations": final_relations,
        "path_validation": {
            "guard_approach": guard_approach,
            "upper_join": upper_join,
            "short_l_key_samples": tool_samples,
        },
        "animation_contract": {
            "guard_start_and_tighten_order": [28, 31, 29, 30],
            "bottom_up_layer_fasteners": [7, 8, 18, 19],
            "front_nuts": [9, 10],
            "rear_washer_locknut_pairs": [[20, 22], [21, 23]],
            "robot_present": False,
        },
        "fusion_state": {
            "pending_snapshot": bool(design.snapshots.hasPendingSnapshot)
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
