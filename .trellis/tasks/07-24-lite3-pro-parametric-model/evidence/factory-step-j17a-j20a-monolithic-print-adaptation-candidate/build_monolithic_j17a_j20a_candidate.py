"""Build a reversible one-piece J17A/J20A print-adaptation candidate.

The manufacturer J17A and J20A occurrences remain unchanged and are hidden,
not overwritten. Their current world-space B-reps are copied into a new
derived component. Four internal fusion groups occupy the former two M3 and
two M4 layer-fastener axes, producing one closed solid while preserving the
external J17A/J20A pose, D435i interface, MID360 mounting pattern, and S410
M5 interface.

This is explicitly a user-requested print adaptation, not official CAD and
not a fabrication or structural-safety release.
"""

import adsk.core
import adsk.fusion
import json
import os


globals().pop("run", None)


EVIDENCE_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-j17a-j20a-monolithic-print-adaptation-candidate"
)
PRE_CHANGE_F3D = os.path.join(
    EVIDENCE_DIR, "pre-monolithic-34-occurrence-scene-backup.f3d"
)
CANDIDATE_STEP = os.path.join(
    EVIDENCE_DIR, "j17a-j20a-monolithic-print-adaptation-rev-a.step"
)
BUILD_REPORT = os.path.join(EVIDENCE_DIR, "build_report.json")

COMPONENT_NAME = (
    "J17A_J20A_MONOLITHIC_PRINT_ADAPTATION_REV_A_NOT_OFFICIAL_CAD"
)
BODY_NAME = "J17A_J20A_MONOLITHIC_ONE_SOLID_REV_A"

TRANSFORM_ATTRIBUTE_GROUP = "codex_full_installation_animation"
FINAL_TRANSFORM_ATTRIBUTE = "final_transform"
FINAL_VISIBILITY_ATTRIBUTE = "final_visibility"

J17A_INDEX = 1
J20A_INDEX = 2
SOURCE_OCCURRENCE_COUNT = 34
REJECTED_LAYER_HARDWARE_INDICES = (7, 8, 9, 10, 18, 19, 20, 21, 22, 23)

FRONT_AXES = (
    (-32.24700964468146, 20.468141858307484, 259.73489005808057),
    (-28.647009644681464, 20.468141858307484, 259.73489005808057),
)
REAR_AXES = (
    (-33.84112221937691, 22.018141858307482, 251.89077750838507),
    (-27.05289706998607, 22.018141858307482, 251.89077750838507),
)


def point(values):
    return adsk.core.Point3D.create(*values)


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


def union(temporary, target, tool, label):
    if not temporary.booleanOperation(
        target, tool, adsk.fusion.BooleanTypes.UnionBooleanType
    ):
        raise RuntimeError("Temporary B-rep union failed: " + label)


def add_front_fusion_group(temporary, target, axis, sequence):
    x, start_y, z = axis
    core_end_y = 21.20163550736137
    cap_end_y = 20.718141858307484
    core = temporary.createCylinderOrCone(
        point((x, start_y, z)), 0.25, point((x, core_end_y, z)), 0.25
    )
    cap = temporary.createCylinderOrCone(
        point((x, start_y, z)), 0.35, point((x, cap_end_y, z)), 0.35
    )
    union(temporary, target, core, "front_core_%d" % sequence)
    union(temporary, target, cap, "front_cap_%d" % sequence)
    return {
        "group": "former_front_m3_axis_%d" % sequence,
        "axis_cm": list(axis),
        "core_diameter_mm": 5.0,
        "cap_diameter_mm": 7.0,
        "source_role_replaced": "J17A clearance to J20A M3 thread",
    }


def add_rear_fusion_group(temporary, target, axis, sequence):
    x, shoulder_y, z = axis
    core_end_y = 23.218141858307483
    outer_face_y = 20.468141858307484
    core = temporary.createCylinderOrCone(
        point((x, shoulder_y, z)), 0.34, point((x, core_end_y, z)), 0.34
    )
    cap = temporary.createCylinderOrCone(
        point((x, outer_face_y, z)), 0.40, point((x, shoulder_y, z)), 0.40
    )
    union(temporary, target, core, "rear_core_%d" % sequence)
    union(temporary, target, cap, "rear_cap_%d" % sequence)
    return {
        "group": "former_rear_m4_axis_%d" % sequence,
        "axis_cm": list(axis),
        "core_diameter_mm": 6.8,
        "cap_diameter_mm": 8.0,
        "source_role_replaced": "J17A counterbore/clearance to J20A M4 thread",
    }


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences
    os.makedirs(EVIDENCE_DIR, exist_ok=True)

    existing = []
    for index in range(occurrences.count):
        occurrence = occurrences.item(index)
        if occurrence.component.name == COMPONENT_NAME:
            existing.append((index, occurrence))
    if existing:
        raise RuntimeError(
            "Monolithic candidate already exists at occurrence index "
            + str(existing[0][0])
        )
    if occurrences.count != SOURCE_OCCURRENCE_COUNT:
        raise RuntimeError(
            "Expected reviewed 34-occurrence scene, found "
            + str(occurrences.count)
        )
    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()

    source_names = {
        "j17a": occurrences.item(J17A_INDEX).component.name,
        "j20a": occurrences.item(J20A_INDEX).component.name,
    }
    if not source_names["j17a"].startswith(
        "J17A_ORIGINAL_MANUFACTURER_BREP_CORRECT_UPPER_65MM_PAIR"
    ):
        raise RuntimeError("Unexpected J17A source component")
    if not source_names["j20a"].startswith("1T21-J20A-"):
        raise RuntimeError("Unexpected J20A source component")
    if (
        occurrences.item(J17A_INDEX).bRepBodies.count != 1
        or occurrences.item(J20A_INDEX).bRepBodies.count != 1
    ):
        raise RuntimeError("Expected one assembly-context B-rep for each source bracket")

    original_transforms = {
        index: list(occurrences.item(index).transform2.asArray())
        for index in range(occurrences.count)
    }
    export_manager = design.exportManager
    if not os.path.exists(PRE_CHANGE_F3D):
        backup_options = export_manager.createFusionArchiveExportOptions(
            PRE_CHANGE_F3D, root
        )
        if backup_options is None or not export_manager.execute(backup_options):
            raise RuntimeError("Could not export the pre-change Fusion archive")

    temporary = adsk.fusion.TemporaryBRepManager.get()
    target = temporary.copy(occurrences.item(J17A_INDEX).bRepBodies.item(0))
    j20_copy = temporary.copy(occurrences.item(J20A_INDEX).bRepBodies.item(0))
    source_metrics = {
        "j17a_volume_mm3": target.volume * 1000.0,
        "j20a_volume_mm3": j20_copy.volume * 1000.0,
    }

    fusion_groups = []
    for sequence, axis in enumerate(FRONT_AXES, start=1):
        fusion_groups.append(
            add_front_fusion_group(temporary, target, axis, sequence)
        )
    for sequence, axis in enumerate(REAR_AXES, start=1):
        fusion_groups.append(
            add_rear_fusion_group(temporary, target, axis, sequence)
        )
    union(temporary, target, j20_copy, "manufacturer_j20a_source_body")
    if not target.isSolid or target.lumps.count != 1 or target.shells.count != 1:
        raise RuntimeError("Monolithic temporary body is not one closed solid")

    candidate_occurrence = occurrences.addNewComponent(adsk.core.Matrix3D.create())
    candidate_component = candidate_occurrence.component
    candidate_component.name = COMPONENT_NAME
    base_feature = candidate_component.features.baseFeatures.add()
    base_feature.name = "MONOLITHIC_SOURCE_COPY_AND_INTERNAL_FUSION_GROUPS"
    base_feature.startEdit()
    candidate_body = candidate_component.bRepBodies.add(target, base_feature)
    if candidate_body is None:
        raise RuntimeError("Could not add the monolithic B-rep to the component")
    candidate_body.name = BODY_NAME
    source_appearance = occurrences.item(J17A_INDEX).bRepBodies.item(0).appearance
    if source_appearance is not None:
        candidate_body.appearance = source_appearance
    base_feature.finishEdit()
    # Fusion can reset a body name when the direct/base feature edit finishes.
    candidate_body = candidate_component.bRepBodies.item(0)
    candidate_body.name = BODY_NAME
    if candidate_body.name != BODY_NAME:
        raise RuntimeError("Could not persist the monolithic candidate body name")

    # Adding timeline geometry must not reset the reviewed occurrence poses.
    for index, values in original_transforms.items():
        occurrences.item(index).transform2 = matrix_from_values(values)

    candidate_component.attributes.add(
        "hardware_evidence", "classification", "print_adaptation"
    )
    candidate_component.attributes.add(
        "hardware_evidence", "official_cad", "false"
    )
    candidate_component.attributes.add(
        "hardware_evidence", "source_components", json.dumps(source_names)
    )
    candidate_component.attributes.add(
        "hardware_evidence", "fusion_groups", json.dumps(fusion_groups)
    )
    candidate_component.attributes.add(
        "hardware_evidence",
        "claim_boundary",
        "One-piece geometry candidate only; material, strength, fatigue, torque, vibration, and fabrication safety are unvalidated",
    )

    occurrences.item(J17A_INDEX).isLightBulbOn = False
    occurrences.item(J20A_INDEX).isLightBulbOn = False
    set_final_state_attributes(occurrences.item(J17A_INDEX), False)
    set_final_state_attributes(occurrences.item(J20A_INDEX), False)
    for index in REJECTED_LAYER_HARDWARE_INDICES:
        occurrences.item(index).isLightBulbOn = False
        set_final_state_attributes(occurrences.item(index), False)
    candidate_occurrence.isLightBulbOn = True
    set_final_state_attributes(candidate_occurrence, True)
    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()

    step_options = export_manager.createSTEPExportOptions(
        CANDIDATE_STEP, candidate_component
    )
    if step_options is None or not export_manager.execute(step_options):
        raise RuntimeError("Could not export the monolithic candidate STEP")

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
        "source_occurrence_count": SOURCE_OCCURRENCE_COUNT,
        "candidate_occurrence_index": occurrences.count - 1,
        "final_occurrence_count": occurrences.count,
        "component": COMPONENT_NAME,
        "body": BODY_NAME,
        "classification": "print_adaptation",
        "official_cad": False,
        "source_components": source_names,
        "source_metrics": source_metrics,
        "fusion_groups": fusion_groups,
        "candidate_metrics": {
            "brep_body_count": candidate_component.bRepBodies.count,
            "mesh_body_count": candidate_component.meshBodies.count,
            "is_solid": body.isSolid,
            "lump_count": body.lumps.count,
            "shell_count": body.shells.count,
            "face_count": body.faces.count,
            "volume_mm3": body.volume * 1000.0,
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
            "manufacturer_sources_unchanged": True,
            "manufacturer_sources_hidden": True,
            "maximum_source_transform_difference": maximum_source_transform_difference,
            "pre_change_f3d": PRE_CHANGE_F3D,
            "candidate_step": CANDIDATE_STEP,
            "pending_snapshot": bool(design.snapshots.hasPendingSnapshot),
        },
        "claim_boundary": (
            "One-piece B-rep and access-preserving geometry candidate only; "
            "material, print orientation, strength, fatigue, torque, vibration, "
            "and real-hardware safety remain unvalidated."
        ),
    }
    with open(BUILD_REPORT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps(report, ensure_ascii=False))
