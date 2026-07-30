"""Build and validate the physical-Lite3 carrier V1 in the live Fusion scene.

The script preserves all manufacturer source occurrences, creates a separately
named 10 mm continuous-rear-web print adaptation, adds a measurement-pending
Interface keep-out, exports a review F3D, and records collision/tool evidence.
"""

import adsk.core
import adsk.fusion
import json
import math
import os


globals().pop("run", None)


PACKAGE_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "physical-lite3-mid360-d435i-fusion-adapter-v1"
)
PARAMETERS_PATH = os.path.join(PACKAGE_DIR, "parameters.json")
F3D_PATH = os.path.join(
    PACKAGE_DIR, "cad", "lite3-mid360-d435i-fusion-adapter-v1-review.f3d"
)
REPORT_PATH = os.path.join(PACKAGE_DIR, "validation", "fusion_assembly_validation.json")

SOURCE_COMPONENT = (
    "J17A_J20A_MONOLITHIC_REAR_WEB_PRINT_ADAPTATION_REV_B_NOT_OFFICIAL_CAD"
)
COMPONENT_NAME = "LITE3_MID360_D435I_MONOLITHIC_CARRIER_V1_NOT_OFFICIAL_CAD"
BODY_NAME = "LITE3_MID360_D435I_MONOLITHIC_CARRIER_V1_10MM_REAR_WEB"
INTERFACE_COMPONENT = "PHYSICAL_INTERFACE_KEEP_OUT_PENDING_MEASUREMENT"
INTERFACE_BODY = "INTERFACE_CONSERVATIVE_ENVELOPE_NOT_PRINT_PART"

TRANSFORM_ATTRIBUTE_GROUP = "codex_full_installation_animation"
FINAL_TRANSFORM_ATTRIBUTE = "final_transform"
FINAL_VISIBILITY_ATTRIBUTE = "final_visibility"

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


def replace_attribute(entity, group, name, value):
    existing = entity.attributes.itemByName(group, name)
    if existing is not None:
        existing.deleteMe()
    entity.attributes.add(group, name, value)


def set_final_state_attributes(occurrence, visible):
    replace_attribute(
        occurrence,
        TRANSFORM_ATTRIBUTE_GROUP,
        FINAL_TRANSFORM_ATTRIBUTE,
        json.dumps(list(occurrence.transform2.asArray())),
    )
    replace_attribute(
        occurrence,
        TRANSFORM_ATTRIBUTE_GROUP,
        FINAL_VISIBILITY_ATTRIBUTE,
        "true" if visible else "false",
    )


def find_occurrence(occurrences, component_name):
    for index in range(occurrences.count):
        occurrence = occurrences.item(index)
        if occurrence.component.name == component_name:
            return index, occurrence
    return None, None


def find_occurrence_prefix(occurrences, prefix):
    for index in range(occurrences.count):
        occurrence = occurrences.item(index)
        if occurrence.component.name.startswith(prefix):
            return index, occurrence
    return None, None


def add_world_body(root, temporary_body, component_name, body_name, appearance=None):
    occurrence = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    component = occurrence.component
    component.name = component_name
    base_feature = component.features.baseFeatures.add()
    base_feature.name = "PARAMETERIZED_SOURCE_DERIVATION"
    base_feature.startEdit()
    body = component.bRepBodies.add(temporary_body, base_feature)
    if body is None:
        raise RuntimeError("Could not persist " + component_name)
    if appearance is not None:
        body.appearance = appearance
    base_feature.finishEdit()
    body = component.bRepBodies.item(0)
    body.name = body_name
    return occurrence, body


def make_box(temporary, x_min, x_max, y_min, y_max, z_min, z_max):
    box = adsk.core.OrientedBoundingBox3D.create(
        point(((x_min + x_max) * 0.5, (y_min + y_max) * 0.5, (z_min + z_max) * 0.5)),
        vector((1.0, 0.0, 0.0)),
        vector((0.0, 1.0, 0.0)),
        x_max - x_min,
        y_max - y_min,
        z_max - z_min,
    )
    result = temporary.createBox(box)
    if result is None:
        raise RuntimeError("Could not create temporary box")
    return result


def aabb_overlap(first, second):
    return not (
        first.maxPoint.x < second.minPoint.x
        or first.minPoint.x > second.maxPoint.x
        or first.maxPoint.y < second.minPoint.y
        or first.minPoint.y > second.maxPoint.y
        or first.maxPoint.z < second.minPoint.z
        or first.minPoint.z > second.maxPoint.z
    )


def aabb_distance_mm(first, second):
    gaps = []
    for first_min, first_max, second_min, second_max in (
        (first.minPoint.x, first.maxPoint.x, second.minPoint.x, second.maxPoint.x),
        (first.minPoint.y, first.maxPoint.y, second.minPoint.y, second.maxPoint.y),
        (first.minPoint.z, first.maxPoint.z, second.minPoint.z, second.maxPoint.z),
    ):
        if first_max < second_min:
            gaps.append(second_min - first_max)
        elif second_max < first_min:
            gaps.append(first_min - second_max)
        else:
            gaps.append(0.0)
    return math.sqrt(sum(value * value for value in gaps)) * 10.0


def intersection_volume_mm3(temporary, first, second):
    if not aabb_overlap(first.boundingBox, second.boundingBox):
        return 0.0
    target = temporary.copy(first)
    tool = temporary.copy(second)
    if not temporary.booleanOperation(
        target, tool, adsk.fusion.BooleanTypes.IntersectionBooleanType
    ):
        return 0.0
    return target.volume * 1000.0


def occurrence_intersection_mm3(temporary, first, second):
    total = 0.0
    for first_index in range(first.bRepBodies.count):
        for second_index in range(second.bRepBodies.count):
            total += intersection_volume_mm3(
                temporary,
                first.bRepBodies.item(first_index),
                second.bRepBodies.item(second_index),
            )
    return total


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
        if abs(geometry.radius * 10.0 - radius_mm) <= tolerance_mm and alignment >= 0.99999:
            matches.append(
                {
                    "origin_cm": [geometry.origin.x, geometry.origin.y, geometry.origin.z],
                    "radius_mm": geometry.radius * 10.0,
                    "axis_alignment": alignment,
                }
            )
    return matches


def make_tool_corridor(temporary, origin, direction, diameter_cm=0.60, length_cm=3.0):
    direction = normalized(direction)
    start = point(origin)
    end = point(tuple(origin[index] + direction[index] * length_cm for index in range(3)))
    corridor = temporary.createCylinderOrCone(start, diameter_cm * 0.5, end, diameter_cm * 0.5)
    if corridor is None:
        raise RuntimeError("Could not build tool corridor")
    return corridor


def determinant(transform):
    values = transform.asArray()
    return (
        values[0] * (values[5] * values[10] - values[6] * values[9])
        - values[1] * (values[4] * values[10] - values[6] * values[8])
        + values[2] * (values[4] * values[9] - values[5] * values[8])
    )


def select_robot_occurrence(occurrences):
    best = None
    best_count = -1
    for index in range(occurrences.count):
        occurrence = occurrences.item(index)
        count = len(nested_occurrence_bodies(occurrence))
        if count > best_count:
            best = (index, occurrence)
            best_count = count
    return best[0], best[1], best_count


def choose_robot_white_appearance(robot_occurrence, fallback):
    for body in nested_occurrence_bodies(robot_occurrence):
        appearance = body.appearance
        if appearance is not None and "white" in appearance.name.lower():
            return appearance
    return fallback


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences
    temporary = adsk.fusion.TemporaryBRepManager.get()
    os.makedirs(os.path.dirname(F3D_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(PARAMETERS_PATH, "r", encoding="utf-8") as stream:
        parameters = json.load(stream)

    source_index, source_occurrence = find_occurrence(occurrences, SOURCE_COMPONENT)
    if source_occurrence is None or source_occurrence.bRepBodies.count != 1:
        raise RuntimeError("Frozen Rev B source component is missing")
    source_body = source_occurrence.bRepBodies.item(0)

    candidate_index, candidate_occurrence = find_occurrence(occurrences, COMPONENT_NAME)
    if candidate_occurrence is None:
        target = temporary.copy(source_body)
        web_bounds = parameters["geometry_mm"]["rear_web_world_bounds"]
        web_thickness_cm = parameters["geometry_mm"]["rear_web_thickness"]["value"] / 10.0
        web = make_box(
            temporary,
            web_bounds["x_min"] / 10.0,
            web_bounds["x_max"] / 10.0,
            web_bounds["y_min"] / 10.0,
            web_bounds["y_max"] / 10.0,
            web_bounds["front_z"] / 10.0 - web_thickness_cm,
            web_bounds["front_z"] / 10.0,
        )
        if not temporary.booleanOperation(target, web, adsk.fusion.BooleanTypes.UnionBooleanType):
            raise RuntimeError("Could not thicken the continuous rear web")
        if not target.isSolid or target.lumps.count != 1 or target.shells.count != 1:
            raise RuntimeError("V1 Fusion target is not one closed solid")
        candidate_occurrence, candidate_body = add_world_body(
            root, target, COMPONENT_NAME, BODY_NAME, source_body.appearance
        )
        candidate_index = occurrences.count - 1
        component = candidate_occurrence.component
        component.attributes.add("hardware_evidence", "classification", "print_adaptation")
        component.attributes.add("hardware_evidence", "official_cad", "false")
        component.attributes.add("hardware_evidence", "source_component", SOURCE_COMPONENT)
        component.attributes.add(
            "hardware_evidence",
            "rear_web_thickness_mm",
            str(parameters["geometry_mm"]["rear_web_thickness"]["value"]),
        )
        component.attributes.add(
            "hardware_evidence",
            "claim_boundary",
            "Archived V1 upper-geometry evidence only; robot interface rejected for the purchased current Lite3 Pro",
        )
    else:
        if candidate_occurrence.bRepBodies.count != 1:
            raise RuntimeError("Existing V1 occurrence does not contain one B-rep body")
        candidate_body = candidate_occurrence.bRepBodies.item(0)

    robot_index, robot_occurrence, robot_body_count = select_robot_occurrence(occurrences)
    if robot_body_count < 200:
        raise RuntimeError("Could not identify the full Lite3 robot occurrence")

    interface_index, interface_occurrence = find_occurrence(occurrences, INTERFACE_COMPONENT)
    if interface_occurrence is None:
        keepout = parameters["interface_keepout_mm"]
        candidate_bounds = candidate_body.boundingBox
        center_x = (candidate_bounds.minPoint.x + candidate_bounds.maxPoint.x) * 0.5
        width_cm = keepout["nominal_width"] / 10.0
        height_cm = keepout["nominal_height"] / 10.0
        length_cm = keepout["nominal_length"] / 10.0
        clearance_cm = keepout["nominal_front_clearance"] / 10.0
        front_z = candidate_bounds.minPoint.z - clearance_cm
        y_min = 20.456141858307483
        interface_temp = make_box(
            temporary,
            center_x - width_cm * 0.5,
            center_x + width_cm * 0.5,
            y_min,
            y_min + height_cm,
            front_z - length_cm,
            front_z,
        )
        interface_appearance = choose_robot_white_appearance(robot_occurrence, source_body.appearance)
        interface_occurrence, interface_body = add_world_body(
            root, interface_temp, INTERFACE_COMPONENT, INTERFACE_BODY, interface_appearance
        )
        interface_index = occurrences.count - 1
        interface_occurrence.component.attributes.add(
            "hardware_evidence", "classification", "user_photo_keepout_estimate"
        )
        interface_occurrence.component.attributes.add("hardware_evidence", "export_as_print_part", "false")
        interface_occurrence.component.attributes.add("hardware_evidence", "measurement_status", keepout["status"])
        interface_occurrence.component.attributes.add(
            "hardware_evidence",
            "claim_boundary",
            "Conservative visualization envelope only; no physical dimensions are inferred from the perspective photo",
        )
    else:
        interface_body = interface_occurrence.bRepBodies.item(0)

    source_occurrence.isLightBulbOn = False
    candidate_occurrence.isLightBulbOn = True
    interface_occurrence.isLightBulbOn = True
    interface_body.opacity = 1.0
    for index in range(occurrences.count):
        occurrence = occurrences.item(index)
        name = occurrence.component.name
        if name.startswith("1T21-J17A") or name.startswith("1T21-J20A"):
            occurrence.isLightBulbOn = False
        if "REV_C" in name or "HEAD_ACCESS_PREVIEW" in name or "THROUGH_HOLE" in name:
            occurrence.isLightBulbOn = False
        set_final_state_attributes(occurrence, bool(occurrence.isLightBulbOn))
    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()

    s410_index, s410 = find_occurrence_prefix(occurrences, "1CA5-S410")
    mid360_index, mid360 = find_occurrence_prefix(occurrences, "MID-360_4_ASM")
    d435_index, d435 = find_occurrence_prefix(occurrences, "LITE3_FULLSTACK_D435I_REAL_BREP")
    if any(item is None for item in (s410, mid360, d435)):
        raise RuntimeError("One or more official sensor occurrences are missing")

    interface_cylinders = {
        "d435i_2x_m3_clearance": cylinder_matches(candidate_body, 1.6, CAMERA_AXIS),
        "mid360_4x_m3_clearance": cylinder_matches(candidate_body, 1.75, MOUNT_NORMAL),
        "s410_4x_m5_receivers": cylinder_matches(candidate_body, 2.1, MOUNT_NORMAL),
    }
    sensor_interference = {
        "d435i_mm3": occurrence_intersection_mm3(temporary, candidate_occurrence, d435),
        "mid360_mm3": occurrence_intersection_mm3(temporary, candidate_occurrence, mid360),
        "s410_mm3": occurrence_intersection_mm3(temporary, candidate_occurrence, s410),
    }

    robot_hits = []
    for body_index, robot_body in enumerate(nested_occurrence_bodies(robot_occurrence)):
        volume = intersection_volume_mm3(temporary, candidate_body, robot_body)
        if volume > 0.01:
            robot_hits.append({"body_index": body_index, "volume_mm3": volume})

    interface_collision_mm3 = intersection_volume_mm3(temporary, candidate_body, interface_body)
    interface_distance_mm = aabb_distance_mm(
        candidate_body.boundingBox, interface_body.boundingBox
    )

    tool_corridors = {}
    for group, contract in TOOL_CORRIDORS.items():
        rows = []
        for axis_index, origin in enumerate(contract["points"], start=1):
            direction = normalized(contract["direction"])
            entry_offset_cm = (
                parameters["tool_and_cable_envelopes_mm"]["driver_corridor_entry_offset"]
                / 10.0
            )
            external_origin = tuple(
                origin[index] + direction[index] * entry_offset_cm
                for index in range(3)
            )
            corridor = make_tool_corridor(
                temporary, external_origin, contract["direction"]
            )
            rows.append(
                {
                    "axis": axis_index,
                    "external_entry_offset_mm": entry_offset_cm * 10.0,
                    "carrier_intersection_mm3": intersection_volume_mm3(temporary, corridor, candidate_body),
                    "interface_intersection_mm3": intersection_volume_mm3(temporary, corridor, interface_body),
                }
            )
        tool_corridors[group] = rows

    determinant_checks = {
        "carrier": determinant(candidate_occurrence.transform2),
        "interface": determinant(interface_occurrence.transform2),
        "s410": determinant(s410.transform2),
        "mid360": determinant(mid360.transform2),
        "d435i": determinant(d435.transform2),
    }

    export_options = design.exportManager.createFusionArchiveExportOptions(F3D_PATH, root)
    if export_options is None or not design.exportManager.execute(export_options):
        raise RuntimeError("Could not export the V1 review F3D")

    report = {
        "stage": "experiment_and_analysis",
        "status": "historical_internal_fusion_geometry_pass_rejected_for_current_pro_interface",
        "document": application.activeDocument.name,
        "indices": {
            "source_rev_b_hidden": source_index,
            "carrier_v1": candidate_index,
            "physical_interface_keepout": interface_index,
            "robot": robot_index,
            "s410": s410_index,
            "mid360": mid360_index,
            "d435i": d435_index,
        },
        "carrier": {
            "component": candidate_occurrence.component.name,
            "body": candidate_body.name,
            "brep_body_count": candidate_occurrence.bRepBodies.count,
            "mesh_body_count": candidate_occurrence.component.meshBodies.count,
            "is_solid": candidate_body.isSolid,
            "lump_count": candidate_body.lumps.count,
            "shell_count": candidate_body.shells.count,
            "face_count": candidate_body.faces.count,
            "volume_mm3": candidate_body.volume * 1000.0,
        },
        "interface_cylinders": interface_cylinders,
        "sensor_interference": sensor_interference,
        "robot_interference": {"checked_body_count": robot_body_count, "hits": robot_hits},
        "physical_interface_keepout": {
            "classification": "user_photo_keepout_estimate",
            "collision_mm3": interface_collision_mm3,
            "minimum_distance_mm": interface_distance_mm,
            "dimensions_status": parameters["interface_keepout_mm"]["status"],
        },
        "tool_corridors": tool_corridors,
        "rotation_determinants": determinant_checks,
        "f3d": {"path": F3D_PATH, "bytes": os.path.getsize(F3D_PATH)},
        "claim_boundary": "The archived Fusion scene retains internal V1 registration and upper-module evidence only. Its robot body, keep-out, holes, screws, spacers, and installation path are rejected for the purchased current Lite3 Pro.",
    }
    report["checks"] = {
        "topology_pass": bool(candidate_body.isSolid and candidate_body.lumps.count == 1 and candidate_body.shells.count == 1),
        "interface_count_pass": bool(
            len(interface_cylinders["d435i_2x_m3_clearance"]) == 2
            and len(interface_cylinders["mid360_4x_m3_clearance"]) == 4
            and len(interface_cylinders["s410_4x_m5_receivers"]) == 4
        ),
        "sensor_collision_pass": all(value <= 0.01 for value in sensor_interference.values()),
        "robot_collision_pass": not robot_hits,
        "interface_keepout_pass": interface_collision_mm3 <= 0.01 and interface_distance_mm >= 9.99,
        "tool_corridor_pass": all(
            row["carrier_intersection_mm3"] <= 0.01 and row["interface_intersection_mm3"] <= 0.01
            for rows in tool_corridors.values()
            for row in rows
        ),
        "rigid_transform_pass": all(abs(value - 1.0) <= 1.0e-9 for value in determinant_checks.values()),
        "f3d_export_pass": os.path.exists(F3D_PATH) and os.path.getsize(F3D_PATH) > 1_000_000,
    }
    report["pass"] = all(report["checks"].values())
    with open(REPORT_PATH, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["pass"]:
        raise RuntimeError("Fusion V1 assembly validation failed")
