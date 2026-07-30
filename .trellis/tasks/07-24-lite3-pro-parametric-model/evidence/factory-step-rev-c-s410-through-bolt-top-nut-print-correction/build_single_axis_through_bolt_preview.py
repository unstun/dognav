"""Build a reversible one-axis S410 through-bolt + top-nut preview.

This script does not overwrite the accepted Rev B print candidate.  It creates
a separately named Rev C single-axis preview, widens only S1_TOP_LEFT from the
modeled 4.2 mm receiver to a 5.2 mm through hole, and adds one visual M5x14
bottom-up bolt plus one visual M5 top nut.

All dimensions remain print/visual candidates pending physical validation.
"""

import adsk.core
import adsk.fusion
import json
import math
import os


globals().pop("run", None)


EVIDENCE_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-rev-c-s410-through-bolt-top-nut-print-correction"
)
F3D_PATH = os.path.join(
    EVIDENCE_DIR,
    "lite3-rev-c-s410-single-through-bolt-top-nut-preview.f3d",
)
BUILD_REPORT = os.path.join(EVIDENCE_DIR, "single_axis_build_report.json")

REV_B_COMPONENT_NAME = (
    "J17A_J20A_MONOLITHIC_REAR_WEB_PRINT_ADAPTATION_REV_B_NOT_OFFICIAL_CAD"
)
REV_C_COMPONENT_NAME = (
    "J17A_J20A_REV_C_S410_SINGLE_THROUGH_HOLE_PREVIEW_NOT_OFFICIAL_CAD"
)
REV_C_BODY_NAME = "J17A_J20A_REV_C_SINGLE_S410_CLEARANCE_HOLE_PREVIEW"
OLD_SCREW_COMPONENT_NAME = (
    "S410_TO_J20_M5X8_INDIVIDUAL_SCREW_VISUAL_CANDIDATE"
)
BOLT_COMPONENT_NAME = (
    "S410_S1_M5X14_BOTTOM_UP_THROUGH_BOLT_VISUAL_CANDIDATE"
)
NUT_COMPONENT_NAME = "S410_S1_M5_TOP_HEX_NUT_VISUAL_CANDIDATE"
MOUNT_NORMAL = (0.0, 0.9659258262890683, 0.25881904510252074)
SELECTED_POSITION = "S1_TOP_LEFT"

TRANSFORM_ATTRIBUTE_GROUP = "codex_full_installation_animation"
FINAL_TRANSFORM_ATTRIBUTE = "final_transform"
FINAL_VISIBILITY_ATTRIBUTE = "final_visibility"

# Fusion internal units are centimetres.
CLEARANCE_RADIUS_CM = 0.26  # candidate diameter 5.2 mm
BOLT_RADIUS_CM = 0.25       # nominal M5 visual shaft
BOLT_LENGTH_CM = 1.40       # visual M5x14 candidate
HEAD_RADIUS_CM = 0.425      # 8.5 mm socket-head visual envelope
HEAD_HEIGHT_CM = 0.50       # 5.0 mm socket-head visual envelope
SOCKET_RADIUS_CM = 0.18     # simplified recess; not a supplied-tool claim
SOCKET_DEPTH_CM = 0.25
NUT_ACROSS_FLATS_CM = 0.80  # 8 mm M5 visual envelope
NUT_THICKNESS_CM = 0.40     # 4 mm M5 visual envelope
NUT_HOLE_RADIUS_CM = 0.255  # simplified non-threaded visual clearance


def point(values):
    return adsk.core.Point3D.create(*values)


def vector(values):
    return adsk.core.Vector3D.create(*values)


def point_values(value):
    return [value.x, value.y, value.z]


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


def face_projection_interval(face, transform, normal):
    values = []
    for edge_index in range(face.edges.count):
        edge = face.edges.item(edge_index)
        for vertex_value in (edge.startVertex, edge.endVertex):
            if vertex_value is None:
                continue
            vertex_point = vertex_value.geometry.copy()
            vertex_point.transformBy(transform)
            values.append(projection(vertex_point, normal))
    if not values:
        raise RuntimeError("Selected cylindrical face has no edge vertices")
    return min(values), max(values)


def point_at_projection(axis_point, normal, target_projection):
    return shifted(
        axis_point,
        normal,
        target_projection - projection(axis_point, normal),
    )


def create_hex_nut(temporary, center, normal):
    u_axis = vector((1.0, 0.0, 0.0))
    if abs(u_axis.dotProduct(normal)) > 1.0e-9:
        raise RuntimeError("Expected the model width axis to be normal-orthogonal")
    v_axis = normal.crossProduct(u_axis)
    v_axis.normalize()
    long_span = 2.0
    hex_body = None
    for angle_degrees in (0.0, 60.0, 120.0):
        angle = math.radians(angle_degrees)
        length_direction = vector(
            (
                u_axis.x * math.cos(angle) + v_axis.x * math.sin(angle),
                u_axis.y * math.cos(angle) + v_axis.y * math.sin(angle),
                u_axis.z * math.cos(angle) + v_axis.z * math.sin(angle),
            )
        )
        width_direction = vector(
            (
                -u_axis.x * math.sin(angle) + v_axis.x * math.cos(angle),
                -u_axis.y * math.sin(angle) + v_axis.y * math.cos(angle),
                -u_axis.z * math.sin(angle) + v_axis.z * math.cos(angle),
            )
        )
        slab_box = adsk.core.OrientedBoundingBox3D.create(
            center,
            length_direction,
            width_direction,
            long_span,
            NUT_ACROSS_FLATS_CM,
            NUT_THICKNESS_CM,
        )
        slab = temporary.createBox(slab_box)
        if slab is None:
            raise RuntimeError("Could not create a temporary hex-nut slab")
        if hex_body is None:
            hex_body = slab
        elif not temporary.booleanOperation(
            hex_body,
            slab,
            adsk.fusion.BooleanTypes.IntersectionBooleanType,
        ):
            raise RuntimeError("Could not intersect the temporary hex-nut slabs")

    hole_start = shifted(center, normal, -NUT_THICKNESS_CM)
    hole_end = shifted(center, normal, NUT_THICKNESS_CM)
    hole = temporary.createCylinderOrCone(
        hole_start,
        NUT_HOLE_RADIUS_CM,
        hole_end,
        NUT_HOLE_RADIUS_CM,
    )
    if hole is None or not temporary.booleanOperation(
        hex_body,
        hole,
        adsk.fusion.BooleanTypes.DifferenceBooleanType,
    ):
        raise RuntimeError("Could not cut the simplified M5 nut opening")
    return hex_body


def add_component_body(root, name, body_name, temporary_body, appearance=None):
    occurrence = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    component = occurrence.component
    component.name = name
    base_feature = component.features.baseFeatures.add()
    base_feature.name = body_name + "_BASE_FEATURE"
    base_feature.startEdit()
    body = component.bRepBodies.add(temporary_body, base_feature)
    if body is None:
        raise RuntimeError("Could not add body for " + name)
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

    for index in range(occurrences.count):
        if occurrences.item(index).component.name in (
            REV_C_COMPONENT_NAME,
            BOLT_COMPONENT_NAME,
            NUT_COMPONENT_NAME,
        ):
            raise RuntimeError("The single-axis Rev C preview already exists")

    rev_b = None
    rev_b_index = None
    guard = None
    guard_index = None
    selected_screw = None
    selected_screw_index = None
    old_screw_indices = []
    for index in range(occurrences.count):
        occurrence = occurrences.item(index)
        if occurrence.component.name == REV_B_COMPONENT_NAME:
            rev_b = occurrence
            rev_b_index = index
        if index == 3 and "S410" in occurrence.component.name:
            guard = occurrence
            guard_index = index
        if occurrence.component.name == OLD_SCREW_COMPONENT_NAME:
            old_screw_indices.append(index)
            position_attribute = occurrence.attributes.itemByName(
                "s410_sequential_fastener", "position"
            )
            if (
                position_attribute is not None
                and position_attribute.value == SELECTED_POSITION
            ):
                selected_screw = occurrence
                selected_screw_index = index

    if rev_b is None or guard is None or selected_screw is None:
        raise RuntimeError("Could not resolve the reviewed Rev B/S410 source scene")
    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()

    normal = vector(MOUNT_NORMAL)
    normal.normalize()
    translation = selected_screw.transform2.translation
    axis_point = point((translation.x, translation.y, translation.z))

    guard_face = guard.component.bRepBodies.item(0).faces.item(5)
    guard_cylinder = adsk.core.Cylinder.cast(guard_face.geometry)
    rev_b_body = rev_b.component.bRepBodies.item(0)
    rev_b_face = rev_b_body.faces.item(29)
    rev_b_cylinder = adsk.core.Cylinder.cast(rev_b_face.geometry)
    if guard_cylinder is None or abs(guard_cylinder.radius - 0.26) > 1.0e-5:
        raise RuntimeError("Unexpected S410 S1 clearance face")
    if rev_b_cylinder is None or abs(rev_b_cylinder.radius - 0.21) > 1.0e-5:
        raise RuntimeError("Unexpected Rev B S1 receiver face")

    guard_interval = face_projection_interval(
        guard_face, guard.transform2, normal
    )
    rev_b_interval = face_projection_interval(
        rev_b_face, rev_b.transform2, normal
    )
    underside_projection = min(rev_b_interval)
    topside_projection = max(guard_interval)
    stack_mm = (topside_projection - underside_projection) * 10.0
    underside_point = point_at_projection(
        axis_point, normal, underside_projection
    )
    topside_point = point_at_projection(axis_point, normal, topside_projection)

    temporary = adsk.fusion.TemporaryBRepManager.get()
    rev_c_temp = temporary.copy(rev_b_body)
    cutter_start = shifted(underside_point, normal, -0.20)
    cutter_end = shifted(topside_point, normal, 0.20)
    clearance_cutter = temporary.createCylinderOrCone(
        cutter_start,
        CLEARANCE_RADIUS_CM,
        cutter_end,
        CLEARANCE_RADIUS_CM,
    )
    if clearance_cutter is None or not temporary.booleanOperation(
        rev_c_temp,
        clearance_cutter,
        adsk.fusion.BooleanTypes.DifferenceBooleanType,
    ):
        raise RuntimeError("Could not widen S1 to the 5.2 mm through-hole candidate")
    if not rev_c_temp.isSolid:
        raise RuntimeError("Rev C single-axis preview is not a closed solid")

    rev_c_occurrence, rev_c_body = add_component_body(
        root,
        REV_C_COMPONENT_NAME,
        REV_C_BODY_NAME,
        rev_c_temp,
        rev_b_body.appearance,
    )

    shaft_end = shifted(underside_point, normal, BOLT_LENGTH_CM)
    shaft = temporary.createCylinderOrCone(
        underside_point,
        BOLT_RADIUS_CM,
        shaft_end,
        BOLT_RADIUS_CM,
    )
    head_bottom = shifted(underside_point, normal, -HEAD_HEIGHT_CM)
    head = temporary.createCylinderOrCone(
        head_bottom,
        HEAD_RADIUS_CM,
        underside_point,
        HEAD_RADIUS_CM,
    )
    if shaft is None or head is None or not temporary.booleanOperation(
        shaft, head, adsk.fusion.BooleanTypes.UnionBooleanType
    ):
        raise RuntimeError("Could not create the bottom-up bolt envelope")
    socket_end = shifted(head_bottom, normal, SOCKET_DEPTH_CM)
    socket_cutter = temporary.createCylinderOrCone(
        shifted(head_bottom, normal, -0.01),
        SOCKET_RADIUS_CM,
        socket_end,
        SOCKET_RADIUS_CM,
    )
    if socket_cutter is None or not temporary.booleanOperation(
        shaft,
        socket_cutter,
        adsk.fusion.BooleanTypes.DifferenceBooleanType,
    ):
        raise RuntimeError("Could not add the simplified underside socket recess")

    fastener_appearance = None
    if old_screw_indices:
        old_body = occurrences.item(old_screw_indices[0]).component.bRepBodies.item(0)
        fastener_appearance = old_body.appearance
    bolt_occurrence, bolt_body = add_component_body(
        root,
        BOLT_COMPONENT_NAME,
        "M5X14_BOTTOM_UP_SOCKET_HEAD_BOLT_VISUAL",
        shaft,
        fastener_appearance,
    )

    nut_center = shifted(topside_point, normal, NUT_THICKNESS_CM * 0.5)
    nut_temp = create_hex_nut(temporary, nut_center, normal)
    nut_appearance = fastener_appearance
    if occurrences.count > 9 and occurrences.item(9).component.bRepBodies.count:
        nut_appearance = occurrences.item(9).component.bRepBodies.item(0).appearance
    nut_occurrence, nut_body = add_component_body(
        root,
        NUT_COMPONENT_NAME,
        "M5_TOP_HEX_NUT_SIMPLIFIED_VISUAL",
        nut_temp,
        nut_appearance,
    )

    contract = {
        "selected_position": SELECTED_POSITION,
        "axis_point_cm": point_values(axis_point),
        "mount_normal": list(MOUNT_NORMAL),
        "printed_receiver": "plain through hole",
        "hole_diameter_mm": CLEARANCE_RADIUS_CM * 20.0,
        "bolt": {
            "direction": "bottom/underside to top",
            "nominal": "M5x14 visual candidate",
            "under_head_length_mm": BOLT_LENGTH_CM * 10.0,
            "head_diameter_mm": HEAD_RADIUS_CM * 20.0,
            "head_height_mm": HEAD_HEIGHT_CM * 10.0,
        },
        "nut": {
            "location": "top side of S410 foot",
            "across_flats_mm": NUT_ACROSS_FLATS_CM * 10.0,
            "thickness_mm": NUT_THICKNESS_CM * 10.0,
            "thread_geometry": "not modeled; simplified visual opening",
        },
        "measured_stack_mm": stack_mm,
        "modeled_thread_protrusion_above_nut_mm": (
            BOLT_LENGTH_CM
            - (topside_projection - underside_projection)
            - NUT_THICKNESS_CM
        )
        * 10.0,
    }
    for component in (
        rev_c_occurrence.component,
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
            "One-axis visual/print candidate only; no official hardware, torque, print tolerance, strength, vibration, or real-robot safety claim",
        )

    rev_b.isLightBulbOn = False
    set_final_state_attributes(rev_b, False)
    for index in old_screw_indices:
        occurrences.item(index).isLightBulbOn = False
        set_final_state_attributes(occurrences.item(index), False)
    rev_c_occurrence.isLightBulbOn = True
    bolt_occurrence.isLightBulbOn = True
    nut_occurrence.isLightBulbOn = True
    set_final_state_attributes(rev_c_occurrence, True)
    set_final_state_attributes(bolt_occurrence, True)
    set_final_state_attributes(nut_occurrence, True)
    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()

    export_options = design.exportManager.createFusionArchiveExportOptions(
        F3D_PATH, root
    )
    if export_options is None or not design.exportManager.execute(export_options):
        raise RuntimeError("Could not export the single-axis Rev C preview F3D")

    report = {
        "stage": "experiment_and_analysis",
        "status": "awaiting_single_axis_visual_review",
        "document": application.activeDocument.name,
        "indices": {
            "rev_b_hidden": rev_b_index,
            "rev_c_single_axis_preview": occurrences.count - 3,
            "bottom_up_bolt": occurrences.count - 2,
            "top_nut": occurrences.count - 1,
            "official_s410_guard": guard_index,
            "superseded_direct_thread_screw": selected_screw_index,
            "all_hidden_direct_thread_screws": old_screw_indices,
        },
        "contract": contract,
        "geometry": {
            "rev_c_body_count": rev_c_occurrence.component.bRepBodies.count,
            "rev_c_is_solid": rev_c_body.isSolid,
            "bolt_is_solid": bolt_body.isSolid,
            "nut_is_solid": nut_body.isSolid,
            "root_occurrence_count": occurrences.count,
        },
        "preservation": {
            "rev_b_preserved_and_hidden": True,
            "official_s410_preserved": True,
            "only_one_rev_c_hole_widened_for_preview": True,
            "f3d": F3D_PATH,
        },
        "claim_boundary": (
            "Single-axis user-corrected visual/print candidate only. Exact bolt "
            "standard, nut type, fit, print tolerance, torque, strength, vibration, "
            "and real-robot safety remain unvalidated."
        ),
    }
    with open(BUILD_REPORT, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
