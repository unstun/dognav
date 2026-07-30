"""Measure why the underside M5 socket head collides with the Rev C print body."""

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
REPORT_PATH = os.path.join(EVIDENCE_DIR, "underside_head_seat_diagnosis.json")
REV_C_COMPONENT_NAME = (
    "J17A_J20A_REV_C_S410_SINGLE_THROUGH_HOLE_PREVIEW_NOT_OFFICIAL_CAD"
)
MOUNT_NORMAL = (0.0, 0.9659258262890683, 0.25881904510252074)
AXIS_POINT = (-32.90685957328745, 21.378538809797107, 260.49515922999285)
UNDERSIDE_PROJECTION_CM = 87.33122856653883


def point(values):
    return adsk.core.Point3D.create(*values)


def vector(values):
    return adsk.core.Vector3D.create(*values)


def shifted(origin, direction, amount):
    return adsk.core.Point3D.create(
        origin.x + direction.x * amount,
        origin.y + direction.y * amount,
        origin.z + direction.z * amount,
    )


def projection(value, direction):
    return value.x * direction.x + value.y * direction.y + value.z * direction.z


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


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences
    os.makedirs(EVIDENCE_DIR, exist_ok=True)

    rev_c = None
    for index in range(occurrences.count):
        if occurrences.item(index).component.name == REV_C_COMPONENT_NAME:
            rev_c = occurrences.item(index)
            break
    if rev_c is None:
        raise RuntimeError("Rev C single-axis preview is missing")

    temporary = adsk.fusion.TemporaryBRepManager.get()
    rev_c_world = temporary.copy(rev_c.component.bRepBodies.item(0))
    if not temporary.transform(rev_c_world, rev_c.transform2):
        raise RuntimeError("Could not transform Rev C into assembly space")
    normal = vector(MOUNT_NORMAL)
    normal.normalize()
    axis_point = point(AXIS_POINT)
    underside = shifted(
        axis_point,
        normal,
        UNDERSIDE_PROJECTION_CM - projection(axis_point, normal),
    )

    shaft = temporary.createCylinderOrCone(
        underside,
        0.25,
        shifted(underside, normal, 1.40),
        0.25,
    )
    shaft_collision_mm3 = intersection_volume_mm3(
        temporary, shaft, rev_c_world
    )
    trials = []
    for offset_mm in range(0, 151):
        offset_cm = offset_mm / 100.0
        head_top = shifted(underside, normal, -offset_cm)
        head_bottom = shifted(head_top, normal, -0.50)
        head = temporary.createCylinderOrCone(
            head_bottom, 0.425, head_top, 0.425
        )
        collision_mm3 = intersection_volume_mm3(
            temporary, head, rev_c_world
        )
        trials.append(
            {
                "head_seat_offset_below_nominal_mm": float(offset_mm) / 10.0,
                "intersection_mm3": collision_mm3,
            }
        )

    first_clear = next(
        (
            trial
            for trial in trials
            if trial["intersection_mm3"] <= 0.01
        ),
        None,
    )
    report = {
        "stage": "experiment_and_analysis",
        "shaft_collision_mm3": shaft_collision_mm3,
        "head_collision_at_nominal_seat_mm3": trials[0]["intersection_mm3"],
        "first_clear_offset": first_clear,
        "trials": trials,
        "interpretation": (
            "A zero shaft collision with a positive head collision means the 5.2 mm "
            "through hole is clear but the current underside surface cannot accept the "
            "8.5 mm socket-head envelope at the modeled hole-face endpoint."
        ),
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(
        json.dumps(
            {
                "shaft_collision_mm3": shaft_collision_mm3,
                "head_collision_at_nominal_seat_mm3": trials[0][
                    "intersection_mm3"
                ],
                "first_clear_offset": first_clear,
                "last_trial": trials[-1],
                "report": REPORT_PATH,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
