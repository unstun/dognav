"""Add four visual M5 fasteners on the official S410/J20 hole axes.

The S410 drawing calls out four 5.2 mm clearance holes. The J20 drawing and
manufacturer BRep contain the four coincident M5 through-thread axes. The
nominal M5x8 screw length is a visual candidate because the public drawings do
not specify the supplied screw length, head standard, torque, or engagement.
"""

import adsk.core
import adsk.fusion
import json

globals().pop("run", None)


COMPONENT_NAME = "S410_TO_J20_4X_M5X8_SOCKET_HEAD_SCREWS_VISUAL_CANDIDATE"
ANIMATION_ATTRIBUTE_GROUP = "codex_full_installation_animation"
FINAL_TRANSFORM_ATTRIBUTE = "final_transform"
FINAL_VISIBILITY_ATTRIBUTE = "final_visibility"
ALIGNMENT_ATTRIBUTE_GROUP = "s410_axis_alignment"
ALIGNMENT_ATTRIBUTE_NAME = "guard_to_j20_rigid_translation_cm"
ALIGNMENT_CORRECTION_CM = (
    0.0,
    -0.0044219104382,
    0.0165027944219,
)


def point_shifted(point, vector, distance):
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


def run(context):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")

    root = design.rootComponent
    occurrences = root.occurrences
    existing = None
    existing_index = None
    for index in range(occurrences.count):
        candidate = occurrences.item(index)
        if candidate.component.name == COMPONENT_NAME:
            existing = candidate
            existing_index = index
            break

    guard = occurrences.item(3)
    if "S410" not in guard.name:
        raise RuntimeError("Occurrence 3 is not the official S410 guard")

    alignment_attribute = guard.attributes.itemByName(
        ALIGNMENT_ATTRIBUTE_GROUP, ALIGNMENT_ATTRIBUTE_NAME
    )
    alignment_applied_now = alignment_attribute is None
    if alignment_applied_now:
        guard_values = list(guard.transform2.asArray())
        guard_values[3] += ALIGNMENT_CORRECTION_CM[0]
        guard_values[7] += ALIGNMENT_CORRECTION_CM[1]
        guard_values[11] += ALIGNMENT_CORRECTION_CM[2]
        guard_matrix = adsk.core.Matrix3D.create()
        guard_matrix.setWithArray(guard_values)
        guard.transform = guard_matrix
        guard.attributes.add(
            ALIGNMENT_ATTRIBUTE_GROUP,
            ALIGNMENT_ATTRIBUTE_NAME,
            json.dumps(list(ALIGNMENT_CORRECTION_CM)),
        )

    guard.isLightBulbOn = True
    replace_attribute(
        guard,
        ANIMATION_ATTRIBUTE_GROUP,
        FINAL_TRANSFORM_ATTRIBUTE,
        json.dumps(list(guard.transform.asArray())),
    )
    replace_attribute(
        guard,
        ANIMATION_ATTRIBUTE_GROUP,
        FINAL_VISIBILITY_ATTRIBUTE,
        "true",
    )

    if existing is not None:
        if alignment_applied_now:
            existing_values = list(existing.transform2.asArray())
            existing_values[3] += ALIGNMENT_CORRECTION_CM[0]
            existing_values[7] += ALIGNMENT_CORRECTION_CM[1]
            existing_values[11] += ALIGNMENT_CORRECTION_CM[2]
            existing_matrix = adsk.core.Matrix3D.create()
            existing_matrix.setWithArray(existing_values)
            existing.transform = existing_matrix
        replace_attribute(
            existing,
            ANIMATION_ATTRIBUTE_GROUP,
            FINAL_TRANSFORM_ATTRIBUTE,
            json.dumps(list(existing.transform.asArray())),
        )
        existing.isLightBulbOn = True
        replace_attribute(
            existing,
            ANIMATION_ATTRIBUTE_GROUP,
            FINAL_VISIBILITY_ATTRIBUTE,
            "true",
        )
        print(
            json.dumps(
                {
                    "status": "already_present",
                    "root_occurrence_count": occurrences.count,
                    "occurrence_index": existing_index,
                    "component": COMPONENT_NAME,
                    "alignment_applied_now": alignment_applied_now,
                }
            )
        )
        return

    if occurrences.count != 27:
        raise RuntimeError(
            "Expected the reviewed 27-occurrence source scene, found "
            + str(occurrences.count)
        )

    transform = guard.transform2
    body = guard.component.bRepBodies.item(0)
    normal = adsk.core.Vector3D.create(
        0.0, 0.9659258262890683, 0.25881904510252074
    )
    normal.normalize()

    # Manufacturer S410 BRep faces 5-8 are the four 5.2 mm clearance bores.
    axes = []
    for face_index in (5, 6, 7, 8):
        face = body.faces.item(face_index)
        cylinder = adsk.core.Cylinder.cast(face.geometry)
        if cylinder is None or abs(cylinder.radius - 0.26) > 1.0e-6:
            raise RuntimeError(
                "Unexpected S410 clearance face at index " + str(face_index)
            )

        center = cylinder.origin.copy()
        center.transformBy(transform)
        center_projection = (
            center.x * normal.x
            + center.y * normal.y
            + center.z * normal.z
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
        outer_center = point_shifted(
            center, normal, outer_projection - center_projection
        )
        axes.append(outer_center)

    occurrence = occurrences.addNewComponent(adsk.core.Matrix3D.create())
    component = occurrence.component
    component.name = COMPONENT_NAME
    base_feature = component.features.baseFeatures.add()
    base_feature.name = "S410_M5_FASTENER_BREP"
    base_feature.startEdit()

    temporary = adsk.fusion.TemporaryBRepManager.get()
    source_appearance = None
    source_fastener = occurrences.item(18).component
    if source_fastener.bRepBodies.count:
        source_appearance = source_fastener.bRepBodies.item(0).appearance

    for screw_index, seat in enumerate(axes, start=1):
        # Fusion internal length unit is cm: M5x8 shaft and 8.5x5 mm head.
        shaft_end = point_shifted(seat, normal, -0.8)
        head_top = point_shifted(seat, normal, 0.5)
        shaft_temp = temporary.createCylinderOrCone(
            seat, 0.25, shaft_end, 0.25
        )
        head_temp = temporary.createCylinderOrCone(
            seat, 0.425, head_top, 0.425
        )
        shaft_body = component.bRepBodies.add(shaft_temp, base_feature)
        head_body = component.bRepBodies.add(head_temp, base_feature)
        shaft_body.name = "M5X8_SHAFT_%d" % screw_index
        head_body.name = "M5_SOCKET_HEAD_%d" % screw_index
        if source_appearance is not None:
            shaft_body.appearance = source_appearance
            head_body.appearance = source_appearance

    base_feature.finishEdit()

    component.attributes.add(
        "s410_fastener_evidence",
        "source_contract",
        "S410 4x phi5.2 clearance to J20 4x M5 through-thread",
    )
    component.attributes.add(
        "s410_fastener_evidence",
        "claim_boundary",
        "M5x8 socket-head length and head form are visual candidates",
    )
    occurrence.isLightBulbOn = True
    replace_attribute(
        occurrence,
        ANIMATION_ATTRIBUTE_GROUP,
        FINAL_TRANSFORM_ATTRIBUTE,
        json.dumps(list(occurrence.transform.asArray())),
    )
    replace_attribute(
        occurrence,
        ANIMATION_ATTRIBUTE_GROUP,
        FINAL_VISIBILITY_ATTRIBUTE,
        "true",
    )

    print(
        json.dumps(
            {
                "status": "created",
                "root_occurrence_count": occurrences.count,
                "occurrence_index": occurrences.count - 1,
                "component": COMPONENT_NAME,
                "body_count": component.bRepBodies.count,
                "screw_count": len(axes),
                "axis_centers_cm": [
                    [point.x, point.y, point.z] for point in axes
                ],
            }
        )
    )
