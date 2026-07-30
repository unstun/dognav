"""Validate the persistent one-piece J17A/J20A candidate in Fusion.

The source brackets are used only as preserved references for access-corridor
checks. The candidate must remain one B-rep solid, retain the D435i, MID360,
and S410 interface cylinders, and add no volumetric collision with those three
manufacturer sensor components.
"""

import adsk.core
import adsk.fusion
import json
import math
import os


EVIDENCE_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-j17a-j20a-monolithic-print-adaptation-candidate"
)
REPORT_PATH = os.path.join(EVIDENCE_DIR, "fusion_validation.json")

J17A_INDEX = 1
J20A_INDEX = 2
S410_INDEX = 3
MID360_INDEX = 4
D435I_INDEX = 15
CANDIDATE_INDEX = 34
REJECTED_LAYER_HARDWARE_INDICES = (7, 8, 9, 10, 18, 19, 20, 21, 22, 23)

COMPONENT_NAME = "J17A_J20A_MONOLITHIC_PRINT_ADAPTATION_REV_A_NOT_OFFICIAL_CAD"
BODY_NAME = "J17A_J20A_MONOLITHIC_ONE_SOLID_REV_A"

MOUNT_NORMAL = (0.0, 0.9659258262890683, 0.25881904510252074)
CAMERA_AXIS = (0.0, -0.34202014332566627, 0.9396926207859093)

MID360_AXIS_POINTS = (
    (-32.24700964468146, 21.452842807920245, 258.6723716491626),
    (-28.647009644681464, 21.452842807920245, 258.6723716491626),
    (-28.647009644681464, 22.69517422441234, 254.03592768297506),
    (-32.24700964468146, 22.69517422441234, 254.03592768297506),
)
D435I_AXIS_POINTS = (
    (-32.697009644681464, 21.835352488197586, 262.0531323590644),
    (-28.197009644681464, 21.835352488197586, 262.0531323590644),
)
S410_AXIS_POINTS = (
    (-32.90685957328738, 21.378538809797117, 260.49515922999285),
    (-27.98715971607558, 21.378538809797085, 260.49515922999274),
    (-32.935037516962154, 23.53789375953872, 252.4363368459814),
    (-27.95898177240097, 23.5378937595389, 252.4363368459814),
)


def point(values):
    return adsk.core.Point3D.create(*values)


def shifted(values, direction, amount):
    return tuple(values[index] + direction[index] * amount for index in range(3))


def normalized(values):
    length = math.sqrt(sum(value * value for value in values))
    return tuple(value / length for value in values)


def body_interference(design, first, second):
    total_count = 0
    total_volume_mm3 = 0.0
    for first_body in first.bRepBodies:
        for second_body in second.bRepBodies:
            entities = adsk.core.ObjectCollection.create()
            entities.add(first_body)
            entities.add(second_body)
            results = design.analyzeInterference(
                design.createInterferenceInput(entities)
            )
            total_count += results.count
            total_volume_mm3 += sum(
                results.item(index).interferenceBody.volume * 1000.0
                for index in range(results.count)
            )
    return {
        "result_count": total_count,
        "volume_mm3": total_volume_mm3,
    }


def corridor_clearance(application, axis_points, outward, blocker_occurrences):
    outward = normalized(outward)
    temporary = adsk.fusion.TemporaryBRepManager.get()
    rows = []
    for sequence, axis_point in enumerate(axis_points, start=1):
        start = shifted(axis_point, outward, 0.55)
        end = shifted(start, outward, 3.0)
        corridor = temporary.createCylinderOrCone(
            point(start), 0.30, point(end), 0.30
        )
        blocker_rows = []
        for occurrence in blocker_occurrences:
            distances_mm = [
                application.measureManager.measureMinimumDistance(
                    corridor, body
                ).value
                * 10.0
                for body in occurrence.bRepBodies
            ]
            blocker_rows.append(
                {
                    "occurrence": occurrence.name,
                    "minimum_distance_mm": min(distances_mm),
                }
            )
        rows.append(
            {
                "axis": sequence,
                "diameter_mm": 6.0,
                "length_mm": 30.0,
                "start_cm": list(start),
                "end_cm": list(end),
                "blockers": blocker_rows,
                "clear": all(
                    row["minimum_distance_mm"] > 1.0e-5
                    for row in blocker_rows
                ),
            }
        )
    return rows


def cylinder_count(body, radius_mm, direction, tolerance_mm=1.0e-4):
    direction = normalized(direction)
    matches = []
    for face in body.faces:
        geometry = face.geometry
        if not geometry or geometry.objectType != adsk.core.Cylinder.classType():
            continue
        axis = normalized((geometry.axis.x, geometry.axis.y, geometry.axis.z))
        alignment = abs(sum(axis[index] * direction[index] for index in range(3)))
        if (
            abs(geometry.radius * 10.0 - radius_mm) <= tolerance_mm
            and alignment >= 0.99999
        ):
            matches.append(
                {
                    "origin_cm": [
                        geometry.origin.x,
                        geometry.origin.y,
                        geometry.origin.z,
                    ],
                    "radius_mm": geometry.radius * 10.0,
                    "axis_alignment": alignment,
                }
            )
    return matches


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences
    if occurrences.count != 35:
        raise RuntimeError("Expected the reviewed 35-occurrence candidate scene")

    candidate = occurrences.item(CANDIDATE_INDEX)
    source_j17a = occurrences.item(J17A_INDEX)
    source_j20a = occurrences.item(J20A_INDEX)
    if candidate.component.name != COMPONENT_NAME:
        raise RuntimeError("Unexpected candidate component")
    if candidate.bRepBodies.count != 1:
        raise RuntimeError("Candidate occurrence does not expose one B-rep body")
    body = candidate.bRepBodies.item(0)

    interface_cylinders = {
        "d435i_2x_m3_clearance": cylinder_count(body, 1.6, CAMERA_AXIS),
        "mid360_4x_m3_clearance": cylinder_count(body, 1.75, MOUNT_NORMAL),
        "s410_4x_m5_receivers": cylinder_count(body, 2.1, MOUNT_NORMAL),
    }
    sensor_interference = {
        "d435i": body_interference(design, candidate, occurrences.item(D435I_INDEX)),
        "mid360": body_interference(design, candidate, occurrences.item(MID360_INDEX)),
        "s410_guard": body_interference(design, candidate, occurrences.item(S410_INDEX)),
    }

    access_corridors = {
        "mid360_underside": corridor_clearance(
            application,
            MID360_AXIS_POINTS,
            tuple(-value for value in MOUNT_NORMAL),
            (source_j17a, occurrences.item(D435I_INDEX)),
        ),
        "d435i_camera_side": corridor_clearance(
            application,
            D435I_AXIS_POINTS,
            CAMERA_AXIS,
            (
                source_j20a,
                occurrences.item(MID360_INDEX),
                occurrences.item(S410_INDEX),
            ),
        ),
        "s410_external": corridor_clearance(
            application,
            S410_AXIS_POINTS,
            MOUNT_NORMAL,
            (source_j17a, occurrences.item(MID360_INDEX)),
        ),
    }

    interface_pass = (
        len(interface_cylinders["d435i_2x_m3_clearance"]) == 2
        and len(interface_cylinders["mid360_4x_m3_clearance"]) == 4
        and len(interface_cylinders["s410_4x_m5_receivers"]) == 4
    )
    sensor_clearance_pass = all(
        row["volume_mm3"] <= 1.0e-7 for row in sensor_interference.values()
    )
    access_pass = all(
        row["clear"]
        for group in access_corridors.values()
        for row in group
    )
    source_visibility_pass = (
        not source_j17a.isLightBulbOn
        and not source_j20a.isLightBulbOn
        and candidate.isLightBulbOn
        and all(
            not occurrences.item(index).isLightBulbOn
            for index in REJECTED_LAYER_HARDWARE_INDICES
        )
    )
    topology_pass = (
        candidate.component.bRepBodies.count == 1
        and candidate.component.meshBodies.count == 0
        and body.name == BODY_NAME
        and body.isSolid
        and body.lumps.count == 1
        and body.shells.count == 1
    )
    classification_pass = (
        candidate.component.attributes.itemByName(
            "hardware_evidence", "classification"
        ).value
        == "print_adaptation"
        and candidate.component.attributes.itemByName(
            "hardware_evidence", "official_cad"
        ).value
        == "false"
    )

    report = {
        "stage": "experiment_and_analysis",
        "status": "awaiting_visual_review",
        "document": application.activeDocument.name,
        "root_occurrence_count": occurrences.count,
        "candidate": {
            "index": CANDIDATE_INDEX,
            "component": candidate.component.name,
            "body": body.name,
            "brep_body_count": candidate.component.bRepBodies.count,
            "mesh_body_count": candidate.component.meshBodies.count,
            "is_solid": body.isSolid,
            "lump_count": body.lumps.count,
            "shell_count": body.shells.count,
            "face_count": body.faces.count,
            "volume_mm3": body.volume * 1000.0,
        },
        "source_preservation": {
            "j17a_name": source_j17a.component.name,
            "j20a_name": source_j20a.component.name,
            "sources_hidden": not source_j17a.isLightBulbOn
            and not source_j20a.isLightBulbOn,
            "candidate_visible": candidate.isLightBulbOn,
            "former_layer_hardware_hidden": all(
                not occurrences.item(index).isLightBulbOn
                for index in REJECTED_LAYER_HARDWARE_INDICES
            ),
        },
        "interface_cylinders": interface_cylinders,
        "sensor_interference": sensor_interference,
        "tool_access_corridors": access_corridors,
        "checks": {
            "topology_pass": topology_pass,
            "classification_pass": classification_pass,
            "source_visibility_pass": source_visibility_pass,
            "interface_pass": interface_pass,
            "sensor_clearance_pass": sensor_clearance_pass,
            "access_pass": access_pass,
        },
        "pass": bool(
            topology_pass
            and classification_pass
            and source_visibility_pass
            and interface_pass
            and sensor_clearance_pass
            and access_pass
        ),
        "claim_boundary": (
            "Geometry and modeled tool access only; material, print orientation, "
            "strength, fatigue, torque, vibration, and real-hardware safety are unvalidated."
        ),
    }

    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["pass"]:
        raise RuntimeError("Monolithic candidate validation failed; inspect fusion_validation.json")
