"""Render the slow, no-text physical-Lite3 carrier V1 installation animation.

The printable J17A/J20A-derived carrier is already one piece.  The human order
is therefore D435i -> Mid-360 -> S410 -> rear spacers -> complete module to
Lite3 -> four robot-side screws.  Every screw is animated independently and a
short L-key follows the active axis.  No removed inter-layer nuts appear.
"""

import adsk.core
import adsk.fusion
import json
import math
import os


globals().pop("run", None)


TOTAL_FRAME_COUNT = 960
FRAME_START = globals().get("FRAME_START", 0)
FRAME_END = globals().get("FRAME_END", TOTAL_FRAME_COUNT)
FRAME_LIST = globals().get("FRAME_LIST")
FRAME_WIDTH = globals().get("FRAME_WIDTH", 1280)
FRAME_HEIGHT = globals().get("FRAME_HEIGHT", 720)

PACKAGE_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "physical-lite3-mid360-d435i-fusion-adapter-v1"
)
OUTPUT_DIR = os.path.join(PACKAGE_DIR, "frames")
REPORT_DIR = os.path.join(PACKAGE_DIR, "validation", "animation_chunks")

COMPONENT_NAME = "LITE3_MID360_D435I_MONOLITHIC_CARRIER_V1_NOT_OFFICIAL_CAD"
INTERFACE_COMPONENT = "PHYSICAL_INTERFACE_KEEP_OUT_PENDING_MEASUREMENT"

ROBOT_INDEX = 0
S410_INDEX = 3
MID360_INDEX = 4
MID_SCREW_INDICES = (11, 12, 13, 14)
D435_INDEX = 15
D435_SCREW_INDICES = (16, 17)
FRONT_BASE_SCREWS_INDEX = 24
REAR_BASE_SPACERS_INDEX = 25
REAR_BASE_SCREWS_INDEX = 26
S410_SCREW_INDICES = (28, 29, 30, 31)

MOUNT_NORMAL = (0.0, 0.9659258262890683, 0.25881904510252074)
PLATE_UP = (0.0, -0.25881904510252074, 0.9659258262890683)
CAMERA_AXIS = (0.0, -0.34202014332566627, 0.9396926207859093)
CAMERA_UP = (0.0, 0.9396926207859093, 0.34202014332566627)
WIDTH_AXIS = (1.0, 0.0, 0.0)

D435_AXIS_POINTS = {
    16: (-32.697009644681464, 21.835352488197586, 262.0531323590644),
    17: (-28.197009644681464, 21.835352488197586, 262.0531323590644),
}
MID_AXIS_POINTS = {
    11: (-32.24700964468146, 21.452842807920245, 258.6723716491626),
    12: (-28.647009644681464, 21.452842807920245, 258.6723716491626),
    13: (-28.647009644681464, 22.69517422441234, 254.03592768297506),
    14: (-32.24700964468146, 22.69517422441234, 254.03592768297506),
}
S410_AXIS_POINTS = {
    28: (-32.906859573287356, 21.37853880979711, 260.4951592299928),
    29: (-27.987159716075574, 21.37853880979711, 260.4951592299928),
    30: (-32.935037516961955, 23.537893759538793, 252.43633684598146),
    31: (-27.958981772400975, 23.537893759538793, 252.43633684598146),
}
FRONT_BASE_AXIS_POINTS = (
    (-33.697009644681465, 20.168141858307482, 260.68489005808055),
    (-27.197009644681465, 20.168141858307482, 260.68489005808055),
)
REAR_BASE_AXIS_POINTS = (
    (-35.69739294209252, 20.66814185830748, 247.2850190222833),
    (-25.196948718114285, 20.66814185830748, 247.28502596461186),
)

MODULE_INDICES = (
    None,
    D435_INDEX,
    *D435_SCREW_INDICES,
    MID360_INDEX,
    *MID_SCREW_INDICES,
    S410_INDEX,
    *S410_SCREW_INDICES,
)

D435_APPROACH = (48, 107)
D435_SCREW_SCHEDULE = {16: (108, 155), 17: (156, 203)}
MID_APPROACH = (204, 263)
MID_SCREW_SCHEDULE = {
    11: (264, 287),
    13: (288, 311),
    12: (312, 335),
    14: (336, 359),
}
S410_APPROACH = (360, 419)
S410_SCREW_SCHEDULE = {
    28: (420, 443),
    31: (444, 467),
    29: (468, 491),
    30: (492, 515),
}
MODULE_HOLD = (516, 575)
SPACER_SCHEDULE = {0: (576, 599), 1: (600, 623)}
MODULE_TO_ROBOT = (624, 695)
BASE_SCREW_SCHEDULE = {
    ("front", 0): (696, 731),
    ("rear", 1): (732, 767),
    ("front", 1): (768, 803),
    ("rear", 0): (804, 839),
}
FINAL_CLOSE = (840, 887)
GLOBAL_HOLD = (888, 959)


def point(values):
    return adsk.core.Point3D.create(*values)


def vector(values):
    return adsk.core.Vector3D.create(*values)


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def phase(frame, start, end):
    if frame <= start:
        return 0.0
    if frame >= end:
        return 1.0
    return smoothstep((frame - start) / float(end - start))


def lerp(first, second, amount):
    return first + (second - first) * amount


def normalized(values):
    length = math.sqrt(sum(value * value for value in values))
    return tuple(value / length for value in values)


def scaled(values, amount):
    return tuple(value * amount for value in values)


def added(first, second):
    return tuple(first[index] + second[index] for index in range(3))


def cross(first, second):
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
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
    camera.eye = point(added(target, scaled(direction, 60.0)))
    camera.target = point(target)
    camera.upVector = vector(up)
    camera.viewExtents = extents
    viewport.camera = camera


def color_effect(red, green, blue, opacity=1.0):
    diffuse = adsk.core.Color.create(red, green, blue, 255)
    ambient = adsk.core.Color.create(
        min(255, red + 30), min(255, green + 30), min(255, blue + 30), 255
    )
    specular = adsk.core.Color.create(255, 255, 255, 255)
    emissive = adsk.core.Color.create(0, 0, 0, 255)
    return adsk.fusion.CustomGraphicsBasicMaterialColorEffect.create(
        diffuse, ambient, specular, emissive, 24.0, opacity
    )


def component_bodies(component):
    bodies = []
    seen = set()

    def walk(current):
        for body_index in range(current.bRepBodies.count):
            body = current.bRepBodies.item(body_index)
            if body.entityToken not in seen:
                seen.add(body.entityToken)
                bodies.append(body)
        for occurrence_index in range(current.occurrences.count):
            walk(current.occurrences.item(occurrence_index).component)

    walk(component)
    return bodies


def find_occurrence(occurrences, component_name):
    for index in range(occurrences.count):
        occurrence = occurrences.item(index)
        if occurrence.component.name == component_name:
            return index, occurrence
    raise RuntimeError("Missing occurrence " + component_name)


def matrix_from_values(values):
    matrix = adsk.core.Matrix3D.create()
    if not matrix.setWithArray(values):
        raise RuntimeError("Could not set matrix values")
    return matrix


def translation_matrix(offset):
    matrix = adsk.core.Matrix3D.create()
    values = list(matrix.asArray())
    values[3], values[7], values[11] = offset
    if not matrix.setWithArray(values):
        raise RuntimeError("Could not create translation")
    return matrix


def set_offset_occurrence(occurrence, final_values, offset, visible=True):
    values = list(final_values)
    values[3] += offset[0]
    values[7] += offset[1]
    values[11] += offset[2]
    occurrence.transform = matrix_from_values(values)
    occurrence.isLightBulbOn = visible


def rodrigues(axis, angle):
    x, y, z = normalized(axis)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    one_minus = 1.0 - cosine
    return (
        (cosine + x * x * one_minus, x * y * one_minus - z * sine, x * z * one_minus + y * sine),
        (y * x * one_minus + z * sine, cosine + y * y * one_minus, y * z * one_minus - x * sine),
        (z * x * one_minus - y * sine, z * y * one_minus + x * sine, cosine + z * z * one_minus),
    )


def mat_vec(matrix, values):
    return tuple(
        sum(matrix[row][column] * values[column] for column in range(3))
        for row in range(3)
    )


def mat_mul(first, second):
    return tuple(
        tuple(
            sum(first[row][k] * second[k][column] for k in range(3))
            for column in range(3)
        )
        for row in range(3)
    )


def set_rotating_occurrence(
    occurrence,
    final_values,
    visible,
    axis_point,
    axis,
    axial_offset,
    angle,
    module_offset=(0.0, 0.0, 0.0),
):
    final_rotation = tuple(
        tuple(final_values[row * 4 + column] for column in range(3))
        for row in range(3)
    )
    final_translation = (final_values[3], final_values[7], final_values[11])
    rotation = rodrigues(axis, angle)
    rotated_orientation = mat_mul(rotation, final_rotation)
    relative_translation = tuple(
        final_translation[index] - axis_point[index] for index in range(3)
    )
    rotated_relative = mat_vec(rotation, relative_translation)
    translation = tuple(
        axis_point[index]
        + rotated_relative[index]
        + axis[index] * axial_offset
        + module_offset[index]
        for index in range(3)
    )
    values = [0.0] * 16
    for row in range(3):
        for column in range(3):
            values[row * 4 + column] = rotated_orientation[row][column]
    values[3], values[7], values[11] = translation
    values[15] = 1.0
    occurrence.transform = matrix_from_values(values)
    occurrence.isLightBulbOn = visible


def screw_state(frame, begin, end, start_offset):
    if frame < begin:
        return False, start_offset, 0.0
    if frame <= end:
        amount = phase(frame, begin, end)
        return True, start_offset * (1.0 - amount), 8.0 * math.pi * amount
    return True, 0.0, 8.0 * math.pi


def body_center(body):
    bounds = body.boundingBox
    return (
        (bounds.minPoint.x + bounds.maxPoint.x) * 0.5,
        (bounds.minPoint.y + bounds.maxPoint.y) * 0.5,
        (bounds.minPoint.z + bounds.maxPoint.z) * 0.5,
    )


def world_body_copy(temporary, occurrence, body_index=0):
    body = temporary.copy(occurrence.component.bRepBodies.item(body_index))
    if not temporary.transform(body, occurrence.transform2):
        raise RuntimeError("Could not transform graphics body into world space")
    return body


def add_graphic(group, body, color):
    graphic = group.addBRepBody(body)
    if graphic is None:
        raise RuntimeError("Could not add graphics body")
    graphic.color = color
    graphic.isSelectable = False
    return graphic


def create_graphics(root, temporary, interface, front_screws, rear_spacers, rear_screws):
    group = root.customGraphicsGroups.add()
    group.id = "PHYSICAL_LITE3_FUSION_ADAPTER_V1_INSTALLATION_ANIMATION"
    group.isSelectable = False
    graphics = {
        "interface": [],
        "front_screws": [],
        "rear_spacers": [],
        "rear_screws": [],
        "tool": [],
    }
    graphics["interface"].append(
        add_graphic(
            group,
            world_body_copy(temporary, interface),
            color_effect(242, 242, 238, 1.0),
        )
    )
    for body_index in range(front_screws.component.bRepBodies.count):
        graphics["front_screws"].append(
            add_graphic(
                group,
                world_body_copy(temporary, front_screws, body_index),
                color_effect(242, 134, 35, 1.0),
            )
        )
    for body_index in range(rear_spacers.component.bRepBodies.count):
        graphics["rear_spacers"].append(
            add_graphic(
                group,
                world_body_copy(temporary, rear_spacers, body_index),
                color_effect(242, 198, 48, 1.0),
            )
        )
    for body_index in range(rear_screws.component.bRepBodies.count):
        graphics["rear_screws"].append(
            add_graphic(
                group,
                world_body_copy(temporary, rear_screws, body_index),
                color_effect(242, 134, 35, 1.0),
            )
        )
    tool_shaft = temporary.createCylinderOrCone(
        point((0.0, 0.0, 0.0)), 0.08, point((0.0, 3.2, 0.0)), 0.08
    )
    tool_handle = temporary.createCylinderOrCone(
        point((0.0, 3.2, 0.0)), 0.08, point((1.5, 3.2, 0.0)), 0.08
    )
    for tool_body in (tool_shaft, tool_handle):
        graphics["tool"].append(
            add_graphic(group, tool_body, color_effect(36, 145, 240, 1.0))
        )
    return group, graphics


def set_graphics_visible(items, visible):
    for item in items:
        item.isVisible = visible


def axis_graphic_transform(axis_point, axis, angle, axial_offset):
    matrix = adsk.core.Matrix3D.create()
    matrix.setToRotation(angle, vector(axis), point(axis_point))
    values = list(matrix.asArray())
    values[3] += axis[0] * axial_offset
    values[7] += axis[1] * axial_offset
    values[11] += axis[2] * axial_offset
    if not matrix.setWithArray(values):
        raise RuntimeError("Could not create axis graphics transform")
    return matrix


def tool_transform(axis_point, outward_axis, angle, screw_offset):
    y_axis = normalized(outward_axis)
    reference = (0.0, 0.0, 1.0)
    if abs(sum(y_axis[index] * reference[index] for index in range(3))) > 0.92:
        reference = (1.0, 0.0, 0.0)
    x_axis = normalized(cross(y_axis, reference))
    z_axis = normalized(cross(x_axis, y_axis))
    spin = rodrigues(y_axis, angle)
    x_axis = mat_vec(spin, x_axis)
    z_axis = mat_vec(spin, z_axis)
    origin = added(axis_point, scaled(normalized(outward_axis), abs(screw_offset)))
    values = [
        x_axis[0], y_axis[0], z_axis[0], origin[0],
        x_axis[1], y_axis[1], z_axis[1], origin[1],
        x_axis[2], y_axis[2], z_axis[2], origin[2],
        0.0, 0.0, 0.0, 1.0,
    ]
    return matrix_from_values(values)


def active_actual_screw(frame):
    for index, (begin, end) in D435_SCREW_SCHEDULE.items():
        if begin <= frame <= end:
            return index, D435_AXIS_POINTS[index], CAMERA_AXIS, -2.0, begin, end
    for index, (begin, end) in MID_SCREW_SCHEDULE.items():
        if begin <= frame <= end:
            return index, MID_AXIS_POINTS[index], MOUNT_NORMAL, -2.2, begin, end
    for index, (begin, end) in S410_SCREW_SCHEDULE.items():
        if begin <= frame <= end:
            return index, S410_AXIS_POINTS[index], MOUNT_NORMAL, 1.8, begin, end
    return None


def active_base_screw(frame):
    for key, (begin, end) in BASE_SCREW_SCHEDULE.items():
        if begin <= frame <= end:
            return key, begin, end
    return None


def module_offset(frame):
    if frame < SPACER_SCHEDULE[0][0]:
        return (0.0, 0.0, 0.0)
    if frame < MODULE_TO_ROBOT[0]:
        return (0.0, 10.0, 0.0)
    if frame <= MODULE_TO_ROBOT[1]:
        return (0.0, 10.0 * (1.0 - phase(frame, *MODULE_TO_ROBOT)), 0.0)
    return (0.0, 0.0, 0.0)


def set_tool_for_actual_screw(graphics, frame, active):
    if active is None:
        set_graphics_visible(graphics["tool"], False)
        return
    _index, axis_point, axis, start_offset, begin, end = active
    visible, offset, angle = screw_state(frame, begin, end, start_offset)
    outward = scaled(axis, 1.0 if start_offset >= 0.0 else -1.0)
    transform = tool_transform(axis_point, outward, angle, offset)
    for item in graphics["tool"]:
        item.isVisible = visible and frame >= begin + 8
        item.transform = transform


def set_tool_for_base_screw(graphics, frame, active):
    if active is None:
        set_graphics_visible(graphics["tool"], False)
        return
    (group_name, body_index), begin, end = active
    axis_point = (
        FRONT_BASE_AXIS_POINTS[body_index]
        if group_name == "front"
        else REAR_BASE_AXIS_POINTS[body_index]
    )
    _visible, offset, angle = screw_state(frame, begin, end, 2.0)
    transform = tool_transform(axis_point, (0.0, 1.0, 0.0), angle, offset)
    for item in graphics["tool"]:
        item.isVisible = frame >= begin + 8
        item.transform = transform


def set_scene_state(
    occurrences,
    carrier_index,
    interface_index,
    final_transforms,
    opacity_records,
    graphics,
    frame,
):
    for index in range(occurrences.count):
        occurrences.item(index).isLightBulbOn = False
    for body, opacity in opacity_records:
        body.opacity = opacity

    carrier = occurrences.item(carrier_index)
    d435 = occurrences.item(D435_INDEX)
    mid360 = occurrences.item(MID360_INDEX)
    s410 = occurrences.item(S410_INDEX)
    offset = module_offset(frame)

    if frame < SPACER_SCHEDULE[0][0]:
        set_offset_occurrence(carrier, final_transforms[carrier_index], (0.0, 0.0, 0.0), True)
    else:
        set_offset_occurrence(carrier, final_transforms[carrier_index], offset, True)

    d435_amount = phase(frame, *D435_APPROACH)
    d435_offset = scaled(CAMERA_AXIS, 4.5 * (1.0 - d435_amount))
    d435_visible = frame >= D435_APPROACH[0]
    if frame >= SPACER_SCHEDULE[0][0]:
        d435_offset = offset
    set_offset_occurrence(d435, final_transforms[D435_INDEX], d435_offset, d435_visible)

    mid_amount = phase(frame, *MID_APPROACH)
    mid_offset = scaled(MOUNT_NORMAL, 5.5 * (1.0 - mid_amount))
    mid_visible = frame >= MID_APPROACH[0]
    if frame >= SPACER_SCHEDULE[0][0]:
        mid_offset = offset
    set_offset_occurrence(mid360, final_transforms[MID360_INDEX], mid_offset, mid_visible)

    guard_amount = phase(frame, *S410_APPROACH)
    guard_offset = scaled(MOUNT_NORMAL, 6.0 * (1.0 - guard_amount))
    guard_visible = frame >= S410_APPROACH[0]
    if frame >= SPACER_SCHEDULE[0][0]:
        guard_offset = offset
    set_offset_occurrence(s410, final_transforms[S410_INDEX], guard_offset, guard_visible)

    for index, schedule in D435_SCREW_SCHEDULE.items():
        begin, end = schedule
        visible, screw_offset, angle = screw_state(frame, begin, end, -2.0)
        module_shift = offset if frame >= SPACER_SCHEDULE[0][0] else (0.0, 0.0, 0.0)
        set_rotating_occurrence(
            occurrences.item(index), final_transforms[index], visible,
            D435_AXIS_POINTS[index], CAMERA_AXIS, screw_offset, angle, module_shift
        )
    for index, schedule in MID_SCREW_SCHEDULE.items():
        begin, end = schedule
        visible, screw_offset, angle = screw_state(frame, begin, end, -2.2)
        module_shift = offset if frame >= SPACER_SCHEDULE[0][0] else (0.0, 0.0, 0.0)
        set_rotating_occurrence(
            occurrences.item(index), final_transforms[index], visible,
            MID_AXIS_POINTS[index], MOUNT_NORMAL, screw_offset, angle, module_shift
        )
    for index, schedule in S410_SCREW_SCHEDULE.items():
        begin, end = schedule
        visible, screw_offset, angle = screw_state(frame, begin, end, 1.8)
        module_shift = offset if frame >= SPACER_SCHEDULE[0][0] else (0.0, 0.0, 0.0)
        set_rotating_occurrence(
            occurrences.item(index), final_transforms[index], visible,
            S410_AXIS_POINTS[index], MOUNT_NORMAL, screw_offset, angle, module_shift
        )

    robot_visible = frame >= SPACER_SCHEDULE[0][0]
    occurrences.item(ROBOT_INDEX).isLightBulbOn = robot_visible
    occurrences.item(interface_index).isLightBulbOn = False
    set_graphics_visible(graphics["interface"], robot_visible)

    for spacer_index, item in enumerate(graphics["rear_spacers"]):
        begin, end = SPACER_SCHEDULE[spacer_index]
        if frame < begin:
            item.isVisible = False
        else:
            spacer_offset = 3.0 * (1.0 - phase(frame, begin, end))
            item.isVisible = True
            item.transform = translation_matrix((0.0, spacer_offset, 0.0))

    set_graphics_visible(graphics["front_screws"], False)
    set_graphics_visible(graphics["rear_screws"], False)
    for key, (begin, end) in BASE_SCREW_SCHEDULE.items():
        group_name, body_index = key
        items = graphics["front_screws"] if group_name == "front" else graphics["rear_screws"]
        item = items[body_index]
        visible, screw_offset, angle = screw_state(frame, begin, end, 2.0)
        axis_point = FRONT_BASE_AXIS_POINTS[body_index] if group_name == "front" else REAR_BASE_AXIS_POINTS[body_index]
        item.isVisible = visible
        item.transform = axis_graphic_transform(axis_point, (0.0, -1.0, 0.0), angle, -screw_offset)

    actual_active = active_actual_screw(frame)
    base_active = active_base_screw(frame)
    if actual_active is not None:
        set_tool_for_actual_screw(graphics, frame, actual_active)
    elif base_active is not None:
        set_tool_for_base_screw(graphics, frame, base_active)
    else:
        set_graphics_visible(graphics["tool"], False)

    if actual_active is not None:
        active_index = actual_active[0]
        for body in component_bodies(carrier.component):
            body.opacity = 0.42
        if active_index in D435_SCREW_INDICES:
            for body in component_bodies(d435.component):
                body.opacity = 0.30
        elif active_index in MID_SCREW_INDICES:
            for body in component_bodies(mid360.component):
                body.opacity = 0.26
        else:
            for body in component_bodies(s410.component):
                body.opacity = 0.30


def screw_camera(viewport, axis_point, axis, side, up):
    target = added(axis_point, scaled(axis, -0.55))
    direction = added(scaled(axis, -1.0), added(scaled(WIDTH_AXIS, side * 0.78), scaled(up, 0.24)))
    apply_camera(viewport, target, direction, 5.7, up)


def set_scene_camera(viewport, frame):
    active = active_actual_screw(frame)
    if active is not None:
        index, axis_point, axis, start_offset, _begin, _end = active
        side = -1.0 if axis_point[0] < -30.447 else 1.0
        up = CAMERA_UP if index in D435_SCREW_INDICES else PLATE_UP
        screw_camera(viewport, axis_point, axis, side, up)
        return
    base_active = active_base_screw(frame)
    if base_active is not None:
        (group_name, body_index), _begin, _end = base_active
        axis_point = FRONT_BASE_AXIS_POINTS[body_index] if group_name == "front" else REAR_BASE_AXIS_POINTS[body_index]
        side = -1.0 if axis_point[0] < -30.447 else 1.0
        apply_camera(
            viewport,
            axis_point,
            (side * 0.78, 1.0, 0.52 if group_name == "front" else -0.46),
            7.2,
            up=(0.0, 0.0, 1.0),
        )
        return
    if frame < D435_APPROACH[0]:
        apply_camera(viewport, (-30.447, 21.7, 254.5), (0.80, 0.72, -0.62), 18.5, up=(0.0, 0.0, 1.0))
    elif frame < MID_APPROACH[0]:
        apply_camera(viewport, (-30.447, 21.5, 260.5), (0.74, 0.72, 0.48), 15.0, up=CAMERA_UP)
    elif frame < S410_APPROACH[0]:
        apply_camera(viewport, (-30.447, 22.4, 256.2), (0.72, 0.92, -0.36), 17.0, up=PLATE_UP)
    elif frame < MODULE_HOLD[0]:
        apply_camera(viewport, (-30.447, 22.5, 256.0), (0.78, 0.88, -0.30), 20.0, up=PLATE_UP)
    elif frame < SPACER_SCHEDULE[0][0]:
        apply_camera(viewport, (-30.447, 22.4, 256.0), (0.78, 0.88, -0.30), 22.0, up=PLATE_UP)
    elif frame < MODULE_TO_ROBOT[0]:
        apply_camera(viewport, (-30.447, 20.8, 248.0), (0.76, 1.0, -0.52), 15.0, up=(0.0, 0.0, 1.0))
    elif frame <= MODULE_TO_ROBOT[1]:
        apply_camera(viewport, (-30.447, 18.0, 250.0), (0.72, 0.90, 0.42), 44.0, up=(0.0, 1.0, 0.0))
    elif frame < FINAL_CLOSE[0]:
        apply_camera(viewport, (-30.447, 20.8, 254.0), (0.66, 1.0, 0.42), 20.0, up=(0.0, 0.0, 1.0))
    elif frame < GLOBAL_HOLD[0]:
        apply_camera(viewport, (-30.447, 20.8, 255.0), (0.72, 0.92, 0.38), 28.0, up=(0.0, 1.0, 0.0))
    else:
        apply_camera(viewport, (-30.447, 0.0, 246.0), (0.82, 0.72, 0.56), 74.0, up=(0.0, 1.0, 0.0))


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences
    temporary = adsk.fusion.TemporaryBRepManager.get()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)

    carrier_index, carrier = find_occurrence(occurrences, COMPONENT_NAME)
    interface_index, interface = find_occurrence(occurrences, INTERFACE_COMPONENT)
    front_screws = occurrences.item(FRONT_BASE_SCREWS_INDEX)
    rear_spacers = occurrences.item(REAR_BASE_SPACERS_INDEX)
    rear_screws = occurrences.item(REAR_BASE_SCREWS_INDEX)

    final_transforms = {
        index: list(occurrences.item(index).transform.asArray())
        for index in range(occurrences.count)
    }
    final_visibility = [
        bool(occurrences.item(index).isLightBulbOn)
        for index in range(occurrences.count)
    ]
    opacity_records = []
    for index in (carrier_index, D435_INDEX, MID360_INDEX, S410_INDEX):
        for body in component_bodies(occurrences.item(index).component):
            opacity_records.append((body, body.opacity))
    viewport = application.activeViewport
    original_camera = camera_state(viewport.camera)
    original_graphics_count = root.customGraphicsGroups.count
    graphics_group, graphics = create_graphics(
        root, temporary, interface, front_screws, rear_spacers, rear_screws
    )
    frames = FRAME_LIST if FRAME_LIST is not None else range(FRAME_START, FRAME_END)
    rendered = []
    graphics_removed = False
    try:
        for frame in frames:
            set_scene_state(
                occurrences,
                carrier_index,
                interface_index,
                final_transforms,
                opacity_records,
                graphics,
                frame,
            )
            set_scene_camera(viewport, frame)
            viewport.refresh()
            adsk.doEvents()
            path = os.path.join(OUTPUT_DIR, "frame_%04d.png" % frame)
            if not viewport.saveAsImageFile(path, FRAME_WIDTH, FRAME_HEIGHT):
                raise RuntimeError("Could not render " + path)
            rendered.append(frame)
    finally:
        for index in range(occurrences.count):
            occurrences.item(index).transform = matrix_from_values(final_transforms[index])
            occurrences.item(index).isLightBulbOn = final_visibility[index]
        for body, opacity in opacity_records:
            body.opacity = opacity
        if graphics_group is not None and graphics_group.isValid:
            graphics_removed = bool(graphics_group.deleteMe())
        restore_camera(viewport, original_camera)
        viewport.refresh()
        adsk.doEvents()

    maximum_transform_difference = 0.0
    visibility_mismatches = []
    for index in range(occurrences.count):
        actual = list(occurrences.item(index).transform.asArray())
        expected = final_transforms[index]
        maximum_transform_difference = max(
            maximum_transform_difference,
            max(abs(actual[item] - expected[item]) for item in range(16)),
        )
        if bool(occurrences.item(index).isLightBulbOn) != final_visibility[index]:
            visibility_mismatches.append(index)
    report = {
        "status": "historical_v1_animation_chunk_rejected_for_current_pro_robot_sequence",
        "stage": "experiment_and_analysis",
        "frame_start": min(rendered) if rendered else None,
        "frame_end_inclusive": max(rendered) if rendered else None,
        "frames_rendered": len(rendered),
        "total_frame_count": TOTAL_FRAME_COUNT,
        "output_dir": OUTPUT_DIR,
        "contains_text_overlay": False,
        "sequence": {
            "carrier_only": [0, 47],
            "d435i_approach": list(D435_APPROACH),
            "d435i_two_direct_screws": D435_SCREW_SCHEDULE,
            "mid360_approach": list(MID_APPROACH),
            "mid360_four_underside_screws_cross_order": MID_SCREW_SCHEDULE,
            "s410_approach": list(S410_APPROACH),
            "s410_four_direct_screws_cross_order": S410_SCREW_SCHEDULE,
            "rear_spacers": SPACER_SCHEDULE,
            "complete_module_to_lite3": list(MODULE_TO_ROBOT),
            "four_robot_side_screws_cross_order": {str(key): value for key, value in BASE_SCREW_SCHEDULE.items()},
            "global_hold": list(GLOBAL_HOLD),
            "removed_inter_layer_fasteners": 0,
            "nuts": 0,
        },
        "restoration": {
            "maximum_transform_difference": maximum_transform_difference,
            "visibility_mismatches": visibility_mismatches,
            "custom_graphics_removed": graphics_removed,
            "custom_graphics_count_before": original_graphics_count,
            "custom_graphics_count_after": root.customGraphicsGroups.count,
            "pending_snapshot": bool(design.snapshots.hasPendingSnapshot),
        },
    }
    report["pass"] = bool(
        rendered
        and maximum_transform_difference <= 1.0e-9
        and not visibility_mismatches
        and graphics_removed
        and root.customGraphicsGroups.count == original_graphics_count
        and all(
            os.path.exists(os.path.join(OUTPUT_DIR, "frame_%04d.png" % frame))
            for frame in rendered
        )
    )
    report_path = os.path.join(
        REPORT_DIR,
        "chunk_%04d_%04d.json" % (report["frame_start"], report["frame_end_inclusive"]),
    )
    with open(report_path, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False))
    if not report["pass"]:
        raise RuntimeError("Animation chunk validation failed")
