"""Render the corrected S410/J20A and J20A/J17A fastening logic.

The accepted J17A/D435i first layer and accepted J20A/MID360 upper
subassembly begin separated. S410 is attached directly to J20A with the four
source-backed M5 axes. The complete guarded upper subassembly then seats on
J17A. Two short M3 and two short M4 display-model screw candidates enter from
the J17A head-seat side and terminate inside J20A's modeled threaded receiver
material. No far-side nut, washer, or long through-bolt is shown.

The M3x6 and M4x10 lengths and socket-head forms are visualization candidates,
chosen only to demonstrate the source-CAD path. Exact supplied hardware,
usable thread engagement, torque, strength, and service procedure remain
unresolved. The short direct-thread screws are transient custom graphics; the
Fusion design is restored without adding persistent occurrences.
"""

import adsk.core
import adsk.fusion
import json
import math
import os


FRAME_START = globals().get("FRAME_START", 0)
FRAME_END = globals().get("FRAME_END", 480)
FRAME_LIST = globals().get("FRAME_LIST")
FRAME_WIDTH = globals().get("FRAME_WIDTH", 1280)
FRAME_HEIGHT = globals().get("FRAME_HEIGHT", 720)

EVIDENCE_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-installation-restart-03b-correct-direct-thread"
)
OUTPUT_DIR = os.path.join(EVIDENCE_DIR, "frames")
REPORT_PATH = os.path.join(EVIDENCE_DIR, "render_report.json")

J17A_INDEX = 1
J20A_INDEX = 2
S410_INDEX = 3
MID360_INDEX = 4
MID360_SCREW_INDICES = (11, 12, 13, 14)
D435I_INDEX = 15
D435I_SCREW_INDICES = (16, 17)
S410_SCREW_INDICES = (28, 29, 30, 31)
SHORT_L_KEY_INDEX = 33

# The rejected long layer bolts, nuts, washers, and locknuts are deliberately
# absent from every frame: 7-10 and 18-23.
PERSISTENT_VISIBLE_INDICES = (
    J17A_INDEX,
    J20A_INDEX,
    S410_INDEX,
    MID360_INDEX,
    *MID360_SCREW_INDICES,
    D435I_INDEX,
    *D435I_SCREW_INDICES,
    *S410_SCREW_INDICES,
)

MOUNT_NORMAL = (0.0, 0.9659258262890683, 0.25881904510252074)
PLATE_UP = (0.0, -0.25881904510252074, 0.9659258262890683)
WIDTH_AXIS = (1.0, 0.0, 0.0)
LAYER_AXIS = (0.0, 1.0, 0.0)
UPPER_SEPARATION = (0.0, 8.0, 0.0)

S410_SCREW_SEATS = {
    28: (-32.906859573287356, 21.37853880979711, 260.4951592299928),
    29: (-27.987159716075574, 21.37853880979711, 260.4951592299928),
    30: (-32.935037516961955, 23.537893759538793, 252.43633684598146),
    31: (-27.958981772400975, 23.537893759538793, 252.43633684598146),
}

S410_SCREW_SCHEDULES = {
    28: {"start": (80, 95), "tighten": (144, 159)},
    31: {"start": (96, 111), "tighten": (160, 175)},
    29: {"start": (112, 127), "tighten": (176, 191)},
    30: {"start": (128, 143), "tighten": (192, 207)},
}

S410_TOOL_ANGLE_RANGES_DEG = {
    28: (240.0, 330.0),
    31: (60.0, 150.0),
    29: (210.0, 300.0),
    30: (30.0, 120.0),
}

# Values are in Fusion's internal centimeters. The bearing point is the
# shaft/head junction on the J17A head-seat side. Each shaft points +Y into
# the corresponding J20A modeled threaded receiver.
DIRECT_SCREW_SPECS = {
    "front_left_m3": {
        "nominal": "M3x6 visual candidate",
        "bearing": (-32.24700964468146, 20.468141858307484, 259.73489005808057),
        "shaft_radius": 0.15,
        "shaft_length": 0.60,
        "head_radius": 0.275,
        "head_height": 0.30,
        "j17_clearance_diameter_mm": 3.5,
        "j20_modeled_receiver_diameter_mm": 2.5,
        "j17_traversal_mm": 2.5,
        "modeled_j20_engagement_mm": 3.5,
        "schedule": (248, 283),
        "width_sign": -1.0,
    },
    "front_right_m3": {
        "nominal": "M3x6 visual candidate",
        "bearing": (-28.647009644681464, 20.468141858307484, 259.73489005808057),
        "shaft_radius": 0.15,
        "shaft_length": 0.60,
        "head_radius": 0.275,
        "head_height": 0.30,
        "j17_clearance_diameter_mm": 3.5,
        "j20_modeled_receiver_diameter_mm": 2.5,
        "j17_traversal_mm": 2.5,
        "modeled_j20_engagement_mm": 3.5,
        "schedule": (284, 319),
        "width_sign": 1.0,
    },
    "rear_left_m4": {
        "nominal": "M4x10 visual candidate",
        "bearing": (-33.84112221937691, 22.018141858307482, 251.89077750838507),
        "shaft_radius": 0.20,
        "shaft_length": 1.00,
        "head_radius": 0.35,
        "head_height": 0.40,
        "j17_counterbore_diameter_mm": 8.0,
        "j17_clearance_diameter_mm": 4.5,
        "j20_modeled_receiver_diameter_mm": 3.3,
        "j17_traversal_mm": 3.0,
        "modeled_j20_engagement_mm": 7.0,
        "schedule": (320, 355),
        "width_sign": -1.0,
    },
    "rear_right_m4": {
        "nominal": "M4x10 visual candidate",
        "bearing": (-27.05289706998607, 22.018141858307482, 251.89077750838507),
        "shaft_radius": 0.20,
        "shaft_length": 1.00,
        "head_radius": 0.35,
        "head_height": 0.40,
        "j17_counterbore_diameter_mm": 8.0,
        "j17_clearance_diameter_mm": 4.5,
        "j20_modeled_receiver_diameter_mm": 3.3,
        "j17_traversal_mm": 3.0,
        "modeled_j20_engagement_mm": 7.0,
        "schedule": (356, 391),
        "width_sign": 1.0,
    },
}


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


def normalized(vector):
    length = math.sqrt(sum(value * value for value in vector))
    return tuple(value / length for value in vector)


def scaled(vector, amount):
    return tuple(value * amount for value in vector)


def shifted(first, second):
    return tuple(first[index] + second[index] for index in range(3))


def point(values):
    return adsk.core.Point3D.create(*values)


def vector(values):
    return adsk.core.Vector3D.create(*values)


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


def apply_camera(viewport, target, direction, extents, up=(0.0, 0.0, 1.0)):
    direction = normalized(direction)
    eye = shifted(target, scaled(direction, 36.0))
    camera = viewport.camera
    camera.isSmoothTransition = False
    camera.cameraType = adsk.core.CameraTypes.OrthographicCameraType
    camera.eye = point(eye)
    camera.target = point(target)
    camera.upVector = vector(up)
    camera.viewExtents = extents
    viewport.camera = camera


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


def matrix_from_values(values):
    matrix = adsk.core.Matrix3D.create()
    if not matrix.setWithArray(values):
        raise RuntimeError("Could not set transform matrix")
    return matrix


def set_offset_occurrence(occurrence, final_values, visible, offset):
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
        (
            cosine + x * x * one_minus,
            x * y * one_minus - z * sine,
            x * z * one_minus + y * sine,
        ),
        (
            y * x * one_minus + z * sine,
            cosine + y * y * one_minus,
            y * z * one_minus - x * sine,
        ),
        (
            z * x * one_minus - y * sine,
            z * y * one_minus + x * sine,
            cosine + z * z * one_minus,
        ),
    )


def rigid_axis_transform(axis, axis_point, axial_offset, angle):
    rotation = rodrigues(axis, angle)
    rotated_point = tuple(
        sum(rotation[row][column] * axis_point[column] for column in range(3))
        for row in range(3)
    )
    translation = tuple(
        axis_point[index]
        - rotated_point[index]
        + axis[index] * axial_offset
        for index in range(3)
    )
    values = [0.0] * 16
    for row in range(3):
        for column in range(3):
            values[row * 4 + column] = rotation[row][column]
    values[3], values[7], values[11] = translation
    values[15] = 1.0
    return matrix_from_values(values)


def color_effect(red, green, blue, opacity=1.0):
    diffuse = adsk.core.Color.create(red, green, blue, 255)
    ambient = adsk.core.Color.create(
        min(255, red + 24), min(255, green + 24), min(255, blue + 24), 255
    )
    specular = adsk.core.Color.create(255, 255, 255, 255)
    emissive = adsk.core.Color.create(0, 0, 0, 255)
    return adsk.fusion.CustomGraphicsBasicMaterialColorEffect.create(
        diffuse, ambient, specular, emissive, 18.0, opacity
    )


def solid_color_effect(red, green, blue):
    return adsk.fusion.CustomGraphicsSolidColorEffect.create(
        adsk.core.Color.create(red, green, blue, 255)
    )


def add_direct_screw_graphics(parent_group, name, spec, temporary):
    screw_group = parent_group.addGroup()
    screw_group.id = name
    screw_group.isSelectable = False
    bearing = spec["bearing"]
    shaft_end = shifted(bearing, scaled(LAYER_AXIS, spec["shaft_length"]))
    head_outer = shifted(bearing, scaled(LAYER_AXIS, -spec["head_height"]))
    shaft_body = temporary.createCylinderOrCone(
        point(bearing), spec["shaft_radius"], point(shaft_end), spec["shaft_radius"]
    )
    head_body = temporary.createCylinderOrCone(
        point(head_outer), spec["head_radius"], point(bearing), spec["head_radius"]
    )
    shaft_graphic = screw_group.addBRepBody(shaft_body)
    head_graphic = screw_group.addBRepBody(head_body)
    if shaft_graphic is None or head_graphic is None:
        raise RuntimeError("Could not create direct-thread custom screw " + name)
    screw_color = color_effect(236, 160, 35)
    shaft_graphic.color = screw_color
    head_graphic.color = screw_color
    shaft_graphic.isSelectable = False
    head_graphic.isSelectable = False

    # A dark asymmetric line on the socket-head face makes rotation visible.
    marker_center = head_outer
    marker_half = spec["head_radius"] * 0.64
    marker_coordinates = adsk.fusion.CustomGraphicsCoordinates.create(
        [
            marker_center[0] - marker_half,
            marker_center[1] - 0.003,
            marker_center[2],
            marker_center[0] + marker_half,
            marker_center[1] - 0.003,
            marker_center[2],
        ]
    )
    marker = screw_group.addLines(marker_coordinates, [], False)
    if marker is None:
        raise RuntimeError("Could not create screw rotation marker " + name)
    marker.color = solid_color_effect(70, 46, 12)
    marker.weight = 4.0
    marker.depthPriority = 10
    marker.isSelectable = False
    screw_group.isVisible = False
    return screw_group


def add_ring_group(parent_group, name, ring_specs, red, green, blue):
    group = parent_group.addGroup()
    group.id = name
    group.isSelectable = False
    effect = solid_color_effect(red, green, blue)
    for center, radius in ring_specs:
        circle = adsk.core.Circle3D.createByCenter(point(center), vector(LAYER_AXIS), radius)
        curve = group.addCurve(circle)
        if curve is None:
            raise RuntimeError("Could not create alignment ring " + name)
        curve.color = effect
        curve.weight = 5.0
        curve.depthPriority = 12
        curve.isSelectable = False
    group.isVisible = False
    return group


def create_custom_graphics(root):
    before_count = root.customGraphicsGroups.count
    parent = root.customGraphicsGroups.add()
    if parent is None:
        raise RuntimeError("Could not create transient custom graphics group")
    parent.id = "CORRECT_DIRECT_THREAD_ANIMATION_TRANSIENT"
    parent.isSelectable = False
    temporary = adsk.fusion.TemporaryBRepManager.get()
    screws = {
        name: add_direct_screw_graphics(parent, name, spec, temporary)
        for name, spec in DIRECT_SCREW_SPECS.items()
    }
    j17_rings = add_ring_group(
        parent,
        "J17A_CLEARANCE_AND_HEAD_SEAT_RINGS",
        [
            (DIRECT_SCREW_SPECS["front_left_m3"]["bearing"], 0.23),
            (DIRECT_SCREW_SPECS["front_right_m3"]["bearing"], 0.23),
            (DIRECT_SCREW_SPECS["rear_left_m4"]["bearing"], 0.37),
            (DIRECT_SCREW_SPECS["rear_right_m4"]["bearing"], 0.37),
        ],
        245,
        196,
        32,
    )
    j20_rings = add_ring_group(
        parent,
        "J20A_THREADED_RECEIVER_RINGS",
        [
            ((-32.24700964468146, 20.718141858307484, 259.73489005808057), 0.17),
            ((-28.647009644681464, 20.718141858307484, 259.73489005808057), 0.17),
            ((-33.84112221937691, 22.318141858307482, 251.89077750838507), 0.22),
            ((-27.05289706998607, 22.318141858307482, 251.89077750838507), 0.22),
        ],
        44,
        128,
        240,
    )
    return {
        "parent": parent,
        "before_count": before_count,
        "screws": screws,
        "j17_rings": j17_rings,
        "j20_rings": j20_rings,
    }


def upper_offset(frame):
    if frame < 208:
        return UPPER_SEPARATION
    if frame <= 247:
        return scaled(UPPER_SEPARATION, 1.0 - phase(frame, 208, 247))
    return (0.0, 0.0, 0.0)


def s410_screw_state(frame, screw_index):
    schedule = S410_SCREW_SCHEDULES[screw_index]
    start_begin, start_end = schedule["start"]
    tighten_begin, tighten_end = schedule["tighten"]
    angle_begin_deg, angle_end_deg = S410_TOOL_ANGLE_RANGES_DEG[screw_index]
    angle_begin = math.radians(angle_begin_deg)
    angle_end = math.radians(angle_end_deg)
    if frame < start_begin:
        return False, 0.8, angle_begin
    if frame <= start_end:
        amount = phase(frame, start_begin, start_end)
        return True, lerp(0.8, 0.35, amount), lerp(angle_begin, angle_end, amount)
    if frame < tighten_begin:
        return True, 0.35, angle_end
    if frame <= tighten_end:
        amount = phase(frame, tighten_begin, tighten_end)
        return True, 0.35 * (1.0 - amount), lerp(angle_begin, angle_end, amount)
    return True, 0.0, angle_end


def active_s410_screw(frame):
    for screw_index, schedule in S410_SCREW_SCHEDULES.items():
        for begin, end in (schedule["start"], schedule["tighten"]):
            if begin <= frame <= end:
                visible, offset, angle = s410_screw_state(frame, screw_index)
                return screw_index, offset, angle
    return None


def set_rotating_occurrence(
    occurrence,
    final_values,
    visible,
    axis,
    axis_point,
    axial_offset,
    angle,
    assembly_offset,
):
    final_rotation = tuple(
        tuple(final_values[row * 4 + column] for column in range(3))
        for row in range(3)
    )
    final_translation = (final_values[3], final_values[7], final_values[11])
    rotation = rodrigues(axis, angle)
    rotated_orientation = tuple(
        tuple(
            sum(rotation[row][k] * final_rotation[k][column] for k in range(3))
            for column in range(3)
        )
        for row in range(3)
    )
    relative_translation = tuple(
        final_translation[index] - axis_point[index] for index in range(3)
    )
    rotated_relative = tuple(
        sum(rotation[row][column] * relative_translation[column] for column in range(3))
        for row in range(3)
    )
    translation = tuple(
        axis_point[index]
        + rotated_relative[index]
        + axis[index] * axial_offset
        + assembly_offset[index]
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


def set_short_l_key(occurrence, active, final_transforms, assembly_offset):
    if active is None:
        occurrence.isLightBulbOn = False
        return
    screw_index, insertion_offset, angle = active
    screw_values = final_transforms[screw_index]
    rotation = rodrigues(MOUNT_NORMAL, angle)
    values = [0.0] * 16
    for row in range(3):
        for column in range(3):
            values[row * 4 + column] = rotation[row][column]
    values[3] = screw_values[3] + assembly_offset[0] + MOUNT_NORMAL[0] * insertion_offset
    values[7] = screw_values[7] + assembly_offset[1] + MOUNT_NORMAL[1] * insertion_offset
    values[11] = screw_values[11] + assembly_offset[2] + MOUNT_NORMAL[2] * insertion_offset
    values[15] = 1.0
    occurrence.transform = matrix_from_values(values)
    occurrence.isLightBulbOn = True


def direct_screw_state(frame, spec):
    begin, end = spec["schedule"]
    if frame < begin:
        return False, -3.0, 0.0
    if frame <= end:
        amount = phase(frame, begin, end)
        return True, -3.0 * (1.0 - amount), 12.0 * math.pi * amount
    return True, 0.0, 12.0 * math.pi


def set_opacity_for_component(occurrences, index, opacity):
    for body in component_bodies(occurrences.item(index).component):
        body.opacity = opacity


def set_scene_state(occurrences, final_transforms, frame, opacity_records, graphics):
    for occurrence_index in range(occurrences.count):
        occurrences.item(occurrence_index).isLightBulbOn = False

    for index in (J17A_INDEX, D435I_INDEX, *D435I_SCREW_INDICES):
        set_offset_occurrence(
            occurrences.item(index), final_transforms[index], True, (0.0, 0.0, 0.0)
        )

    current_upper_offset = upper_offset(frame)
    for index in (J20A_INDEX, MID360_INDEX, *MID360_SCREW_INDICES):
        set_offset_occurrence(
            occurrences.item(index), final_transforms[index], True, current_upper_offset
        )

    guard_amount = phase(frame, 24, 71)
    guard_offset = shifted(
        current_upper_offset, scaled(MOUNT_NORMAL, 5.5 * (1.0 - guard_amount))
    )
    set_offset_occurrence(
        occurrences.item(S410_INDEX),
        final_transforms[S410_INDEX],
        frame >= 24,
        guard_offset,
    )

    for index in S410_SCREW_INDICES:
        visible, insertion_offset, angle = s410_screw_state(frame, index)
        set_rotating_occurrence(
            occurrences.item(index),
            final_transforms[index],
            visible,
            MOUNT_NORMAL,
            S410_SCREW_SEATS[index],
            insertion_offset,
            angle,
            current_upper_offset,
        )

    set_short_l_key(
        occurrences.item(SHORT_L_KEY_INDEX),
        active_s410_screw(frame),
        final_transforms,
        current_upper_offset,
    )

    for name, spec in DIRECT_SCREW_SPECS.items():
        visible, axial_offset, angle = direct_screw_state(frame, spec)
        group = graphics["screws"][name]
        group.isVisible = visible
        group.transform = rigid_axis_transform(
            LAYER_AXIS, spec["bearing"], axial_offset, angle
        )

    show_alignment_rings = 208 <= frame <= 247
    graphics["j17_rings"].isVisible = show_alignment_rings
    graphics["j17_rings"].transform = adsk.core.Matrix3D.create()
    graphics["j20_rings"].isVisible = show_alignment_rings
    ring_transform = adsk.core.Matrix3D.create()
    ring_transform.translation = vector(current_upper_offset)
    graphics["j20_rings"].transform = ring_transform

    for body, original_opacity in opacity_records:
        body.opacity = original_opacity
    if 80 <= frame <= 207:
        set_opacity_for_component(occurrences, S410_INDEX, 0.30)
        set_opacity_for_component(occurrences, J20A_INDEX, 0.44)
        set_opacity_for_component(occurrences, MID360_INDEX, 0.20)
    elif 208 <= frame <= 247:
        set_opacity_for_component(occurrences, J17A_INDEX, 0.52)
        set_opacity_for_component(occurrences, J20A_INDEX, 0.52)
        set_opacity_for_component(occurrences, MID360_INDEX, 0.20)
        set_opacity_for_component(occurrences, S410_INDEX, 0.22)
    elif 248 <= frame <= 391:
        set_opacity_for_component(occurrences, J17A_INDEX, 0.32)
        set_opacity_for_component(occurrences, J20A_INDEX, 0.40)
        set_opacity_for_component(occurrences, MID360_INDEX, 0.16)
        set_opacity_for_component(occurrences, S410_INDEX, 0.18)
    elif 392 <= frame <= 423:
        amount = phase(frame, 392, 423)
        set_opacity_for_component(occurrences, J17A_INDEX, lerp(0.32, 1.0, amount))
        set_opacity_for_component(occurrences, J20A_INDEX, lerp(0.40, 1.0, amount))
        set_opacity_for_component(occurrences, MID360_INDEX, lerp(0.16, 1.0, amount))
        set_opacity_for_component(occurrences, S410_INDEX, lerp(0.18, 1.0, amount))


def s410_screw_camera(viewport, screw_index):
    target = shifted(
        shifted(S410_SCREW_SEATS[screw_index], UPPER_SEPARATION),
        scaled(MOUNT_NORMAL, 0.8),
    )
    width_sign = -1.0 if screw_index in (28, 30) else 1.0
    direction = shifted(
        MOUNT_NORMAL,
        shifted(scaled(WIDTH_AXIS, width_sign * 0.65), scaled(PLATE_UP, 0.32)),
    )
    apply_camera(viewport, target, direction, 6.2, up=PLATE_UP)


def direct_screw_camera(viewport, spec):
    target = shifted(spec["bearing"], scaled(LAYER_AXIS, -0.38))
    direction = shifted(
        scaled(LAYER_AXIS, -1.0),
        shifted(
            scaled(WIDTH_AXIS, spec["width_sign"] * 0.72),
            (0.0, 0.0, 0.32),
        ),
    )
    apply_camera(viewport, target, direction, 6.0)


def set_scene_camera(viewport, frame):
    if frame < 24:
        apply_camera(
            viewport, (-30.447, 26.0, 257.0), (0.82, 1.0, 0.48), 22.0
        )
    elif frame < 80:
        apply_camera(
            viewport, (-30.447, 31.0, 257.1), (0.78, 1.0, 0.45), 17.0
        )
    elif frame < 208:
        active = active_s410_screw(frame)
        if active is None:
            apply_camera(
                viewport, (-30.447, 31.0, 257.1), (0.78, 1.0, 0.45), 17.0
            )
        else:
            s410_screw_camera(viewport, active[0])
    elif frame < 248:
        apply_camera(
            viewport, (-30.447, 24.0, 256.2), (0.78, -1.0, 0.44), 17.5
        )
    elif frame < 392:
        for spec in DIRECT_SCREW_SPECS.values():
            begin, end = spec["schedule"]
            if begin <= frame <= end:
                direct_screw_camera(viewport, spec)
                return
        apply_camera(
            viewport, (-30.447, 21.2, 256.0), (0.72, -1.0, 0.36), 15.0
        )
    elif frame < 424:
        apply_camera(
            viewport, (-30.447, 21.5, 256.0), (0.74, -1.0, 0.40), 15.5
        )
    else:
        apply_camera(
            viewport, (-30.447, 24.3, 257.0), (0.82, 1.0, 0.52), 18.5
        )


def maximum_transform_difference(first, second):
    return max(abs(first[index] - second[index]) for index in range(16))


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences
    if occurrences.count != 34:
        raise RuntimeError(
            "Expected 34 root occurrences, found " + str(occurrences.count)
        )

    expected_prefixes = {
        1: "J17A_ORIGINAL_MANUFACTURER_BREP_CORRECT_UPPER_65MM_PAIR",
        2: "1T21-J20A-",
        3: "1CA5-S410-",
        4: "MID-360_4_ASM",
        15: "LITE3_FULLSTACK_D435I_REAL_BREP_OFFICIAL_MANUFACTURER_CAD",
        28: "S410_TO_J20_M5X8_INDIVIDUAL_SCREW_VISUAL_CANDIDATE",
        29: "S410_TO_J20_M5X8_INDIVIDUAL_SCREW_VISUAL_CANDIDATE",
        30: "S410_TO_J20_M5X8_INDIVIDUAL_SCREW_VISUAL_CANDIDATE",
        31: "S410_TO_J20_M5X8_INDIVIDUAL_SCREW_VISUAL_CANDIDATE",
        33: "S410_M5_SHORT_L_KEY_ANIMATION_TOOL",
    }
    for index, prefix in expected_prefixes.items():
        if not occurrences.item(index).component.name.startswith(prefix):
            raise RuntimeError("Unexpected component at index " + str(index))

    final_transforms = {
        index: list(occurrences.item(index).transform.asArray())
        for index in range(occurrences.count)
    }
    final_visibility = [
        bool(occurrences.item(index).isLightBulbOn)
        for index in range(occurrences.count)
    ]
    opacity_records = []
    for index in (J17A_INDEX, J20A_INDEX, S410_INDEX, MID360_INDEX, D435I_INDEX):
        for body in component_bodies(occurrences.item(index).component):
            opacity_records.append((body, body.opacity))

    viewport = application.activeViewport
    original_camera = camera_state(viewport.camera)
    graphics = create_custom_graphics(root)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    frames = FRAME_LIST if FRAME_LIST is not None else range(FRAME_START, FRAME_END)
    rendered = []
    graphics_removed = False
    try:
        for frame in frames:
            set_scene_state(
                occurrences, final_transforms, frame, opacity_records, graphics
            )
            set_scene_camera(viewport, frame)
            viewport.refresh()
            adsk.doEvents()
            path = os.path.join(OUTPUT_DIR, "frame_%04d.png" % frame)
            if not viewport.saveAsImageFile(path, FRAME_WIDTH, FRAME_HEIGHT):
                raise RuntimeError("Failed to render " + path)
            rendered.append(frame)
    finally:
        for index in range(occurrences.count):
            occurrences.item(index).transform = matrix_from_values(
                final_transforms[index]
            )
            occurrences.item(index).isLightBulbOn = final_visibility[index]
        for body, opacity in opacity_records:
            body.opacity = opacity
        if graphics.get("parent") is not None and graphics["parent"].isValid:
            graphics_removed = bool(graphics["parent"].deleteMe())
        restore_camera(viewport, original_camera)
        viewport.refresh()
        adsk.doEvents()

    transform_difference = 0.0
    visibility_mismatches = []
    for index in range(occurrences.count):
        actual = list(occurrences.item(index).transform.asArray())
        transform_difference = max(
            transform_difference,
            maximum_transform_difference(actual, final_transforms[index]),
        )
        if bool(occurrences.item(index).isLightBulbOn) != final_visibility[index]:
            visibility_mismatches.append(index)
    opacity_mismatches = [
        body.entityToken
        for body, expected in opacity_records
        if abs(body.opacity - expected) > 1.0e-12
    ]

    report = {
        "stage": "experiment_and_analysis",
        "frames_rendered": rendered,
        "output_dir": OUTPUT_DIR,
        "contains_text_overlay": False,
        "persistent_visible_occurrences": list(PERSISTENT_VISIBLE_INDICES),
        "rejected_occurrences_always_hidden": [
            7,
            8,
            9,
            10,
            18,
            19,
            20,
            21,
            22,
            23,
        ],
        "sequence": {
            "s410_approach": [24, 71],
            "s410_m5_cross_order": [28, 31, 29, 30],
            "upper_subassembly_to_j17a": [208, 247],
            "direct_thread_order": list(DIRECT_SCREW_SPECS.keys()),
            "nuts": 0,
            "washers": 0,
        },
        "direct_thread_visual_candidates": DIRECT_SCREW_SPECS,
        "claim_boundary": {
            "validated_visual_logic": (
                "S410 clearance feet to J20A M5 threads; J17A head-seat and "
                "clearance path to J20A modeled M3/M4 threaded receivers; no "
                "far-side nuts or washers."
            ),
            "not_validated": (
                "Factory-supplied screw length/head form, usable engagement, "
                "torque, strength, vibration, exact hand-tool access, or "
                "real-hardware safety."
            ),
        },
        "restored": {
            "maximum_transform_difference": transform_difference,
            "visibility_mismatches": visibility_mismatches,
            "opacity_mismatches": opacity_mismatches,
            "custom_graphics_removed": graphics_removed,
            "custom_graphics_group_count_before": graphics["before_count"],
            "custom_graphics_group_count_after": root.customGraphicsGroups.count,
            "pending_snapshot": bool(design.snapshots.hasPendingSnapshot),
        },
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps(report, ensure_ascii=False))

