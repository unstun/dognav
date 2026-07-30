"""Validate the collision-corrected S410 underside-head-access preview."""

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
REPORT_PATH = os.path.join(EVIDENCE_DIR, "single_axis_head_access_validation.json")

COMPONENT_NAME = (
    "J17A_J20A_REV_C2_S410_SINGLE_THROUGH_HOLE_HEAD_ACCESS_PREVIEW_NOT_OFFICIAL_CAD"
)
BOLT_NAME = "S410_S1_M5X14_BOTTOM_UP_BOLT_HEAD_ACCESS_PREVIEW"
NUT_NAME = "S410_S1_M5_TOP_HEX_NUT_HEAD_ACCESS_PREVIEW"
FAILED_NAMES = (
    "J17A_J20A_REV_C_S410_SINGLE_THROUGH_HOLE_PREVIEW_NOT_OFFICIAL_CAD",
    "S410_S1_M5X14_BOTTOM_UP_THROUGH_BOLT_VISUAL_CANDIDATE",
    "S410_S1_M5_TOP_HEX_NUT_VISUAL_CANDIDATE",
)
MOUNT_NORMAL = (0.0, 0.9659258262890683, 0.25881904510252074)
AXIS_POINT = (-32.90685957328745, 21.378538809797107, 260.49515922999285)
UNDERSIDE_PROJECTION_CM = 87.33122856653883
TOPSIDE_PROJECTION_CM = 88.07119113044189


def point(values):
    return adsk.core.Point3D.create(*values)


def vector(values):
    return adsk.core.Vector3D.create(*values)


def world_body_copy(temporary, occurrence):
    body = temporary.copy(occurrence.component.bRepBodies.item(0))
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


def cylinder_records(occurrence, target_radius_cm, axis_point, normal):
    records = []
    body = occurrence.component.bRepBodies.item(0)
    for face_index in range(body.faces.count):
        cylinder = adsk.core.Cylinder.cast(body.faces.item(face_index).geometry)
        if cylinder is None or abs(cylinder.radius - target_radius_cm) > 1.0e-5:
            continue
        origin = cylinder.origin.copy()
        origin.transformBy(occurrence.transform2)
        axis = cylinder.axis.copy()
        axis.transformBy(occurrence.transform2)
        axis.normalize()
        if abs(axis.dotProduct(normal)) < 0.999:
            continue
        records.append(
            {
                "face_index": face_index,
                "radius_mm": cylinder.radius * 10.0,
                "axis_distance_mm": distance_point_to_axis(
                    axis_point, origin, axis
                )
                * 10.0,
            }
        )
    records.sort(key=lambda item: item["axis_distance_mm"])
    return records


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    occurrences = design.rootComponent.occurrences
    os.makedirs(EVIDENCE_DIR, exist_ok=True)

    found = {}
    failed = []
    guard = None
    for index in range(occurrences.count):
        occurrence = occurrences.item(index)
        name = occurrence.component.name
        if name == COMPONENT_NAME:
            found["candidate"] = (index, occurrence)
        elif name == BOLT_NAME:
            found["bolt"] = (index, occurrence)
        elif name == NUT_NAME:
            found["nut"] = (index, occurrence)
        elif name in FAILED_NAMES:
            failed.append((index, occurrence))
        elif index == 3 and "S410" in name:
            guard = (index, occurrence)
    if set(found) != {"candidate", "bolt", "nut"} or guard is None:
        raise RuntimeError("Head-access preview scene is incomplete")

    temporary = adsk.fusion.TemporaryBRepManager.get()
    candidate_world = world_body_copy(temporary, found["candidate"][1])
    bolt_world = world_body_copy(temporary, found["bolt"][1])
    nut_world = world_body_copy(temporary, found["nut"][1])
    guard_world = world_body_copy(temporary, guard[1])
    normal = vector(MOUNT_NORMAL)
    normal.normalize()
    axis_point = point(AXIS_POINT)

    through_faces = cylinder_records(
        found["candidate"][1], 0.26, axis_point, normal
    )
    access_faces = cylinder_records(
        found["candidate"][1], 0.475, axis_point, normal
    )
    collisions_mm3 = {
        "bolt_vs_candidate": intersection_volume_mm3(
            temporary, bolt_world, candidate_world
        ),
        "bolt_vs_s410_guard": intersection_volume_mm3(
            temporary, bolt_world, guard_world
        ),
        "nut_vs_candidate": intersection_volume_mm3(
            temporary, nut_world, candidate_world
        ),
        "nut_vs_s410_guard": intersection_volume_mm3(
            temporary, nut_world, guard_world
        ),
    }
    candidate_body = found["candidate"][1].component.bRepBodies.item(0)
    checks = {
        "candidate_one_closed_solid": (
            found["candidate"][1].component.bRepBodies.count == 1
            and candidate_body.isSolid
            and candidate_body.lumps.count == 1
            and candidate_body.shells.count == 1
        ),
        "selected_through_hole_is_5_2_mm": bool(through_faces)
        and through_faces[0]["axis_distance_mm"] < 0.05,
        "selected_head_access_is_9_5_mm": bool(access_faces)
        and access_faces[0]["axis_distance_mm"] < 0.05,
        "zero_modeled_positive_volume_collision": all(
            value <= 0.01 for value in collisions_mm3.values()
        ),
        "failed_preview_preserved_hidden": len(failed) == 3
        and all(not occurrence.isLightBulbOn for _, occurrence in failed),
        "corrected_candidate_visible": all(
            occurrence.isLightBulbOn for _, occurrence in found.values()
        ),
        "official_s410_preserved": guard[1].component.bRepBodies.count > 0,
    }
    report = {
        "stage": "experiment_and_analysis",
        "status": "passed" if all(checks.values()) else "failed",
        "indices": {
            key: value[0] for key, value in found.items()
        }
        | {
            "s410_guard": guard[0],
            "failed_preview_hidden": [index for index, _ in failed],
        },
        "checks": checks,
        "through_hole_faces_nearest_first": through_faces,
        "head_access_faces_nearest_first": access_faces,
        "collision_intersection_volumes_mm3": collisions_mm3,
        "measured_stack_mm": (
            TOPSIDE_PROJECTION_CM - UNDERSIDE_PROJECTION_CM
        )
        * 10.0,
        "claim_boundary": (
            "Zero modeled collision validates CAD packaging only. The access-bore "
            "effect on print strength, fit, torque, vibration, and real-robot safety "
            "remains unvalidated."
        ),
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
