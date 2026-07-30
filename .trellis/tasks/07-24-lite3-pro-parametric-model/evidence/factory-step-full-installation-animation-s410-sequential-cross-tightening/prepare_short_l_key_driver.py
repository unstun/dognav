"""Replace the long T-driver with a short right-angle L-key visual aid."""

import adsk.core
import adsk.fusion
import json

globals().pop("run", None)


REJECTED_TOOL_NAME = "S410_M5_EXTERNAL_T_DRIVER_ANIMATION_TOOL"
TOOL_COMPONENT_NAME = "S410_M5_SHORT_L_KEY_ANIMATION_TOOL"
TRANSFORM_ATTRIBUTE_GROUP = "codex_full_installation_animation"
FINAL_TRANSFORM_ATTRIBUTE = "final_transform"
FINAL_VISIBILITY_ATTRIBUTE = "final_visibility"
MID360_NORMAL = (0.0, 0.9659258262890683, 0.25881904510252074)


def shifted(point, vector, distance):
    return adsk.core.Point3D.create(
        point.x + vector.x * distance,
        point.y + vector.y * distance,
        point.z + vector.z * distance,
    )


def replace_attribute(entity, group, name, value):
    old = entity.attributes.itemByName(group, name)
    if old is not None:
        old.deleteMe()
    entity.attributes.add(group, name, value)


def set_final_state(occurrence, visible):
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


def run(context):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences
    rejected = None
    existing = None
    existing_index = None
    for index in range(occurrences.count):
        occurrence = occurrences.item(index)
        if occurrence.component.name == REJECTED_TOOL_NAME:
            rejected = occurrence
        if occurrence.component.name == TOOL_COMPONENT_NAME:
            existing = occurrence
            existing_index = index

    if rejected is None:
        raise RuntimeError("Rejected T-driver occurrence missing")
    rejected.isLightBulbOn = False
    set_final_state(rejected, False)

    if existing is not None:
        existing.isLightBulbOn = False
        set_final_state(existing, False)
        if design.snapshots.hasPendingSnapshot:
            design.snapshots.add()
        print(
            json.dumps(
                {
                    "status": "already_present",
                    "tool_index": existing_index,
                    "root_occurrence_count": occurrences.count,
                    "pending_snapshot": design.snapshots.hasPendingSnapshot,
                }
            )
        )
        return

    if occurrences.count != 33:
        raise RuntimeError(
            "Expected 33-occurrence T-driver scene, found "
            + str(occurrences.count)
        )

    normal = adsk.core.Vector3D.create(*MID360_NORMAL)
    normal.normalize()
    origin = adsk.core.Point3D.create(0.0, 0.0, 0.0)
    bend = shifted(origin, normal, 1.2)
    bit_start = shifted(origin, normal, 0.52)
    handle_end = adsk.core.Point3D.create(
        bend.x + 4.0,
        bend.y,
        bend.z,
    )

    occurrence = occurrences.addNewComponent(adsk.core.Matrix3D.create())
    component = occurrence.component
    component.name = TOOL_COMPONENT_NAME
    feature = component.features.baseFeatures.add()
    feature.name = "SHORT_L_KEY_VISUAL_BREP"
    feature.startEdit()
    temporary = adsk.fusion.TemporaryBRepManager.get()
    bit = component.bRepBodies.add(
        temporary.createCylinderOrCone(bit_start, 0.16, bend, 0.16),
        feature,
    )
    handle = component.bRepBodies.add(
        temporary.createCylinderOrCone(bend, 0.16, handle_end, 0.16),
        feature,
    )
    bit.name = "SHORT_L_KEY_BIT_VISUAL"
    handle.name = "SHORT_L_KEY_HANDLE_VISUAL"
    appearance = None
    if occurrences.item(7).component.bRepBodies.count:
        appearance = occurrences.item(7).component.bRepBodies.item(0).appearance
    if appearance is not None:
        bit.appearance = appearance
        handle.appearance = appearance
    feature.finishEdit()
    component.attributes.add(
        "s410_sequential_fastener",
        "claim_boundary",
        "Animation-only short L-key; not supplied-tool evidence",
    )
    occurrence.isLightBulbOn = False
    set_final_state(occurrence, False)
    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()

    print(
        json.dumps(
            {
                "status": "created",
                "tool_index": occurrences.count - 1,
                "root_occurrence_count": occurrences.count,
                "bit_diameter_mm": 3.2,
                "straight_engagement_mm": 6.8,
                "handle_length_mm": 40.0,
                "pending_snapshot": design.snapshots.hasPendingSnapshot,
            }
        )
    )
