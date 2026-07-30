"""Render a no-text, multi-view preview of the corrected S410 fastener stack."""

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
RENDER_REPORT = os.path.join(
    EVIDENCE_DIR, "single_axis_head_access_render_report.json"
)

REV_C_COMPONENT_NAME = (
    "J17A_J20A_REV_C2_S410_SINGLE_THROUGH_HOLE_HEAD_ACCESS_PREVIEW_NOT_OFFICIAL_CAD"
)
BOLT_COMPONENT_NAME = (
    "S410_S1_M5X14_BOTTOM_UP_BOLT_HEAD_ACCESS_PREVIEW"
)
NUT_COMPONENT_NAME = "S410_S1_M5_TOP_HEX_NUT_HEAD_ACCESS_PREVIEW"

MOUNT_NORMAL = (0.0, 0.9659258262890683, 0.25881904510252074)
PLATE_UP = (0.0, -0.25881904510252074, 0.9659258262890683)
WIDTH_AXIS = (1.0, 0.0, 0.0)
AXIS_POINT = (-32.90685957328745, 21.378538809797107, 260.49515922999285)
UNDERSIDE_PROJECTION_CM = 87.33122856653883
TOPSIDE_PROJECTION_CM = 88.07119113044189


def point(values):
    return adsk.core.Point3D.create(*values)


def vector(values):
    return adsk.core.Vector3D.create(*values)


def normalized(values):
    length = math.sqrt(sum(value * value for value in values))
    return tuple(value / length for value in values)


def scaled(values, amount):
    return tuple(value * amount for value in values)


def added(first, second):
    return tuple(first[index] + second[index] for index in range(3))


def projected(values, direction):
    return sum(values[index] * direction[index] for index in range(3))


def at_projection(axis_point, direction, target_projection):
    return added(
        axis_point,
        scaled(direction, target_projection - projected(axis_point, direction)),
    )


def camera_state(camera):
    return {
        "eye": (camera.eye.x, camera.eye.y, camera.eye.z),
        "target": (camera.target.x, camera.target.y, camera.target.z),
        "up": (camera.upVector.x, camera.upVector.y, camera.upVector.z),
        "extents": camera.viewExtents,
        "type": camera.cameraType,
    }


def restore_camera(viewport, state):
    camera = viewport.camera
    camera.isSmoothTransition = False
    camera.cameraType = state["type"]
    camera.eye = point(state["eye"])
    camera.target = point(state["target"])
    camera.upVector = vector(state["up"])
    camera.viewExtents = state["extents"]
    viewport.camera = camera


def apply_camera(viewport, target, direction, extents, up):
    direction = normalized(direction)
    camera = viewport.camera
    camera.isSmoothTransition = False
    camera.cameraType = adsk.core.CameraTypes.OrthographicCameraType
    camera.eye = point(added(target, scaled(direction, 18.0)))
    camera.target = point(target)
    camera.upVector = vector(up)
    camera.viewExtents = extents
    viewport.camera = camera


def color_effect(red, green, blue, opacity=1.0):
    diffuse = adsk.core.Color.create(red, green, blue, 255)
    ambient = adsk.core.Color.create(
        min(255, red + 32), min(255, green + 32), min(255, blue + 32), 255
    )
    specular = adsk.core.Color.create(255, 255, 255, 255)
    emissive = adsk.core.Color.create(0, 0, 0, 255)
    return adsk.fusion.CustomGraphicsBasicMaterialColorEffect.create(
        diffuse, ambient, specular, emissive, 24.0, opacity
    )


def translation_matrix(offset):
    matrix = adsk.core.Matrix3D.create()
    matrix.translation = vector(offset)
    return matrix


def world_body_copy(temporary, occurrence, body_index=0, offset=(0.0, 0.0, 0.0)):
    body = temporary.copy(occurrence.component.bRepBodies.item(body_index))
    transform = occurrence.transform2.copy()
    if not temporary.transform(body, transform):
        raise RuntimeError("Could not transform graphics body into assembly space")
    if any(abs(value) > 1.0e-12 for value in offset):
        if not temporary.transform(body, translation_matrix(offset)):
            raise RuntimeError("Could not apply exploded-view offset")
    return body


def add_colored_body(group, body, color):
    graphic = group.addBRepBody(body)
    if graphic is None:
        raise RuntimeError("Could not add a colored preview body")
    graphic.color = color
    graphic.isSelectable = False
    return graphic


def add_local_section_slices(
    group,
    temporary,
    rev_c_occurrence,
    guard_occurrence,
    center,
    rev_c_color,
    guard_color,
):
    section_box = adsk.core.OrientedBoundingBox3D.create(
        point(center),
        vector(MOUNT_NORMAL),
        vector(PLATE_UP),
        3.2,
        3.2,
        0.75,
    )
    section_volume = temporary.createBox(section_box)
    if section_volume is None:
        raise RuntimeError("Could not create the local section volume")
    for occurrence, color in (
        (rev_c_occurrence, rev_c_color),
        (guard_occurrence, guard_color),
    ):
        section_body = world_body_copy(temporary, occurrence)
        clip_body = temporary.copy(section_volume)
        if not temporary.booleanOperation(
            section_body,
            clip_body,
            adsk.fusion.BooleanTypes.IntersectionBooleanType,
        ):
            raise RuntimeError("Could not create a local fastener section slice")
        add_colored_body(group, section_body, color)


def create_direction_arrow(temporary, axis_point, normal, exploded):
    underside = at_projection(AXIS_POINT, MOUNT_NORMAL, UNDERSIDE_PROJECTION_CM)
    topside = at_projection(AXIS_POINT, MOUNT_NORMAL, TOPSIDE_PROJECTION_CM)
    side_offset = scaled(PLATE_UP, -0.95)
    start = added(underside, added(side_offset, scaled(MOUNT_NORMAL, -1.15 if exploded else -0.45)))
    cone_base = added(topside, added(side_offset, scaled(MOUNT_NORMAL, 0.75 if exploded else 0.45)))
    shaft_end = added(cone_base, scaled(MOUNT_NORMAL, -0.28))
    arrow_tip = added(cone_base, scaled(MOUNT_NORMAL, 0.28))
    shaft = temporary.createCylinderOrCone(
        point(start), 0.055, point(shaft_end), 0.055
    )
    cone = temporary.createCylinderOrCone(
        point(shaft_end), 0.16, point(arrow_tip), 0.0
    )
    if shaft is None or cone is None:
        raise RuntimeError("Could not create the bottom-up direction arrow")
    return shaft, cone


def render(viewport, path, target, direction, extents, up):
    apply_camera(viewport, target, direction, extents, up)
    viewport.refresh()
    adsk.doEvents()
    if not viewport.saveAsImageFile(path, 1600, 1000):
        raise RuntimeError("Could not render " + path)


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences
    os.makedirs(EVIDENCE_DIR, exist_ok=True)

    indices = {}
    guard_index = None
    for index in range(occurrences.count):
        name = occurrences.item(index).component.name
        if name == REV_C_COMPONENT_NAME:
            indices["rev_c"] = index
        elif name == BOLT_COMPONENT_NAME:
            indices["bolt"] = index
        elif name == NUT_COMPONENT_NAME:
            indices["nut"] = index
        elif index == 3 and "S410" in name:
            guard_index = index
    if set(indices) != {"rev_c", "bolt", "nut"} or guard_index is None:
        raise RuntimeError("The single-axis corrected preview scene is incomplete")

    original_visibility = [
        bool(occurrences.item(index).isLightBulbOn)
        for index in range(occurrences.count)
    ]
    opacity_records = []
    for key in ("rev_c",):
        component = occurrences.item(indices[key]).component
        for body_index in range(component.bRepBodies.count):
            body = component.bRepBodies.item(body_index)
            opacity_records.append((body, body.opacity))
    guard_component = occurrences.item(guard_index).component
    for body_index in range(guard_component.bRepBodies.count):
        body = guard_component.bRepBodies.item(body_index)
        opacity_records.append((body, body.opacity))

    viewport = application.activeViewport
    original_camera = camera_state(viewport.camera)
    temporary = adsk.fusion.TemporaryBRepManager.get()
    graphics = root.customGraphicsGroups.add()
    graphics.id = "S410_SINGLE_AXIS_THROUGH_BOLT_TOP_NUT_PREVIEW"
    graphics.isSelectable = False
    rendered = []
    graphics_deleted = False

    bolt_color = color_effect(244, 122, 35, 1.0)
    nut_color = color_effect(74, 190, 95, 1.0)
    arrow_color = color_effect(40, 150, 245, 0.92)
    axis_color = color_effect(48, 170, 245, 0.28)
    rev_c_section_color = color_effect(205, 211, 224, 0.40)
    guard_section_color = color_effect(170, 188, 213, 0.30)

    center_projection = (UNDERSIDE_PROJECTION_CM + TOPSIDE_PROJECTION_CM) * 0.5
    center = at_projection(AXIS_POINT, MOUNT_NORMAL, center_projection)
    side_target = added(center, scaled(PLATE_UP, -0.10))
    top_target = at_projection(AXIS_POINT, MOUNT_NORMAL, TOPSIDE_PROJECTION_CM + 0.12)
    underside_target = at_projection(
        AXIS_POINT, MOUNT_NORMAL, UNDERSIDE_PROJECTION_CM - 0.18
    )

    try:
        for index in range(occurrences.count):
            occurrences.item(index).isLightBulbOn = False
        for body_index in range(
            occurrences.item(indices["rev_c"]).component.bRepBodies.count
        ):
            occurrences.item(indices["rev_c"]).component.bRepBodies.item(
                body_index
            ).opacity = 0.33
        for body_index in range(guard_component.bRepBodies.count):
            guard_component.bRepBodies.item(body_index).opacity = 0.24

        # View 1: assembled cutaway side view.
        add_local_section_slices(
            graphics,
            temporary,
            occurrences.item(indices["rev_c"]),
            occurrences.item(guard_index),
            side_target,
            rev_c_section_color,
            guard_section_color,
        )
        add_colored_body(
            graphics,
            world_body_copy(temporary, occurrences.item(indices["bolt"])),
            bolt_color,
        )
        add_colored_body(
            graphics,
            world_body_copy(temporary, occurrences.item(indices["nut"])),
            nut_color,
        )
        arrow_parts = create_direction_arrow(
            temporary, AXIS_POINT, MOUNT_NORMAL, False
        )
        for arrow_part in arrow_parts:
            add_colored_body(graphics, arrow_part, arrow_color)
        axis_start = point(
            at_projection(AXIS_POINT, MOUNT_NORMAL, UNDERSIDE_PROJECTION_CM - 0.16)
        )
        axis_end = point(
            at_projection(AXIS_POINT, MOUNT_NORMAL, TOPSIDE_PROJECTION_CM + 0.52)
        )
        axis_body = temporary.createCylinderOrCone(
            axis_start, 0.07, axis_end, 0.07
        )
        add_colored_body(graphics, axis_body, axis_color)
        assembled_path = os.path.join(
            EVIDENCE_DIR, "single-axis-head-access-assembled-side-cutaway.png"
        )
        render(
            viewport,
            assembled_path,
            side_target,
            WIDTH_AXIS,
            4.4,
            MOUNT_NORMAL,
        )
        rendered.append(assembled_path)

        # Clear and rebuild graphics for the exploded side view.
        graphics.deleteMe()
        graphics = root.customGraphicsGroups.add()
        graphics.id = "S410_SINGLE_AXIS_THROUGH_BOLT_TOP_NUT_EXPLODED"
        graphics.isSelectable = False
        add_local_section_slices(
            graphics,
            temporary,
            occurrences.item(indices["rev_c"]),
            occurrences.item(guard_index),
            side_target,
            rev_c_section_color,
            guard_section_color,
        )
        add_colored_body(
            graphics,
            world_body_copy(
                temporary,
                occurrences.item(indices["bolt"]),
                offset=scaled(MOUNT_NORMAL, -1.10),
            ),
            bolt_color,
        )
        add_colored_body(
            graphics,
            world_body_copy(
                temporary,
                occurrences.item(indices["nut"]),
                offset=scaled(MOUNT_NORMAL, 0.80),
            ),
            nut_color,
        )
        for arrow_part in create_direction_arrow(
            temporary, AXIS_POINT, MOUNT_NORMAL, True
        ):
            add_colored_body(graphics, arrow_part, arrow_color)
        exploded_path = os.path.join(
            EVIDENCE_DIR,
            "single-axis-head-access-exploded-bottom-bolt-top-nut.png",
        )
        render(
            viewport,
            exploded_path,
            side_target,
            WIDTH_AXIS,
            6.6,
            MOUNT_NORMAL,
        )
        rendered.append(exploded_path)

        # Top view: the nut sits on the S410 foot.
        graphics.deleteMe()
        graphics = root.customGraphicsGroups.add()
        graphics.id = "S410_SINGLE_AXIS_TOP_NUT_VIEW"
        graphics.isSelectable = False
        occurrences.item(indices["rev_c"]).isLightBulbOn = True
        occurrences.item(guard_index).isLightBulbOn = True
        add_colored_body(
            graphics,
            world_body_copy(temporary, occurrences.item(indices["nut"])),
            nut_color,
        )
        top_path = os.path.join(
            EVIDENCE_DIR, "single-axis-head-access-topside-nut.png"
        )
        render(
            viewport,
            top_path,
            top_target,
            MOUNT_NORMAL,
            4.4,
            PLATE_UP,
        )
        rendered.append(top_path)

        # Underside view: only the bolt head is accessible from below.
        graphics.deleteMe()
        graphics = root.customGraphicsGroups.add()
        graphics.id = "S410_SINGLE_AXIS_UNDERSIDE_BOLT_VIEW"
        graphics.isSelectable = False
        add_colored_body(
            graphics,
            world_body_copy(temporary, occurrences.item(indices["bolt"])),
            bolt_color,
        )
        underside_path = os.path.join(
            EVIDENCE_DIR, "single-axis-head-access-underside-bolt-head.png"
        )
        render(
            viewport,
            underside_path,
            underside_target,
            scaled(MOUNT_NORMAL, -1.0),
            4.4,
            PLATE_UP,
        )
        rendered.append(underside_path)
    finally:
        if graphics is not None and graphics.isValid:
            graphics_deleted = bool(graphics.deleteMe())
        for body, opacity in opacity_records:
            body.opacity = opacity
        for index, visible in enumerate(original_visibility):
            occurrences.item(index).isLightBulbOn = visible
        restore_camera(viewport, original_camera)
        viewport.refresh()
        adsk.doEvents()

    visibility_mismatches = [
        index
        for index, expected in enumerate(original_visibility)
        if bool(occurrences.item(index).isLightBulbOn) != expected
    ]
    opacity_mismatches = [
        body.name
        for body, expected in opacity_records
        if abs(body.opacity - expected) > 1.0e-12
    ]
    report = {
        "stage": "experiment_and_analysis",
        "status": "awaiting_user_direction_and_layer_review",
        "rendered": rendered,
        "render_count": len(rendered),
        "visual_encoding": {
            "orange": "M5x14 bolt entering from underside",
            "green": "M5 hex nut seated on top",
            "blue_arrow": "bottom-up insertion direction",
            "ghosted_parts": "Rev C printed bracket and official S410 guard",
            "head_access": "9.5 mm x 6.5 mm underside access bore around the orange bolt head",
        },
        "restoration": {
            "visibility_mismatches": visibility_mismatches,
            "opacity_mismatches": opacity_mismatches,
            "custom_graphics_deleted": graphics_deleted,
        },
        "claim_boundary": (
            "The images validate direction and modeled packaging only. Hardware "
            "standard, fit, torque, print tolerance, strength, vibration, and real-robot "
            "safety remain unvalidated."
        ),
    }
    with open(RENDER_REPORT, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
