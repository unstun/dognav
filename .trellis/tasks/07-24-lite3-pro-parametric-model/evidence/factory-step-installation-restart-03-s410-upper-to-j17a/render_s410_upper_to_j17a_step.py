"""Render restart step 03: guard the radar, then join upper and first layers.

The accepted J17A/D435i first layer and accepted J20A/MID360 upper subassembly
begin separated.  S410 approaches the upper subassembly and its four M5 visual
screw candidates are started and tightened individually in a diagonal cross
sequence with the short L-key.  Four J17A/J20A through-fastener candidates are
then pre-inserted bottom-up while the layers are still separate.  The guarded
upper subassembly approaches J17A along the common fastener axes; two front
nuts and two rear washer/locknut pairs complete the visual connection.

No Lite3 robot, robot-side hardware, receiver proxy, grouped S410 screw draft,
or long T-driver appears.
"""

import adsk.core
import adsk.fusion
import json
import math
import os


FRAME_START = globals().get("FRAME_START", 0)
FRAME_END = globals().get("FRAME_END", 600)
FRAME_LIST = globals().get("FRAME_LIST")
FRAME_WIDTH = globals().get("FRAME_WIDTH", 1280)
FRAME_HEIGHT = globals().get("FRAME_HEIGHT", 720)

OUTPUT_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-installation-restart-03-s410-upper-to-j17a/frames"
)

J17A_INDEX = 1
J20A_INDEX = 2
S410_INDEX = 3
MID360_INDEX = 4
FRONT_BOLT_INDICES = (7, 8)
FRONT_NUT_INDICES = (9, 10)
MID360_SCREW_INDICES = (11, 12, 13, 14)
D435I_INDEX = 15
D435I_SCREW_INDICES = (16, 17)
REAR_BOLT_INDICES = (18, 19)
REAR_WASHER_INDICES = (20, 21)
REAR_LOCKNUT_INDICES = (22, 23)
S410_SCREW_INDICES = (28, 29, 30, 31)
SHORT_L_KEY_INDEX = 33

VISIBLE_FINAL_INDICES = (
    J17A_INDEX,
    J20A_INDEX,
    S410_INDEX,
    MID360_INDEX,
    *FRONT_BOLT_INDICES,
    *FRONT_NUT_INDICES,
    *MID360_SCREW_INDICES,
    D435I_INDEX,
    *D435I_SCREW_INDICES,
    *REAR_BOLT_INDICES,
    *REAR_WASHER_INDICES,
    *REAR_LOCKNUT_INDICES,
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
    28: {"start": (80, 99), "tighten": (160, 179)},
    31: {"start": (100, 119), "tighten": (180, 199)},
    29: {"start": (120, 139), "tighten": (200, 219)},
    30: {"start": (140, 159), "tighten": (220, 239)},
}

S410_TOOL_ANGLE_RANGES_DEG = {
    28: (240.0, 330.0),
    31: (60.0, 150.0),
    29: (210.0, 300.0),
    30: (30.0, 120.0),
}

LAYER_FASTENER_SCHEDULES = {
    7: (240, 263),
    8: (264, 287),
    18: (288, 311),
    19: (312, 335),
}

LAYER_FASTENER_AXIS_POINTS = {
    7: (-32.24700964468146, 21.068141858307484, 259.73489005808057),
    8: (-28.647009644681464, 21.068141858307484, 259.73489005808057),
    18: (-33.84112221937691, 22.918141858307482, 251.89077750838507),
    19: (-27.05289706998607, 22.918141858307482, 251.89077750838507),
}

FRONT_NUT_SCHEDULES = {9: (384, 407), 10: (408, 431)}
FRONT_NUT_AXIS_POINTS = {
    9: (-32.24700964468146, 21.32163550736137, 259.73489005808057),
    10: (-28.647009644681464, 21.32163550736137, 259.73489005808057),
}

REAR_WASHER_SCHEDULES = {20: (432, 447), 21: (472, 487)}
REAR_LOCKNUT_SCHEDULES = {22: (448, 471), 23: (488, 511)}
REAR_AXIS_POINTS = {
    20: (-33.84112221937691, 23.258141858307482, 251.89077750838507),
    21: (-27.05289706998607, 23.258141858307482, 251.89077750838507),
    22: (-33.84112221937691, 23.458141858307485, 251.89077750838507),
    23: (-27.05289706998607, 23.458141858307485, 251.89077750838507),
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
    camera.eye = adsk.core.Point3D.create(*state["eye"])
    camera.target = adsk.core.Point3D.create(*state["target"])
    camera.upVector = adsk.core.Vector3D.create(*state["up"])
    camera.viewExtents = state["extents"]
    viewport.camera = camera


def apply_camera(viewport, target, direction, extents, up=(0.0, 0.0, 1.0)):
    direction = normalized(direction)
    eye = shifted(target, scaled(direction, 36.0))
    camera = viewport.camera
    camera.isSmoothTransition = False
    camera.cameraType = adsk.core.CameraTypes.OrthographicCameraType
    camera.eye = adsk.core.Point3D.create(*eye)
    camera.target = adsk.core.Point3D.create(*target)
    camera.upVector = adsk.core.Vector3D.create(*up)
    camera.viewExtents = extents
    viewport.camera = camera


def component_bodies(component):
    bodies = []
    seen = set()

    def walk(current):
        for index in range(current.bRepBodies.count):
            body = current.bRepBodies.item(index)
            if body.entityToken not in seen:
                seen.add(body.entityToken)
                bodies.append(body)
        for index in range(current.occurrences.count):
            walk(current.occurrences.item(index).component)

    walk(component)
    return bodies


def matrix_from_values(values):
    matrix = adsk.core.Matrix3D.create()
    if not matrix.setWithArray(values):
        raise RuntimeError("Could not set occurrence transform")
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


def mat_vec(matrix, vector):
    return tuple(
        sum(matrix[row][column] * vector[column] for column in range(3))
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
    axis,
    axis_point,
    axial_offset,
    angle,
    assembly_offset=(0.0, 0.0, 0.0),
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


def upper_offset(frame):
    if frame < 336:
        return UPPER_SEPARATION
    if frame <= 383:
        return scaled(UPPER_SEPARATION, 1.0 - phase(frame, 336, 383))
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


def linear_rotating_state(frame, begin, end, initial_offset, turns=3.0):
    if frame < begin:
        return False, initial_offset, 0.0
    if frame <= end:
        amount = phase(frame, begin, end)
        return (
            True,
            initial_offset * (1.0 - amount),
            turns * 2.0 * math.pi * amount,
        )
    return True, 0.0, turns * 2.0 * math.pi


def translate_state(frame, begin, end, initial_offset):
    if frame < begin:
        return False, initial_offset
    if frame <= end:
        return True, initial_offset * (1.0 - phase(frame, begin, end))
    return True, 0.0


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
    values[3] = (
        screw_values[3]
        + assembly_offset[0]
        + MOUNT_NORMAL[0] * insertion_offset
    )
    values[7] = (
        screw_values[7]
        + assembly_offset[1]
        + MOUNT_NORMAL[1] * insertion_offset
    )
    values[11] = (
        screw_values[11]
        + assembly_offset[2]
        + MOUNT_NORMAL[2] * insertion_offset
    )
    values[15] = 1.0
    occurrence.transform = matrix_from_values(values)
    occurrence.isLightBulbOn = True


def set_scene_state(occurrences, final_transforms, frame, opacity_records):
    for index in range(occurrences.count):
        occurrences.item(index).isLightBulbOn = False

    # Accepted first layer stays fixed throughout this step.
    for index in (J17A_INDEX, D435I_INDEX, *D435I_SCREW_INDICES):
        set_offset_occurrence(
            occurrences.item(index),
            final_transforms[index],
            True,
            (0.0, 0.0, 0.0),
        )

    # Accepted J20A/MID360 upper subassembly begins separated from J17A.
    current_upper_offset = upper_offset(frame)
    for index in (J20A_INDEX, MID360_INDEX, *MID360_SCREW_INDICES):
        set_offset_occurrence(
            occurrences.item(index),
            final_transforms[index],
            True,
            current_upper_offset,
        )

    guard_amount = phase(frame, 24, 71)
    guard_offset = shifted(
        current_upper_offset,
        scaled(MOUNT_NORMAL, 5.5 * (1.0 - guard_amount)),
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

    for index, (begin, end) in LAYER_FASTENER_SCHEDULES.items():
        visible, axial_offset, angle = linear_rotating_state(
            frame, begin, end, -3.0
        )
        set_rotating_occurrence(
            occurrences.item(index),
            final_transforms[index],
            visible,
            LAYER_AXIS,
            LAYER_FASTENER_AXIS_POINTS[index],
            axial_offset,
            angle,
        )

    for index, (begin, end) in FRONT_NUT_SCHEDULES.items():
        visible, axial_offset, angle = linear_rotating_state(
            frame, begin, end, 2.0
        )
        set_rotating_occurrence(
            occurrences.item(index),
            final_transforms[index],
            visible,
            LAYER_AXIS,
            FRONT_NUT_AXIS_POINTS[index],
            axial_offset,
            angle,
        )

    for index, (begin, end) in REAR_WASHER_SCHEDULES.items():
        visible, axial_offset = translate_state(frame, begin, end, 1.5)
        set_offset_occurrence(
            occurrences.item(index),
            final_transforms[index],
            visible,
            scaled(LAYER_AXIS, axial_offset),
        )

    for index, (begin, end) in REAR_LOCKNUT_SCHEDULES.items():
        visible, axial_offset, angle = linear_rotating_state(
            frame, begin, end, 2.0
        )
        set_rotating_occurrence(
            occurrences.item(index),
            final_transforms[index],
            visible,
            LAYER_AXIS,
            REAR_AXIS_POINTS[index],
            axial_offset,
            angle,
        )

    for body, opacity in opacity_records:
        body.opacity = opacity
    if 80 <= frame <= 239:
        for body in component_bodies(occurrences.item(S410_INDEX).component):
            body.opacity = 0.30
        for body in component_bodies(occurrences.item(J20A_INDEX).component):
            body.opacity = 0.42
        for body in component_bodies(occurrences.item(MID360_INDEX).component):
            body.opacity = 0.20
    elif 240 <= frame <= 335:
        for body in component_bodies(occurrences.item(J17A_INDEX).component):
            body.opacity = 0.38
    elif 336 <= frame <= 383:
        for body in component_bodies(occurrences.item(J17A_INDEX).component):
            body.opacity = 0.58
        for body in component_bodies(occurrences.item(J20A_INDEX).component):
            body.opacity = 0.58
    elif 384 <= frame <= 511:
        for body in component_bodies(occurrences.item(J20A_INDEX).component):
            body.opacity = 0.38
        for body in component_bodies(occurrences.item(S410_INDEX).component):
            body.opacity = 0.24
        for body in component_bodies(occurrences.item(MID360_INDEX).component):
            body.opacity = 0.20


def screw_camera(viewport, screw_index):
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


def bottom_fastener_camera(viewport, index):
    target = shifted(
        LAYER_FASTENER_AXIS_POINTS[index],
        scaled(LAYER_AXIS, -0.65),
    )
    width_sign = -1.0 if index in (7, 18) else 1.0
    direction = shifted(
        scaled(LAYER_AXIS, -1.0),
        shifted(scaled(WIDTH_AXIS, width_sign * 0.72), (0.0, 0.0, 0.30)),
    )
    apply_camera(viewport, target, direction, 6.2)


def top_fastener_camera(viewport, axis_point, width_sign):
    target = shifted(axis_point, scaled(LAYER_AXIS, 0.45))
    direction = shifted(
        LAYER_AXIS,
        shifted(scaled(WIDTH_AXIS, width_sign * 0.70), (0.0, 0.0, 0.28)),
    )
    apply_camera(viewport, target, direction, 6.3)


def set_scene_camera(viewport, frame):
    if frame < 24:
        apply_camera(
            viewport,
            (-30.447, 26.0, 257.0),
            (0.82, 1.0, 0.48),
            22.0,
        )
    elif frame < 80:
        apply_camera(
            viewport,
            (-30.447, 31.0, 257.1),
            (0.78, 1.0, 0.45),
            17.0,
        )
    elif frame < 240:
        active = active_s410_screw(frame)
        if active is None:
            apply_camera(
                viewport,
                (-30.447, 31.0, 257.1),
                (0.78, 1.0, 0.45),
                17.0,
            )
        else:
            screw_camera(viewport, active[0])
    elif frame < 336:
        for index, (begin, end) in LAYER_FASTENER_SCHEDULES.items():
            if begin <= frame <= end:
                bottom_fastener_camera(viewport, index)
                return
        apply_camera(
            viewport,
            (-30.447, 21.2, 256.0),
            (0.75, -1.0, 0.35),
            15.0,
        )
    elif frame < 384:
        apply_camera(
            viewport,
            (-30.447, 25.0, 256.6),
            (0.82, 1.0, 0.46),
            18.0,
        )
    elif frame < 408:
        top_fastener_camera(viewport, FRONT_NUT_AXIS_POINTS[9], -1.0)
    elif frame < 432:
        top_fastener_camera(viewport, FRONT_NUT_AXIS_POINTS[10], 1.0)
    elif frame < 472:
        top_fastener_camera(viewport, REAR_AXIS_POINTS[22], -1.0)
    elif frame < 512:
        top_fastener_camera(viewport, REAR_AXIS_POINTS[23], 1.0)
    elif frame < 544:
        apply_camera(
            viewport,
            (-30.447, 22.0, 256.2),
            (0.72, -1.0, 0.38),
            16.5,
        )
    else:
        apply_camera(
            viewport,
            (-30.447, 24.5, 257.2),
            (0.82, 1.0, 0.52),
            18.5,
        )


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    occurrences = design.rootComponent.occurrences
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
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    frames = FRAME_LIST if FRAME_LIST is not None else range(FRAME_START, FRAME_END)
    rendered = []
    try:
        for frame in frames:
            set_scene_state(occurrences, final_transforms, frame, opacity_records)
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
            max(abs(actual[i] - expected[i]) for i in range(16)),
        )
        if bool(occurrences.item(index).isLightBulbOn) != final_visibility[index]:
            visibility_mismatches.append(index)

    print(
        json.dumps(
            {
                "frames_rendered": rendered,
                "output_dir": OUTPUT_DIR,
                "visible_final_components": list(VISIBLE_FINAL_INDICES),
                "sequence": {
                    "s410_approach": [24, 71],
                    "s410_start_cross_order": [28, 31, 29, 30],
                    "s410_tighten_cross_order": [28, 31, 29, 30],
                    "j17a_bottom_up_fasteners": [7, 8, 18, 19],
                    "upper_subassembly_join": [336, 383],
                    "front_top_nuts": [9, 10],
                    "rear_washer_locknut_pairs": [[20, 22], [21, 23]],
                    "robot_present": False,
                },
                "restored": {
                    "maximum_transform_difference": maximum_transform_difference,
                    "visibility_mismatches": visibility_mismatches,
                    "pending_snapshot": bool(design.snapshots.hasPendingSnapshot),
                },
            }
        )
    )
