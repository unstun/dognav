"""Validate the one-axis S410 through-bolt + top-nut preview in Fusion."""

import adsk.core
import adsk.fusion
import json
import os


globals().pop("run", None)


EVIDENCE_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-rev-c-s410-through-bolt-top-nut-print-correction"
)
REPORT_PATH = os.path.join(EVIDENCE_DIR, "single_axis_validation.json")

REV_B_COMPONENT_NAME = (
    "J17A_J20A_MONOLITHIC_REAR_WEB_PRINT_ADAPTATION_REV_B_NOT_OFFICIAL_CAD"
)
REV_C_COMPONENT_NAME = (
    "J17A_J20A_REV_C_S410_SINGLE_THROUGH_HOLE_PREVIEW_NOT_OFFICIAL_CAD"
)
BOLT_COMPONENT_NAME = (
    "S410_S1_M5X14_BOTTOM_UP_THROUGH_BOLT_VISUAL_CANDIDATE"
)
NUT_COMPONENT_NAME = "S410_S1_M5_TOP_HEX_NUT_VISUAL_CANDIDATE"
MOUNT_NORMAL = (0.0, 0.9659258262890683, 0.25881904510252074)
AXIS_POINT = (-32.90685957328745, 21.378538809797107, 260.49515922999285)
UNDERSIDE_PROJECTION_CM = 87.33122856653883
TOPSIDE_PROJECTION_CM = 88.07119113044189


def point(values):
    return adsk.core.Point3D.create(*values)


def vector(values):
    return adsk.core.Vector3D.create(*values)


def world_body_copy(temporary, occurrence, body_index=0):
    body = temporary.copy(occurrence.component.bRepBodies.item(body_index))
    if not temporary.transform(body, occurrence.transform2):
        raise RuntimeError("Could not transform body into assembly space")
    return body


def intersection_volume_mm3(temporary, first, second):
    target = temporary.copy(first)
    tool = temporary.copy(second)
    if not temporary.booleanOperation(
        target,
        tool,
        adsk.fusion.BooleanTypes.IntersectionBooleanType,
    ):
        return 0.0
    return target.volume * 1000.0


def distance_point_to_axis(point_value, origin, direction):
    delta = origin.vectorTo(point_value)
    axial = delta.dotProduct(direction)
    radial = adsk.core.Vector3D.create(
        delta.x - direction.x * axial,
        delta.y - direction.y * axial,
        delta.z - direction.z * axial,
    )
    return radial.length


def projection_interval(body, normal):
    values = []
    for vertex_index in range(body.vertices.count):
        value = body.vertices.item(vertex_index).geometry
        values.append(value.x * normal.x + value.y * normal.y + value.z * normal.z)
    if not values:
        bounds = body.boundingBox
        for value in (bounds.minPoint, bounds.maxPoint):
            values.append(
                value.x * normal.x + value.y * normal.y + value.z * normal.z
            )
    return min(values), max(values)


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences
    os.makedirs(EVIDENCE_DIR, exist_ok=True)

    found = {}
    guard = None
    for index in range(occurrences.count):
        occurrence = occurrences.item(index)
        name = occurrence.component.name
        if name == REV_B_COMPONENT_NAME:
            found["rev_b"] = (index, occurrence)
        elif name == REV_C_COMPONENT_NAME:
            found["rev_c"] = (index, occurrence)
        elif name == BOLT_COMPONENT_NAME:
            found["bolt"] = (index, occurrence)
        elif name == NUT_COMPONENT_NAME:
            found["nut"] = (index, occurrence)
        elif index == 3 and "S410" in name:
            guard = (index, occurrence)
    if set(found) != {"rev_b", "rev_c", "bolt", "nut"} or guard is None:
        raise RuntimeError("Corrected single-axis scene is incomplete")

    temporary = adsk.fusion.TemporaryBRepManager.get()
    rev_c_world = world_body_copy(temporary, found["rev_c"][1])
    guard_world = world_body_copy(temporary, guard[1])
    bolt_world = world_body_copy(temporary, found["bolt"][1])
    nut_world = world_body_copy(temporary, found["nut"][1])
    normal = vector(MOUNT_NORMAL)
    normal.normalize()
    axis_point = point(AXIS_POINT)

    clearance_faces = []
    rev_c_body = found["rev_c"][1].component.bRepBodies.item(0)
    for face_index in range(rev_c_body.faces.count):
        face = rev_c_body.faces.item(face_index)
        cylinder = adsk.core.Cylinder.cast(face.geometry)
        if cylinder is None or abs(cylinder.radius - 0.26) > 1.0e-5:
            continue
        axis = cylinder.axis.copy()
        axis.transformBy(found["rev_c"][1].transform2)
        axis.normalize()
        if abs(axis.dotProduct(normal)) < 0.999:
            continue
        origin = cylinder.origin.copy()
        origin.transformBy(found["rev_c"][1].transform2)
        clearance_faces.append(
            {
                "face_index": face_index,
                "radius_mm": cylinder.radius * 10.0,
                "axis_distance_mm": distance_point_to_axis(
                    axis_point, origin, axis
                )
                * 10.0,
            }
        )
    clearance_faces.sort(key=lambda item: item["axis_distance_mm"])

    collisions_mm3 = {
        "bolt_vs_rev_c": intersection_volume_mm3(
            temporary, bolt_world, rev_c_world
        ),
        "bolt_vs_s410_guard": intersection_volume_mm3(
            temporary, bolt_world, guard_world
        ),
        "nut_vs_rev_c": intersection_volume_mm3(
            temporary, nut_world, rev_c_world
        ),
        "nut_vs_s410_guard": intersection_volume_mm3(
            temporary, nut_world, guard_world
        ),
    }
    bolt_interval = projection_interval(bolt_world, normal)
    nut_interval = projection_interval(nut_world, normal)
    tolerance_mm3 = 0.01
    checks = {
        "rev_b_preserved": found["rev_b"][1].component.bRepBodies.count == 1,
        "rev_c_one_solid": (
            found["rev_c"][1].component.bRepBodies.count == 1
            and rev_c_body.isSolid
            and rev_c_body.lumps.count == 1
        ),
        "selected_rev_c_hole_is_5_2_mm": bool(clearance_faces)
        and clearance_faces[0]["axis_distance_mm"] < 0.05,
        "bolt_starts_at_or_below_underside": bolt_interval[0]
        <= UNDERSIDE_PROJECTION_CM,
        "bolt_reaches_above_topside": bolt_interval[1] > TOPSIDE_PROJECTION_CM,
        "nut_starts_on_topside": abs(nut_interval[0] - TOPSIDE_PROJECTION_CM)
        < 1.0e-5,
        "no_positive_volume_collision": all(
            value <= tolerance_mm3 for value in collisions_mm3.values()
        ),
        "old_direct_thread_screws_hidden": all(
            not occurrence.isLightBulbOn
            for _, occurrence in (
                (index, occurrences.item(index))
                for index in range(occurrences.count)
                if occurrences.item(index).component.name
                == "S410_TO_J20_M5X8_INDIVIDUAL_SCREW_VISUAL_CANDIDATE"
            )
        ),
        "new_bolt_and_nut_visible": (
            found["bolt"][1].isLightBulbOn and found["nut"][1].isLightBulbOn
        ),
    }
    report = {
        "stage": "experiment_and_analysis",
        "status": "passed" if all(checks.values()) else "failed",
        "indices": {
            key: value[0] for key, value in found.items()
        }
        | {"s410_guard": guard[0]},
        "checks": checks,
        "clearance_faces_nearest_first": clearance_faces,
        "projection_intervals_cm": {
            "modeled_stack": [UNDERSIDE_PROJECTION_CM, TOPSIDE_PROJECTION_CM],
            "bolt": list(bolt_interval),
            "nut": list(nut_interval),
        },
        "collision_intersection_volumes_mm3": collisions_mm3,
        "collision_tolerance_mm3": tolerance_mm3,
        "claim_boundary": (
            "CAD packaging validation only; contact pressure, thread engagement, "
            "fit, torque, print tolerance, strength, vibration, and real-robot safety "
            "remain unvalidated."
        ),
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
