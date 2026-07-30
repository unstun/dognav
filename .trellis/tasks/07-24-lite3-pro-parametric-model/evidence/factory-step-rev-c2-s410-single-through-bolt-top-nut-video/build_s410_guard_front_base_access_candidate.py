"""Create a reversible S410 guard candidate with two Lite3 screw-access holes."""

import adsk.core
import adsk.fusion
import json
import os


OUTPUT_ROOT = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-rev-c2-s410-single-through-bolt-top-nut-video"
)
BUILD_REPORT = os.path.join(
    OUTPUT_ROOT,
    "s410_guard_front_base_full_depth_access_candidate_build.json",
)
CANDIDATE_STEP = os.path.join(
    OUTPUT_ROOT,
    "s410-guard-front-base-2x-m3-full-depth-access-holes-7mm-visual-candidate.step",
)

COMPONENT_NAME = (
    "S410_GUARD_FRONT_BASE_2X_M3_FULL_DEPTH_ACCESS_HOLES_7MM_"
    "VISUAL_PRINT_CANDIDATE_NOT_OFFICIAL_CAD"
)
BODY_NAME = "S410_GUARD_WITH_FRONT_BASE_2X_7MM_FULL_DEPTH_TOOL_ACCESS"
OFFICIAL_GUARD_INDEX = 3
ACCESS_AXES = (
    (-33.697009644681465, 260.68489005808055),
    (-27.197009644681465, 260.68489005808055),
)
ACCESS_DIAMETER_CM = 0.70
ACCESS_START_Y_CM = 17.0
ACCESS_END_Y_CM = 31.0

ATTRIBUTE_GROUP = "codex_full_installation_animation"
FINAL_TRANSFORM_ATTRIBUTE = "final_transform"
FINAL_VISIBILITY_ATTRIBUTE = "final_visibility"


def replace_attribute(entity, group, name, value):
    existing = entity.attributes.itemByName(group, name)
    if existing is not None:
        existing.deleteMe()
    entity.attributes.add(group, name, value)


def set_final_state(occurrence, visible):
    replace_attribute(
        occurrence,
        ATTRIBUTE_GROUP,
        FINAL_TRANSFORM_ATTRIBUTE,
        json.dumps(list(occurrence.transform2.asArray())),
    )
    replace_attribute(
        occurrence,
        ATTRIBUTE_GROUP,
        FINAL_VISIBILITY_ATTRIBUTE,
        "true" if visible else "false",
    )


def world_body_copy(temporary, occurrence):
    body = temporary.copy(occurrence.component.bRepBodies.item(0))
    if not temporary.transform(body, occurrence.transform2):
        raise RuntimeError("Could not place the official guard body in world space")
    return body


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences
    os.makedirs(OUTPUT_ROOT, exist_ok=True)

    official_guard = occurrences.item(OFFICIAL_GUARD_INDEX)
    if "S410" not in official_guard.component.name:
        raise RuntimeError("Root occurrence 3 is not the official S410 guard")
    for index in range(occurrences.count):
        occurrence = occurrences.item(index)
        if occurrence.component.name == COMPONENT_NAME:
            for candidate_index in range(occurrences.count):
                other = occurrences.item(candidate_index)
                if other.component.name.startswith("S410_GUARD_FRONT_BASE_"):
                    other.isLightBulbOn = other == occurrence
                    set_final_state(other, other == occurrence)
            official_guard.isLightBulbOn = False
            occurrence.isLightBulbOn = True
            set_final_state(official_guard, False)
            set_final_state(occurrence, True)
            print(
                json.dumps(
                    {
                        "status": "existing",
                        "candidate_index": index,
                        "component": COMPONENT_NAME,
                    },
                    ensure_ascii=False,
                )
            )
            return

    temporary = adsk.fusion.TemporaryBRepManager.get()
    candidate = world_body_copy(temporary, official_guard)
    source_volume_mm3 = candidate.volume * 1000.0
    access_rows = []
    for axis_index, (x_value, z_value) in enumerate(ACCESS_AXES):
        start = adsk.core.Point3D.create(x_value, ACCESS_START_Y_CM, z_value)
        end = adsk.core.Point3D.create(x_value, ACCESS_END_Y_CM, z_value)
        cutter = temporary.createCylinderOrCone(
            start,
            ACCESS_DIAMETER_CM * 0.5,
            end,
            ACCESS_DIAMETER_CM * 0.5,
        )
        if cutter is None:
            raise RuntimeError("Could not create S410 access cutter")
        before_mm3 = candidate.volume * 1000.0
        if not temporary.booleanOperation(
            candidate,
            cutter,
            adsk.fusion.BooleanTypes.DifferenceBooleanType,
        ):
            raise RuntimeError("Could not cut S410 front base-screw access hole")
        after_mm3 = candidate.volume * 1000.0
        access_rows.append(
            {
                "axis_index": axis_index,
                "center_xz_cm": [x_value, z_value],
                "diameter_mm": ACCESS_DIAMETER_CM * 10.0,
                "removed_volume_mm3": before_mm3 - after_mm3,
            }
        )
    if not candidate.isSolid or candidate.lumps.count != 1:
        raise RuntimeError("The access-hole guard candidate is not one solid")

    candidate_occurrence = occurrences.addNewComponent(adsk.core.Matrix3D.create())
    candidate_component = candidate_occurrence.component
    candidate_component.name = COMPONENT_NAME
    base_feature = candidate_component.features.baseFeatures.add()
    base_feature.name = "OFFICIAL_S410_COPY_MINUS_2X_FRONT_BASE_ACCESS_HOLES"
    base_feature.startEdit()
    candidate_body = candidate_component.bRepBodies.add(candidate, base_feature)
    if candidate_body is None:
        raise RuntimeError("Could not add the S410 access-hole candidate body")
    source_appearance = official_guard.bRepBodies.item(0).appearance
    if source_appearance is not None:
        candidate_body.appearance = source_appearance
    base_feature.finishEdit()
    candidate_body = candidate_component.bRepBodies.item(0)
    candidate_body.name = BODY_NAME

    candidate_component.attributes.add(
        "hardware_evidence",
        "classification",
        "print_adaptation",
    )
    candidate_component.attributes.add(
        "hardware_evidence",
        "official_cad",
        "false",
    )
    candidate_component.attributes.add(
        "hardware_evidence",
        "claim_boundary",
        (
            "Two 7 mm front Lite3 base-screw access holes only; printability, "
            "strength, fatigue, torque, vibration, and real-hardware safety are unvalidated"
        ),
    )
    official_guard.isLightBulbOn = False
    for index in range(occurrences.count - 1):
        occurrence = occurrences.item(index)
        if occurrence.component.name.startswith("S410_GUARD_FRONT_BASE_"):
            occurrence.isLightBulbOn = False
            set_final_state(occurrence, False)
    candidate_occurrence.isLightBulbOn = True
    set_final_state(official_guard, False)
    set_final_state(candidate_occurrence, True)

    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()
    options = design.exportManager.createSTEPExportOptions(
        CANDIDATE_STEP,
        candidate_component,
    )
    if options is None or not design.exportManager.execute(options):
        raise RuntimeError("Could not export the S410 access-hole candidate STEP")

    report = {
        "stage": "experiment_and_analysis",
        "status": "awaiting_visual_review",
        "document": application.activeDocument.name,
        "candidate_index": occurrences.count - 1,
        "component": COMPONENT_NAME,
        "body": BODY_NAME,
        "official_source_preserved_and_hidden": True,
        "official_cad": False,
        "access_holes": access_rows,
        "source_volume_mm3": source_volume_mm3,
        "candidate_volume_mm3": candidate_body.volume * 1000.0,
        "removed_volume_mm3": (
            source_volume_mm3 - candidate_body.volume * 1000.0
        ),
        "candidate_step": CANDIDATE_STEP,
        "claim_boundary": (
            "Geometry and visual tool access only; printability, strength, "
            "fatigue, torque, vibration, and real-hardware safety remain unvalidated."
        ),
    }
    with open(BUILD_REPORT, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False))
