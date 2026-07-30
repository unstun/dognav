"""Add underside head access to the one-axis S410 through-bolt preview.

The first direction-corrected preview proved that the M5 shaft clears the new
5.2 mm through hole, but the 8.5 mm socket head intersects the irregular print
body below the hole.  This reversible follow-up preserves both Rev B and the
failed first preview, then adds a 9.5 mm x 6.5 mm underside access bore and
reuses the bottom-up M5x14 bolt/top-nut stack.
"""

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
F3D_PATH = os.path.join(
    EVIDENCE_DIR,
    "lite3-rev-c2-s410-single-through-bolt-top-nut-head-access-preview.f3d",
)
REPORT_PATH = os.path.join(EVIDENCE_DIR, "single_axis_head_access_build_report.json")

FAILED_REV_C_NAME = (
    "J17A_J20A_REV_C_S410_SINGLE_THROUGH_HOLE_PREVIEW_NOT_OFFICIAL_CAD"
)
FAILED_BOLT_NAME = "S410_S1_M5X14_BOTTOM_UP_THROUGH_BOLT_VISUAL_CANDIDATE"
FAILED_NUT_NAME = "S410_S1_M5_TOP_HEX_NUT_VISUAL_CANDIDATE"
COMPONENT_NAME = (
    "J17A_J20A_REV_C2_S410_SINGLE_THROUGH_HOLE_HEAD_ACCESS_PREVIEW_NOT_OFFICIAL_CAD"
)
BODY_NAME = "J17A_J20A_REV_C2_S410_THROUGH_HOLE_WITH_UNDERSIDE_HEAD_ACCESS"
BOLT_NAME = "S410_S1_M5X14_BOTTOM_UP_BOLT_HEAD_ACCESS_PREVIEW"
NUT_NAME = "S410_S1_M5_TOP_HEX_NUT_HEAD_ACCESS_PREVIEW"

MOUNT_NORMAL = (0.0, 0.9659258262890683, 0.25881904510252074)
AXIS_POINT = (-32.90685957328745, 21.378538809797107, 260.49515922999285)
UNDERSIDE_PROJECTION_CM = 87.33122856653883
TOPSIDE_PROJECTION_CM = 88.07119113044189
HEAD_ACCESS_RADIUS_CM = 0.475
HEAD_ACCESS_DEPTH_CM = 0.65

TRANSFORM_ATTRIBUTE_GROUP = "codex_full_installation_animation"
FINAL_TRANSFORM_ATTRIBUTE = "final_transform"
FINAL_VISIBILITY_ATTRIBUTE = "final_visibility"


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


def add_component_body(root, name, body_name, temporary_body, appearance):
    occurrence = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    component = occurrence.component
    component.name = name
    base_feature = component.features.baseFeatures.add()
    base_feature.name = body_name + "_BASE_FEATURE"
    base_feature.startEdit()
    body = component.bRepBodies.add(temporary_body, base_feature)
    if body is None:
        raise RuntimeError("Could not add " + name)
    if appearance is not None:
        body.appearance = appearance
    base_feature.finishEdit()
    body = component.bRepBodies.item(0)
    body.name = body_name
    return occurrence, body


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences
    os.makedirs(EVIDENCE_DIR, exist_ok=True)

    failed = {}
    for index in range(occurrences.count):
        occurrence = occurrences.item(index)
        name = occurrence.component.name
        if name == FAILED_REV_C_NAME:
            failed["rev_c"] = (index, occurrence)
        elif name == FAILED_BOLT_NAME:
            failed["bolt"] = (index, occurrence)
        elif name == FAILED_NUT_NAME:
            failed["nut"] = (index, occurrence)
        elif name in (COMPONENT_NAME, BOLT_NAME, NUT_NAME):
            raise RuntimeError("The head-access preview already exists")
    if set(failed) != {"rev_c", "bolt", "nut"}:
        raise RuntimeError("The first single-axis preview is incomplete")
    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()

    temporary = adsk.fusion.TemporaryBRepManager.get()
    normal = vector(MOUNT_NORMAL)
    normal.normalize()
    axis_point = point(AXIS_POINT)
    underside = shifted(
        axis_point,
        normal,
        UNDERSIDE_PROJECTION_CM - projection(axis_point, normal),
    )

    candidate_temp = temporary.copy(
        failed["rev_c"][1].component.bRepBodies.item(0)
    )
    access_start = shifted(underside, normal, -HEAD_ACCESS_DEPTH_CM)
    access_cutter = temporary.createCylinderOrCone(
        access_start,
        HEAD_ACCESS_RADIUS_CM,
        underside,
        HEAD_ACCESS_RADIUS_CM,
    )
    if access_cutter is None or not temporary.booleanOperation(
        candidate_temp,
        access_cutter,
        adsk.fusion.BooleanTypes.DifferenceBooleanType,
    ):
        raise RuntimeError("Could not cut the underside socket-head access bore")
    if (
        not candidate_temp.isSolid
        or candidate_temp.lumps.count != 1
        or candidate_temp.shells.count != 1
    ):
        raise RuntimeError("Head-access candidate is not one closed solid")

    candidate_occurrence, candidate_body = add_component_body(
        root,
        COMPONENT_NAME,
        BODY_NAME,
        candidate_temp,
        failed["rev_c"][1].component.bRepBodies.item(0).appearance,
    )
    bolt_occurrence, bolt_body = add_component_body(
        root,
        BOLT_NAME,
        "M5X14_BOTTOM_UP_SOCKET_HEAD_BOLT_HEAD_ACCESS_PREVIEW",
        temporary.copy(failed["bolt"][1].component.bRepBodies.item(0)),
        failed["bolt"][1].component.bRepBodies.item(0).appearance,
    )
    nut_occurrence, nut_body = add_component_body(
        root,
        NUT_NAME,
        "M5_TOP_HEX_NUT_HEAD_ACCESS_PREVIEW",
        temporary.copy(failed["nut"][1].component.bRepBodies.item(0)),
        failed["nut"][1].component.bRepBodies.item(0).appearance,
    )

    contract = {
        "selected_position": "S1_TOP_LEFT",
        "through_hole_diameter_mm": 5.2,
        "underside_head_access": {
            "diameter_mm": HEAD_ACCESS_RADIUS_CM * 20.0,
            "depth_mm": HEAD_ACCESS_DEPTH_CM * 10.0,
            "reason": "8.5 mm socket head collided with irregular underside while the M5 shaft itself was clear",
        },
        "bolt": "M5x14 bottom-up visual candidate",
        "nut": "M5 top hex nut visual candidate",
        "measured_stack_mm": (TOPSIDE_PROJECTION_CM - UNDERSIDE_PROJECTION_CM)
        * 10.0,
        "modeled_thread_protrusion_above_nut_mm": 2.6003743609693677,
    }
    for component in (
        candidate_occurrence.component,
        bolt_occurrence.component,
        nut_occurrence.component,
    ):
        component.attributes.add(
            "hardware_evidence", "classification", "user_corrected_print_candidate"
        )
        component.attributes.add("hardware_evidence", "official_cad", "false")
        component.attributes.add(
            "hardware_evidence", "single_axis_contract", json.dumps(contract)
        )
        component.attributes.add(
            "hardware_evidence",
            "claim_boundary",
            "One-axis packaging candidate only; head-access weakening, print tolerance, torque, strength, vibration, and real-robot safety are unvalidated",
        )

    for _, occurrence in failed.values():
        occurrence.isLightBulbOn = False
        set_final_state_attributes(occurrence, False)
    candidate_occurrence.isLightBulbOn = True
    bolt_occurrence.isLightBulbOn = True
    nut_occurrence.isLightBulbOn = True
    set_final_state_attributes(candidate_occurrence, True)
    set_final_state_attributes(bolt_occurrence, True)
    set_final_state_attributes(nut_occurrence, True)
    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()

    export_options = design.exportManager.createFusionArchiveExportOptions(
        F3D_PATH, root
    )
    if export_options is None or not design.exportManager.execute(export_options):
        raise RuntimeError("Could not export the head-access preview F3D")

    report = {
        "stage": "experiment_and_analysis",
        "status": "awaiting_collision_validation",
        "indices": {
            "failed_preview_preserved_hidden": [
                failed["rev_c"][0],
                failed["bolt"][0],
                failed["nut"][0],
            ],
            "head_access_candidate": occurrences.count - 3,
            "bottom_up_bolt": occurrences.count - 2,
            "top_nut": occurrences.count - 1,
        },
        "contract": contract,
        "geometry": {
            "candidate_is_one_solid": candidate_body.isSolid
            and candidate_body.lumps.count == 1,
            "bolt_is_solid": bolt_body.isSolid,
            "nut_is_solid": nut_body.isSolid,
        },
        "f3d": F3D_PATH,
        "claim_boundary": (
            "This corrects the modeled access collision only. The 9.5 x 6.5 mm "
            "head-access bore is not structurally released or physically validated."
        ),
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
