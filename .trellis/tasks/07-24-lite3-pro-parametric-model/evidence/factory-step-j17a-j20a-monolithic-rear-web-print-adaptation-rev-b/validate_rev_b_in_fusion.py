"""Validate the persistent Rev B continuous-rear-web candidate in Fusion."""

import adsk.core
import adsk.fusion
import json
import math
import os


EVIDENCE_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-j17a-j20a-monolithic-rear-web-print-adaptation-rev-b"
)
REPORT_PATH = os.path.join(EVIDENCE_DIR, "fusion_validation.json")

J17A_INDEX = 1
J20A_INDEX = 2
S410_INDEX = 3
MID360_INDEX = 4
D435I_INDEX = 15
REV_A_INDEX = 34
REV_B_INDEX = 35
REJECTED_LAYER_HARDWARE_INDICES = (7, 8, 9, 10, 18, 19, 20, 21, 22, 23)
RETAINED_FASTENER_INDICES = (11, 12, 13, 14, 16, 17, 24, 25, 26, 28, 29, 30, 31)

COMPONENT_NAME = (
    "J17A_J20A_MONOLITHIC_REAR_WEB_PRINT_ADAPTATION_REV_B_NOT_OFFICIAL_CAD"
)
BODY_NAME = "J17A_J20A_MONOLITHIC_REAR_WEB_ONE_SOLID_REV_B"

REAR_LEFT_X_CM = -33.84112221937691
REAR_RIGHT_X_CM = -27.05289706998607
WEB_FRONT_Y_CM = 20.468141858307484
WEB_REAR_Y_CM = 23.218141858307483
WEB_TOP_Z_CM = 251.75
WEB_THICKNESS_CM = 0.60

MOUNT_NORMAL = (0.0, 0.9659258262890683, 0.25881904510252074)
CAMERA_AXIS = (0.0, -0.34202014332566627, 0.9396926207859093)
TOOL_CORRIDORS = {
    "mid360_underside": {
        "points": (
            (-32.24700964468146, 21.452842807920245, 258.6723716491626),
            (-28.647009644681464, 21.452842807920245, 258.6723716491626),
            (-28.647009644681464, 22.69517422441234, 254.03592768297506),
            (-32.24700964468146, 22.69517422441234, 254.03592768297506),
        ),
        "direction": tuple(-value for value in MOUNT_NORMAL),
    },
    "d435i_camera_side": {
        "points": (
            (-32.697009644681464, 21.835352488197586, 262.0531323590644),
            (-28.197009644681464, 21.835352488197586, 262.0531323590644),
        ),
        "direction": CAMERA_AXIS,
    },
    "s410_external": {
        "points": (
            (-32.90685957328738, 21.378538809797117, 260.49515922999285),
            (-27.98715971607558, 21.378538809797085, 260.49515922999274),
            (-32.935037516962154, 23.53789375953872, 252.4363368459814),
            (-27.95898177240097, 23.5378937595389, 252.4363368459814),
        ),
        "direction": MOUNT_NORMAL,
    },
}


def point(values):
    return adsk.core.Point3D.create(*values)


def vector(values):
    return adsk.core.Vector3D.create(*values)


def normalized(values):
    length = math.sqrt(sum(value * value for value in values))
    return tuple(value / length for value in values)


def shifted(values, direction, amount):
    return tuple(values[index] + direction[index] * amount for index in range(3))


def make_rear_web(temporary):
    box = adsk.core.OrientedBoundingBox3D.create(
        point(
            (
                (REAR_LEFT_X_CM + REAR_RIGHT_X_CM) * 0.5,
                (WEB_FRONT_Y_CM + WEB_REAR_Y_CM) * 0.5,
                WEB_TOP_Z_CM - WEB_THICKNESS_CM * 0.5,
            )
        ),
        vector((1.0, 0.0, 0.0)),
        vector((0.0, 1.0, 0.0)),
        REAR_RIGHT_X_CM - REAR_LEFT_X_CM,
        WEB_REAR_Y_CM - WEB_FRONT_Y_CM,
        WEB_THICKNESS_CM,
    )
    web = temporary.createBox(box)
    if web is None:
        raise RuntimeError("Could not create validation rear web")
    return web


def aabb_overlap(first, second):
    return not (
        first.maxPoint.x < second.minPoint.x
        or first.minPoint.x > second.maxPoint.x
        or first.maxPoint.y < second.minPoint.y
        or first.minPoint.y > second.maxPoint.y
        or first.maxPoint.z < second.minPoint.z
        or first.minPoint.z > second.maxPoint.z
    )


def temporary_intersection_mm3(temporary, first, second):
    if not aabb_overlap(first.boundingBox, second.boundingBox):
        return 0.0
    target = temporary.copy(first)
    tool = temporary.copy(second)
    if not temporary.booleanOperation(
        target, tool, adsk.fusion.BooleanTypes.IntersectionBooleanType
    ):
        return 0.0
    return target.volume * 1000.0


def persistent_pair_interference(design, first, second):
    if not aabb_overlap(first.boundingBox, second.boundingBox):
        return {"result_count": 0, "volume_mm3": 0.0}
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


def occurrence_interference(design, first, second):
    count = 0
    volume_mm3 = 0.0
    for first_body in first.bRepBodies:
        for second_body in second.bRepBodies:
            row = persistent_pair_interference(design, first_body, second_body)
            count += row["result_count"]
            volume_mm3 += row["volume_mm3"]
    return {"result_count": count, "volume_mm3": volume_mm3}


def nested_occurrence_bodies(root_occurrence):
    bodies = []
    stack = [root_occurrence]
    while stack:
        occurrence = stack.pop()
        for index in range(occurrence.bRepBodies.count):
            bodies.append(occurrence.bRepBodies.item(index))
        children = occurrence.childOccurrences
        for index in range(children.count):
            stack.append(children.item(index))
    return bodies


def cylinder_matches(body, radius_mm, direction, tolerance_mm=1.0e-4):
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
    if occurrences.count != 36:
        raise RuntimeError("Expected the reviewed 36-occurrence Rev B scene")
    rev_b = occurrences.item(REV_B_INDEX)
    if rev_b.component.name != COMPONENT_NAME:
        raise RuntimeError("Unexpected Rev B component")
    if rev_b.bRepBodies.count != 1:
        raise RuntimeError("Rev B does not expose one occurrence B-rep")
    body = rev_b.bRepBodies.item(0)
    temporary = adsk.fusion.TemporaryBRepManager.get()
    web = make_rear_web(temporary)

    topology_pass = (
        rev_b.component.bRepBodies.count == 1
        and rev_b.component.meshBodies.count == 0
        and rev_b.component.bRepBodies.item(0).name == BODY_NAME
        and body.isSolid
        and body.lumps.count == 1
        and body.shells.count == 1
    )
    classification_pass = (
        rev_b.component.attributes.itemByName(
            "hardware_evidence", "classification"
        ).value
        == "print_adaptation"
        and rev_b.component.attributes.itemByName(
            "hardware_evidence", "official_cad"
        ).value
        == "false"
    )
    source_visibility_pass = (
        not occurrences.item(J17A_INDEX).isLightBulbOn
        and not occurrences.item(J20A_INDEX).isLightBulbOn
        and not occurrences.item(REV_A_INDEX).isLightBulbOn
        and rev_b.isLightBulbOn
        and all(
            not occurrences.item(index).isLightBulbOn
            for index in REJECTED_LAYER_HARDWARE_INDICES
        )
    )

    interface_cylinders = {
        "d435i_2x_m3_clearance": cylinder_matches(body, 1.6, CAMERA_AXIS),
        "mid360_4x_m3_clearance": cylinder_matches(body, 1.75, MOUNT_NORMAL),
        "s410_4x_m5_receivers": cylinder_matches(body, 2.1, MOUNT_NORMAL),
    }
    interface_pass = (
        len(interface_cylinders["d435i_2x_m3_clearance"]) == 2
        and len(interface_cylinders["mid360_4x_m3_clearance"]) == 4
        and len(interface_cylinders["s410_4x_m5_receivers"]) == 4
    )

    sensor_interference = {
        "d435i": occurrence_interference(
            design, rev_b, occurrences.item(D435I_INDEX)
        ),
        "mid360": occurrence_interference(
            design, rev_b, occurrences.item(MID360_INDEX)
        ),
        "s410_guard": occurrence_interference(
            design, rev_b, occurrences.item(S410_INDEX)
        ),
    }
    sensor_clearance_pass = all(
        row["volume_mm3"] <= 1.0e-7 for row in sensor_interference.values()
    )

    robot_hits = []
    for robot_body in nested_occurrence_bodies(occurrences.item(0)):
        row = persistent_pair_interference(design, body, robot_body)
        if row["volume_mm3"] > 1.0e-7:
            robot_hits.append(
                {
                    "body": robot_body.name,
                    "result_count": row["result_count"],
                    "volume_mm3": row["volume_mm3"],
                }
            )
    robot_clearance_pass = not robot_hits

    web_engagement = {
        "manufacturer_j17a_region_mm3": temporary_intersection_mm3(
            temporary, web, occurrences.item(J17A_INDEX).bRepBodies.item(0)
        ),
        "manufacturer_j20a_region_mm3": temporary_intersection_mm3(
            temporary, web, occurrences.item(J20A_INDEX).bRepBodies.item(0)
        ),
        "rev_a_mm3": temporary_intersection_mm3(
            temporary, web, occurrences.item(REV_A_INDEX).bRepBodies.item(0)
        ),
    }
    engagement_pass = all(value > 0.0 for value in web_engagement.values())

    web_fastener_interference = {}
    for index in RETAINED_FASTENER_INDICES:
        occurrence = occurrences.item(index)
        web_fastener_interference[str(index)] = {
            "name": occurrence.name,
            "volume_mm3": sum(
                temporary_intersection_mm3(temporary, web, fastener_body)
                for fastener_body in occurrence.bRepBodies
            ),
        }
    retained_fastener_pass = all(
        row["volume_mm3"] <= 1.0e-7
        for row in web_fastener_interference.values()
    )

    guard_clearance_mm = min(
        application.measureManager.measureMinimumDistance(web, guard_body).value
        * 10.0
        for guard_body in occurrences.item(S410_INDEX).bRepBodies
    )
    guard_clearance_pass = guard_clearance_mm >= 1.0

    tool_corridors = {}
    for group_name, spec in TOOL_CORRIDORS.items():
        rows = []
        for sequence, axis_point in enumerate(spec["points"], start=1):
            start = shifted(axis_point, spec["direction"], 0.55)
            end = shifted(start, spec["direction"], 3.0)
            corridor = temporary.createCylinderOrCone(
                point(start), 0.30, point(end), 0.30
            )
            rows.append(
                {
                    "axis": sequence,
                    "diameter_mm": 6.0,
                    "length_mm": 30.0,
                    "rear_web_intersection_mm3": temporary_intersection_mm3(
                        temporary, web, corridor
                    ),
                    "rear_web_minimum_distance_mm": application.measureManager.measureMinimumDistance(
                        web, corridor
                    ).value
                    * 10.0,
                }
            )
        tool_corridors[group_name] = rows
    tool_access_pass = all(
        row["rear_web_intersection_mm3"] <= 1.0e-7
        for rows in tool_corridors.values()
        for row in rows
    )

    report = {
        "stage": "experiment_and_analysis",
        "status": "awaiting_visual_review",
        "document": application.activeDocument.name,
        "root_occurrence_count": occurrences.count,
        "candidate": {
            "index": REV_B_INDEX,
            "component": rev_b.component.name,
            "body": rev_b.component.bRepBodies.item(0).name,
            "brep_body_count": rev_b.component.bRepBodies.count,
            "mesh_body_count": rev_b.component.meshBodies.count,
            "is_solid": body.isSolid,
            "lump_count": body.lumps.count,
            "shell_count": body.shells.count,
            "face_count": body.faces.count,
            "volume_mm3": body.volume * 1000.0,
        },
        "rear_web": {
            "x_span_mm": (REAR_RIGHT_X_CM - REAR_LEFT_X_CM) * 10.0,
            "depth_mm": (WEB_REAR_Y_CM - WEB_FRONT_Y_CM) * 10.0,
            "thickness_mm": WEB_THICKNESS_CM * 10.0,
            "top_z_cm": WEB_TOP_Z_CM,
            "bottom_z_cm": WEB_TOP_Z_CM - WEB_THICKNESS_CM,
            "engagement": web_engagement,
            "s410_minimum_clearance_mm": guard_clearance_mm,
        },
        "interface_cylinders": interface_cylinders,
        "sensor_interference": sensor_interference,
        "robot_interference": {
            "checked_body_count": len(
                nested_occurrence_bodies(occurrences.item(0))
            ),
            "hits": robot_hits,
        },
        "retained_fastener_interference_with_new_web": web_fastener_interference,
        "tool_corridors_against_new_web": tool_corridors,
        "checks": {
            "topology_pass": topology_pass,
            "classification_pass": classification_pass,
            "source_visibility_pass": source_visibility_pass,
            "interface_pass": interface_pass,
            "sensor_clearance_pass": sensor_clearance_pass,
            "robot_clearance_pass": robot_clearance_pass,
            "engagement_pass": engagement_pass,
            "retained_fastener_pass": retained_fastener_pass,
            "guard_clearance_pass": guard_clearance_pass,
            "tool_access_pass": tool_access_pass,
        },
        "pass": bool(
            topology_pass
            and classification_pass
            and source_visibility_pass
            and interface_pass
            and sensor_clearance_pass
            and robot_clearance_pass
            and engagement_pass
            and retained_fastener_pass
            and guard_clearance_pass
            and tool_access_pass
        ),
        "claim_boundary": (
            "Geometry, modeled packaging, and tested tool access only; FDM "
            "material, print orientation, layer adhesion, strength, fatigue, "
            "vibration, cable routing, and real-hardware safety are unvalidated."
        ),
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["pass"]:
        raise RuntimeError("Rev B Fusion validation failed")
