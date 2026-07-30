"""Build a reversible Rev B monolithic J17A/J20A rear-web candidate.

Rev A remains unchanged and hidden. Rev B copies its world-space solid and
adds one continuous 6 mm FDM web between the two former rear M4 connection
axes. The web is shifted downward to preserve modeled S410 clearance while
engaging both manufacturer-source bracket regions.

This is a print adaptation, not official CAD or a structural release.
"""

import adsk.core
import adsk.fusion
import json
import os


globals().pop("run", None)


EVIDENCE_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-j17a-j20a-monolithic-rear-web-print-adaptation-rev-b"
)
PARENT_F3D = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-j17a-j20a-monolithic-print-adaptation-candidate/"
    "lite3-j17a-j20a-monolithic-print-adaptation-rev-a-review.f3d"
)
CANDIDATE_STEP = os.path.join(
    EVIDENCE_DIR,
    "j17a-j20a-monolithic-rear-web-print-adaptation-rev-b.step",
)
BUILD_REPORT = os.path.join(EVIDENCE_DIR, "build_report.json")

SOURCE_OCCURRENCE_COUNT = 35
REV_A_INDEX = 34
J17A_INDEX = 1
J20A_INDEX = 2
REJECTED_LAYER_HARDWARE_INDICES = (7, 8, 9, 10, 18, 19, 20, 21, 22, 23)

REV_A_COMPONENT_NAME = (
    "J17A_J20A_MONOLITHIC_PRINT_ADAPTATION_REV_A_NOT_OFFICIAL_CAD"
)
COMPONENT_NAME = (
    "J17A_J20A_MONOLITHIC_REAR_WEB_PRINT_ADAPTATION_REV_B_NOT_OFFICIAL_CAD"
)
BODY_NAME = "J17A_J20A_MONOLITHIC_REAR_WEB_ONE_SOLID_REV_B"

TRANSFORM_ATTRIBUTE_GROUP = "codex_full_installation_animation"
FINAL_TRANSFORM_ATTRIBUTE = "final_transform"
FINAL_VISIBILITY_ATTRIBUTE = "final_visibility"

REAR_LEFT_X_CM = -33.84112221937691
REAR_RIGHT_X_CM = -27.05289706998607
WEB_FRONT_Y_CM = 20.468141858307484
WEB_REAR_Y_CM = 23.218141858307483
WEB_TOP_Z_CM = 251.75
WEB_THICKNESS_CM = 0.60


def point(values):
    return adsk.core.Point3D.create(*values)


def vector(values):
    return adsk.core.Vector3D.create(*values)


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


def matrix_from_values(values):
    matrix = adsk.core.Matrix3D.create()
    if not matrix.setWithArray(values):
        raise RuntimeError("Could not restore occurrence transform")
    return matrix


def make_rear_web(temporary):
    center = point(
        (
            (REAR_LEFT_X_CM + REAR_RIGHT_X_CM) * 0.5,
            (WEB_FRONT_Y_CM + WEB_REAR_Y_CM) * 0.5,
            WEB_TOP_Z_CM - WEB_THICKNESS_CM * 0.5,
        )
    )
    box = adsk.core.OrientedBoundingBox3D.create(
        center,
        vector((1.0, 0.0, 0.0)),
        vector((0.0, 1.0, 0.0)),
        REAR_RIGHT_X_CM - REAR_LEFT_X_CM,
        WEB_REAR_Y_CM - WEB_FRONT_Y_CM,
        WEB_THICKNESS_CM,
    )
    web = temporary.createBox(box)
    if web is None:
        raise RuntimeError("Could not create the temporary rear web")
    return web


def intersection_volume_mm3(temporary, first, second):
    target = temporary.copy(first)
    tool = temporary.copy(second)
    if not temporary.booleanOperation(
        target, tool, adsk.fusion.BooleanTypes.IntersectionBooleanType
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

    if occurrences.count != SOURCE_OCCURRENCE_COUNT:
        raise RuntimeError(
            "Expected the reviewed 35-occurrence Rev A scene, found "
            + str(occurrences.count)
        )
    if not os.path.exists(PARENT_F3D):
        raise RuntimeError("The frozen Rev A parent F3D is missing")
    if occurrences.item(REV_A_INDEX).component.name != REV_A_COMPONENT_NAME:
        raise RuntimeError("Unexpected Rev A parent component")
    for index in range(occurrences.count):
        if occurrences.item(index).component.name == COMPONENT_NAME:
            raise RuntimeError("Rev B candidate already exists")
    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()

    original_transforms = {
        index: list(occurrences.item(index).transform2.asArray())
        for index in range(occurrences.count)
    }
    temporary = adsk.fusion.TemporaryBRepManager.get()
    rev_a_body = occurrences.item(REV_A_INDEX).bRepBodies.item(0)
    target = temporary.copy(rev_a_body)
    web = make_rear_web(temporary)
    web_volume_mm3 = web.volume * 1000.0
    engagement = {
        "rev_a_mm3": intersection_volume_mm3(temporary, web, rev_a_body),
        "manufacturer_j17a_region_mm3": intersection_volume_mm3(
            temporary, web, occurrences.item(J17A_INDEX).bRepBodies.item(0)
        ),
        "manufacturer_j20a_region_mm3": intersection_volume_mm3(
            temporary, web, occurrences.item(J20A_INDEX).bRepBodies.item(0)
        ),
    }
    rev_a_volume_mm3 = target.volume * 1000.0
    if not temporary.booleanOperation(
        target, web, adsk.fusion.BooleanTypes.UnionBooleanType
    ):
        raise RuntimeError("Could not union the rear web into Rev A")
    if not target.isSolid or target.lumps.count != 1 or target.shells.count != 1:
        raise RuntimeError("Rev B temporary result is not one closed solid")

    candidate_occurrence = occurrences.addNewComponent(adsk.core.Matrix3D.create())
    candidate_component = candidate_occurrence.component
    candidate_component.name = COMPONENT_NAME
    base_feature = candidate_component.features.baseFeatures.add()
    base_feature.name = "REV_A_SOURCE_COPY_PLUS_CONTINUOUS_REAR_WEB"
    base_feature.startEdit()
    candidate_body = candidate_component.bRepBodies.add(target, base_feature)
    if candidate_body is None:
        raise RuntimeError("Could not add the Rev B B-rep")
    source_appearance = occurrences.item(REV_A_INDEX).bRepBodies.item(0).appearance
    if source_appearance is not None:
        candidate_body.appearance = source_appearance
    base_feature.finishEdit()
    candidate_body = candidate_component.bRepBodies.item(0)
    candidate_body.name = BODY_NAME
    if candidate_body.name != BODY_NAME:
        raise RuntimeError("Could not persist the Rev B body name")

    # Timeline additions can reset external occurrence poses unless restored.
    for index, values in original_transforms.items():
        occurrences.item(index).transform2 = matrix_from_values(values)

    web_contract = {
        "intent": "join the two former rear M4 connection regions as one FDM web",
        "x_span_mm": (REAR_RIGHT_X_CM - REAR_LEFT_X_CM) * 10.0,
        "depth_mm": (WEB_REAR_Y_CM - WEB_FRONT_Y_CM) * 10.0,
        "thickness_mm": WEB_THICKNESS_CM * 10.0,
        "top_z_cm": WEB_TOP_Z_CM,
        "bottom_z_cm": WEB_TOP_Z_CM - WEB_THICKNESS_CM,
        "raw_volume_mm3": web_volume_mm3,
        "engagement": engagement,
    }
    candidate_component.attributes.add(
        "hardware_evidence", "classification", "print_adaptation"
    )
    candidate_component.attributes.add(
        "hardware_evidence", "official_cad", "false"
    )
    candidate_component.attributes.add(
        "hardware_evidence", "parent_component", REV_A_COMPONENT_NAME
    )
    candidate_component.attributes.add(
        "hardware_evidence", "rear_web_contract", json.dumps(web_contract)
    )
    candidate_component.attributes.add(
        "hardware_evidence",
        "claim_boundary",
        "One-piece FDM geometry candidate only; material, print orientation, strength, fatigue, torque, vibration, cable routing, and real-hardware safety are unvalidated",
    )

    occurrences.item(REV_A_INDEX).isLightBulbOn = False
    set_final_state_attributes(occurrences.item(REV_A_INDEX), False)
    for index in (J17A_INDEX, J20A_INDEX):
        occurrences.item(index).isLightBulbOn = False
        set_final_state_attributes(occurrences.item(index), False)
    for index in REJECTED_LAYER_HARDWARE_INDICES:
        occurrences.item(index).isLightBulbOn = False
        set_final_state_attributes(occurrences.item(index), False)
    candidate_occurrence.isLightBulbOn = True
    set_final_state_attributes(candidate_occurrence, True)
    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()

    step_options = design.exportManager.createSTEPExportOptions(
        CANDIDATE_STEP, candidate_component
    )
    if step_options is None or not design.exportManager.execute(step_options):
        raise RuntimeError("Could not export the Rev B candidate STEP")

    maximum_source_transform_difference = 0.0
    for index, expected in original_transforms.items():
        actual = list(occurrences.item(index).transform2.asArray())
        maximum_source_transform_difference = max(
            maximum_source_transform_difference,
            max(abs(actual[item] - expected[item]) for item in range(16)),
        )

    body = candidate_component.bRepBodies.item(0)
    bounds = body.boundingBox
    report = {
        "stage": "experiment_and_analysis",
        "status": "awaiting_visual_review",
        "document": application.activeDocument.name,
        "parent_occurrence_count": SOURCE_OCCURRENCE_COUNT,
        "candidate_occurrence_index": occurrences.count - 1,
        "final_occurrence_count": occurrences.count,
        "component": COMPONENT_NAME,
        "body": body.name,
        "classification": "print_adaptation",
        "official_cad": False,
        "parent_component": REV_A_COMPONENT_NAME,
        "rear_web": web_contract,
        "candidate_metrics": {
            "brep_body_count": candidate_component.bRepBodies.count,
            "mesh_body_count": candidate_component.meshBodies.count,
            "is_solid": body.isSolid,
            "lump_count": body.lumps.count,
            "shell_count": body.shells.count,
            "face_count": body.faces.count,
            "volume_mm3": body.volume * 1000.0,
            "added_net_volume_mm3": body.volume * 1000.0 - rev_a_volume_mm3,
            "bounds_cm": {
                "min": [
                    bounds.minPoint.x,
                    bounds.minPoint.y,
                    bounds.minPoint.z,
                ],
                "max": [
                    bounds.maxPoint.x,
                    bounds.maxPoint.y,
                    bounds.maxPoint.z,
                ],
            },
        },
        "preservation": {
            "rev_a_unchanged_and_hidden": True,
            "manufacturer_sources_unchanged_and_hidden": True,
            "maximum_parent_transform_difference": maximum_source_transform_difference,
            "frozen_parent_f3d": PARENT_F3D,
            "candidate_step": CANDIDATE_STEP,
            "pending_snapshot": design.snapshots.hasPendingSnapshot,
        },
        "claim_boundary": (
            "One-piece FDM geometry and packaging candidate only; material, "
            "print orientation, strength, fatigue, torque, vibration, cable "
            "routing, fabrication tolerance, and real-hardware safety remain unvalidated."
        ),
    }
    with open(BUILD_REPORT, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
