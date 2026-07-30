"""Replace the rejected grouped S410 screws with four independent references.

The official S410 and J20 BReps remain unchanged. The four M5x8 screw solids
and the T-driver are explicitly visual candidates because the public drawings
establish the 5.2 mm clearance / M5 receiver relationship but not the supplied
screw length, head standard, tool, torque, or engagement.
"""

import adsk.core
import adsk.fusion
import json

globals().pop("run", None)


OLD_GROUP_NAME = "S410_TO_J20_4X_M5X8_SOCKET_HEAD_SCREWS_VISUAL_CANDIDATE"
SCREW_COMPONENT_NAME = "S410_TO_J20_M5X8_INDIVIDUAL_SCREW_VISUAL_CANDIDATE"
TOOL_COMPONENT_NAME = "S410_M5_EXTERNAL_T_DRIVER_ANIMATION_TOOL"

TRANSFORM_ATTRIBUTE_GROUP = "codex_full_installation_animation"
FINAL_TRANSFORM_ATTRIBUTE = "final_transform"
FINAL_VISIBILITY_ATTRIBUTE = "final_visibility"

MID360_NORMAL = (0.0, 0.9659258262890683, 0.25881904510252074)
POSITION_FACES = (
    ("S1_TOP_LEFT", 5, 5, 1),
    ("S2_TOP_RIGHT", 7, 6, 3),
    ("S3_BOTTOM_LEFT", 6, 7, 4),
    ("S4_BOTTOM_RIGHT", 8, 8, 2),
)


def shifted(point, vector, distance):
    return adsk.core.Point3D.create(
        point.x + vector.x * distance,
        point.y + vector.y * distance,
        point.z + vector.z * distance,
    )


def translation_matrix(point):
    matrix = adsk.core.Matrix3D.create()
    matrix.translation = adsk.core.Vector3D.create(point.x, point.y, point.z)
    return matrix


def replace_attribute(entity, group, name, value):
    old = entity.attributes.itemByName(group, name)
    if old is not None:
        old.deleteMe()
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


def guard_outer_centres(guard):
    normal = adsk.core.Vector3D.create(*MID360_NORMAL)
    normal.normalize()
    transform = guard.transform2
    body = guard.component.bRepBodies.item(0)
    centres = {}

    for position, guard_face, j20_face, tightening_order in POSITION_FACES:
        face = body.faces.item(guard_face)
        cylinder = adsk.core.Cylinder.cast(face.geometry)
        if cylinder is None or abs(cylinder.radius - 0.26) > 1.0e-6:
            raise RuntimeError(
                "Unexpected S410 clearance face " + str(guard_face)
            )
        centre = cylinder.origin.copy()
        centre.transformBy(transform)
        centre_projection = (
            centre.x * normal.x
            + centre.y * normal.y
            + centre.z * normal.z
        )
        projections = []
        for edge_index in range(face.edges.count):
            edge = face.edges.item(edge_index)
            for vertex in (edge.startVertex, edge.endVertex):
                if vertex is None:
                    continue
                point = vertex.geometry.copy()
                point.transformBy(transform)
                projections.append(
                    point.x * normal.x
                    + point.y * normal.y
                    + point.z * normal.z
                )
        outer_projection = max(projections)
        outer_centre = shifted(
            centre, normal, outer_projection - centre_projection
        )
        centres[position] = {
            "point": outer_centre,
            "guard_face": guard_face,
            "j20_face": j20_face,
            "tightening_order": tightening_order,
        }

    return centres


def apply_body_appearance(body, appearance):
    if appearance is not None:
        body.appearance = appearance


def run(context):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences

    old_group = None
    new_screws = []
    driver = None
    for index in range(occurrences.count):
        occurrence = occurrences.item(index)
        if occurrence.component.name == OLD_GROUP_NAME:
            old_group = occurrence
        elif occurrence.component.name == SCREW_COMPONENT_NAME:
            new_screws.append((index, occurrence))
        elif occurrence.component.name == TOOL_COMPONENT_NAME:
            driver = (index, occurrence)

    if old_group is None:
        raise RuntimeError("Rejected grouped S410 fastener occurrence missing")

    old_group.isLightBulbOn = False
    set_final_state_attributes(old_group, False)

    if len(new_screws) == 4 and driver is not None:
        for _, occurrence in new_screws:
            occurrence.isLightBulbOn = True
            set_final_state_attributes(occurrence, True)
        driver[1].isLightBulbOn = False
        set_final_state_attributes(driver[1], False)
        if design.snapshots.hasPendingSnapshot:
            design.snapshots.add()
        print(
            json.dumps(
                {
                    "status": "already_present",
                    "root_occurrence_count": occurrences.count,
                    "screw_indices": [item[0] for item in new_screws],
                    "tool_index": driver[0],
                    "old_group_hidden": True,
                    "pending_snapshot": design.snapshots.hasPendingSnapshot,
                }
            )
        )
        return

    if occurrences.count != 28:
        raise RuntimeError(
            "Expected reviewed 28-occurrence source, found "
            + str(occurrences.count)
        )
    if new_screws or driver is not None:
        raise RuntimeError("Partial sequential fastener revision detected")

    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()

    guard = occurrences.item(3)
    if "S410" not in guard.name:
        raise RuntimeError("Occurrence 3 is not the official S410 guard")
    centres = guard_outer_centres(guard)
    normal = adsk.core.Vector3D.create(*MID360_NORMAL)
    normal.normalize()

    screw_appearance = None
    if occurrences.item(18).component.bRepBodies.count:
        screw_appearance = (
            occurrences.item(18).component.bRepBodies.item(0).appearance
        )
    tool_appearance = None
    if occurrences.item(7).component.bRepBodies.count:
        tool_appearance = (
            occurrences.item(7).component.bRepBodies.item(0).appearance
        )

    first_position = POSITION_FACES[0][0]
    first_occurrence = occurrences.addNewComponent(
        translation_matrix(centres[first_position]["point"])
    )
    screw_component = first_occurrence.component
    screw_component.name = SCREW_COMPONENT_NAME
    base_feature = screw_component.features.baseFeatures.add()
    base_feature.name = "M5X8_VISUAL_BREP"
    base_feature.startEdit()

    origin = adsk.core.Point3D.create(0.0, 0.0, 0.0)
    shaft_end = shifted(origin, normal, -0.8)
    head_top = shifted(origin, normal, 0.5)
    temporary = adsk.fusion.TemporaryBRepManager.get()
    shaft = screw_component.bRepBodies.add(
        temporary.createCylinderOrCone(origin, 0.25, shaft_end, 0.25),
        base_feature,
    )
    head = screw_component.bRepBodies.add(
        temporary.createCylinderOrCone(origin, 0.425, head_top, 0.425),
        base_feature,
    )
    shaft.name = "M5X8_SHAFT_VISUAL_CANDIDATE"
    head.name = "M5_SOCKET_HEAD_VISUAL_CANDIDATE"
    apply_body_appearance(shaft, screw_appearance)
    apply_body_appearance(head, screw_appearance)
    base_feature.finishEdit()

    screw_occurrences = [first_occurrence]
    for position, _, _, _ in POSITION_FACES[1:]:
        screw_occurrences.append(
            occurrences.addExistingComponent(
                screw_component,
                translation_matrix(centres[position]["point"]),
            )
        )

    for occurrence, entry in zip(screw_occurrences, POSITION_FACES):
        position, guard_face, j20_face, tightening_order = entry
        occurrence.isLightBulbOn = True
        occurrence.attributes.add(
            "s410_sequential_fastener", "position", position
        )
        occurrence.attributes.add(
            "s410_sequential_fastener", "guard_face", str(guard_face)
        )
        occurrence.attributes.add(
            "s410_sequential_fastener", "j20_face", str(j20_face)
        )
        occurrence.attributes.add(
            "s410_sequential_fastener",
            "tightening_order",
            str(tightening_order),
        )
        set_final_state_attributes(occurrence, True)

    tool_occurrence = occurrences.addNewComponent(adsk.core.Matrix3D.create())
    tool_component = tool_occurrence.component
    tool_component.name = TOOL_COMPONENT_NAME
    tool_feature = tool_component.features.baseFeatures.add()
    tool_feature.name = "T_DRIVER_VISUAL_BREP"
    tool_feature.startEdit()

    bit_start = shifted(origin, normal, 0.52)
    handle_centre = shifted(origin, normal, 10.0)
    bit = tool_component.bRepBodies.add(
        temporary.createCylinderOrCone(
            bit_start, 0.20, handle_centre, 0.20
        ),
        tool_feature,
    )
    handle_start = adsk.core.Point3D.create(
        handle_centre.x - 2.5,
        handle_centre.y,
        handle_centre.z,
    )
    handle_end = adsk.core.Point3D.create(
        handle_centre.x + 2.5,
        handle_centre.y,
        handle_centre.z,
    )
    handle = tool_component.bRepBodies.add(
        temporary.createCylinderOrCone(
            handle_start, 0.30, handle_end, 0.30
        ),
        tool_feature,
    )
    bit.name = "M5_T_DRIVER_BIT_VISUAL"
    handle.name = "M5_T_DRIVER_HANDLE_VISUAL"
    apply_body_appearance(bit, tool_appearance)
    apply_body_appearance(handle, tool_appearance)
    tool_feature.finishEdit()

    tool_component.attributes.add(
        "s410_sequential_fastener",
        "claim_boundary",
        "Animation-only external driver; not supplied-tool evidence",
    )
    tool_occurrence.isLightBulbOn = False
    set_final_state_attributes(tool_occurrence, False)

    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()

    print(
        json.dumps(
            {
                "status": "created",
                "root_occurrence_count": occurrences.count,
                "screw_indices": list(
                    range(occurrences.count - 5, occurrences.count - 1)
                ),
                "tool_index": occurrences.count - 1,
                "old_group_hidden": True,
                "positions": {
                    position: {
                        "point_cm": [
                            data["point"].x,
                            data["point"].y,
                            data["point"].z,
                        ],
                        "guard_face": data["guard_face"],
                        "j20_face": data["j20_face"],
                        "tightening_order": data["tightening_order"],
                    }
                    for position, data in centres.items()
                },
                "pending_snapshot": design.snapshots.hasPendingSnapshot,
            }
        )
    )
