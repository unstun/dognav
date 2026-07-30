"""Render the corrected S410 single-axis fastening sequence without text.

Sequence:
1. The carrier and S410 guard are preassembled above the Lite3 body because
   the final installed pose does not provide a collision-free underside tool path.
2. An M5x14 bolt enters from the underside and stops 0.8 mm short of its seat.
3. The top M5 nut advances six turns over 4.8 mm onto the exposed shaft.
4. A short L-key approaches from below and performs four 90-degree strokes,
   advancing the bolt by one M5 pitch (0.8 mm) until the head seats.
5. The two rear locating spacers are placed on Lite3 before the fastened
   carrier/guard assembly lowers into its final pose.
6. The retained front 2x M3x8 and rear 2x M3x12 base screws are installed one
   at a time with an animation-only long-reach hex key.
7. The video ends on an opaque local inspection view and the complete Lite3.

The printed carrier and S410 guard are shown as translucent section/full views.
This is a visual/packaging candidate, not an official hardware or torque claim.
"""

import adsk.core
import adsk.fusion
import json
import math
import os
import traceback


globals().pop("run", None)


TOTAL_FRAME_COUNT = 570
FRAME_START = globals().get("FRAME_START", 0)
FRAME_END = globals().get("FRAME_END", TOTAL_FRAME_COUNT)
FRAME_LIST = globals().get("FRAME_LIST")
FRAME_WIDTH = globals().get("FRAME_WIDTH", 1280)
FRAME_HEIGHT = globals().get("FRAME_HEIGHT", 720)

OUTPUT_ROOT = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-rev-c2-s410-single-through-bolt-top-nut-video"
)
OUTPUT_DIR = os.path.join(OUTPUT_ROOT, "frames")

CARRIER_NAME = (
    "J17A_J20A_REV_C2_S410_SINGLE_THROUGH_HOLE_HEAD_ACCESS_PREVIEW_NOT_OFFICIAL_CAD"
)
BOLT_NAME = "S410_S1_M5X14_BOTTOM_UP_BOLT_HEAD_ACCESS_PREVIEW"
NUT_NAME = "S410_S1_M5_TOP_HEX_NUT_HEAD_ACCESS_PREVIEW"
TOOL_NAME = "S410_M5_SHORT_L_KEY_ANIMATION_TOOL"
GUARD_ACCESS_CANDIDATE_NAME = (
    "S410_GUARD_FRONT_BASE_2X_M3_FULL_DEPTH_ACCESS_HOLES_7MM_"
    "VISUAL_PRINT_CANDIDATE_NOT_OFFICIAL_CAD"
)
FRONT_BASE_SCREWS_NAME = (
    "BASE_TO_LITE3_FRONT_2X_M3X8_SOCKET_HEAD_SCREWS_REAL_BREP"
)
REAR_BASE_SPACERS_NAME = (
    "BASE_TO_LITE3_REAR_2X_OD8_ID3P5_LOCATING_SPACERS_REAL_BREP"
)
REAR_BASE_SCREWS_NAME = (
    "BASE_TO_LITE3_REAR_2X_M3X12_SOCKET_HEAD_SCREWS_REAL_BREP"
)

MOUNT_NORMAL = (0.0, 0.9659258262890683, 0.25881904510252074)
PLATE_UP = (0.0, -0.25881904510252074, 0.9659258262890683)
WIDTH_AXIS = (1.0, 0.0, 0.0)
AXIS_POINT = (-32.90685957328745, 21.378538809797107, 260.49515922999285)
UNDERSIDE_PROJECTION_CM = 87.33122856653883
TOPSIDE_PROJECTION_CM = 88.07119113044189

BOLT_START_OFFSET_CM = -1.30
BOLT_PRETIGHT_OFFSET_CM = -0.08
NUT_START_OFFSET_CM = 0.48
M5_PITCH_CM = 0.08
QUARTER_TURN_ADVANCE_CM = M5_PITCH_CM / 4.0
TOOL_STROKE_START_DEG = 240.0
PREASSEMBLY_STANDOFF_CM = 15.0

REAR_SPACER_START = 294
REAR_SPACER_END = 317
STACK_MOUNT_START = 318
STACK_MOUNT_END = 347
BASE_SCREW_OPERATION_FRAMES = 36
BASE_SCREW_STARTS = (348, 384, 426, 462)
BASE_FINAL_CLOSE_START = 498
BASE_EXACT_FINAL_START = 522
GLOBAL_HOLD_START = 546

BASE_SCREW_START_OFFSET_CM = 2.0
BASE_SCREW_HAND_SEAT_OFFSET_CM = 0.35
BASE_DRIVER_APPROACH_OFFSET_CM = 0.85
BASE_SCREW_TIGHTENING_TURNS = 2.0

FRONT_BASE_AXIS_POINTS = (
    (-33.697009644681465, 20.168141858307482, 260.68489005808055),
    (-27.197009644681465, 20.168141858307482, 260.68489005808055),
)
FRONT_BASE_HEAD_POINTS = (
    (-33.697009644681465, 20.718141858307483, 260.68489005808055),
    (-27.197009644681465, 20.718141858307483, 260.68489005808055),
)
REAR_BASE_AXIS_POINTS = (
    (-35.69739294209252, 20.66814185830748, 247.2850190222833),
    (-25.196948718114285, 20.66814185830748, 247.28502596461186),
)
REAR_BASE_HEAD_POINTS = (
    (-35.69739294209252, 21.41814185830748, 247.2850190222833),
    (-25.196948718114285, 21.41814185830748, 247.28502596461186),
)


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


def lerp3(first, second, amount):
    return tuple(lerp(first[index], second[index], amount) for index in range(3))


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


def camera_snapshot(viewport):
    camera = viewport.camera
    return {
        "eye": (camera.eye.x, camera.eye.y, camera.eye.z),
        "target": (camera.target.x, camera.target.y, camera.target.z),
        "up": (camera.upVector.x, camera.upVector.y, camera.upVector.z),
        "extents": camera.viewExtents,
        "type": camera.cameraType,
    }


def restore_camera(viewport, snapshot):
    camera = viewport.camera
    camera.isSmoothTransition = False
    camera.cameraType = snapshot["type"]
    camera.eye = point(snapshot["eye"])
    camera.target = point(snapshot["target"])
    camera.upVector = vector(snapshot["up"])
    camera.viewExtents = snapshot["extents"]
    viewport.camera = camera


def apply_camera(viewport, shot):
    camera = viewport.camera
    camera.isSmoothTransition = False
    camera.cameraType = adsk.core.CameraTypes.OrthographicCameraType
    camera.eye = point(shot["eye"])
    camera.target = point(shot["target"])
    camera.upVector = vector(shot["up"])
    camera.viewExtents = shot["extents"]
    viewport.camera = camera


def blend_camera(viewport, first, second, amount):
    up = normalized(lerp3(first["up"], second["up"], amount))
    apply_camera(
        viewport,
        {
            "eye": lerp3(first["eye"], second["eye"], amount),
            "target": lerp3(first["target"], second["target"], amount),
            "up": up,
            "extents": lerp(first["extents"], second["extents"], amount),
        },
    )


UNDERSIDE_POINT = at_projection(
    AXIS_POINT, MOUNT_NORMAL, UNDERSIDE_PROJECTION_CM
)
TOPSIDE_POINT = at_projection(AXIS_POINT, MOUNT_NORMAL, TOPSIDE_PROJECTION_CM)
STACK_CENTER = at_projection(
    AXIS_POINT,
    MOUNT_NORMAL,
    (UNDERSIDE_PROJECTION_CM + TOPSIDE_PROJECTION_CM) * 0.5,
)
PREASSEMBLY_OFFSET = scaled(MOUNT_NORMAL, PREASSEMBLY_STANDOFF_CM)

SIDE_SHOT = {
    "target": added(STACK_CENTER, scaled(PLATE_UP, -0.05)),
    "eye": added(STACK_CENTER, scaled(WIDTH_AXIS, 18.0)),
    "up": MOUNT_NORMAL,
    "extents": 4.6,
}
UNDERSIDE_SHOT = {
    "target": added(UNDERSIDE_POINT, scaled(MOUNT_NORMAL, -0.18)),
    "eye": added(
        added(UNDERSIDE_POINT, scaled(MOUNT_NORMAL, -15.0)),
        scaled(WIDTH_AXIS, 3.8),
    ),
    "up": PLATE_UP,
    "extents": 4.1,
}
TOPSIDE_SHOT = {
    "target": added(TOPSIDE_POINT, scaled(MOUNT_NORMAL, 0.15)),
    "eye": added(
        added(TOPSIDE_POINT, scaled(MOUNT_NORMAL, 15.0)),
        scaled(WIDTH_AXIS, 3.0),
    ),
    "up": PLATE_UP,
    "extents": 4.1,
}
TOP_TOOL_SHOT = {
    "target": added(TOPSIDE_POINT, scaled(MOUNT_NORMAL, 0.75)),
    "eye": added(
        added(
            added(TOPSIDE_POINT, scaled(MOUNT_NORMAL, 14.0)),
            scaled(WIDTH_AXIS, 5.0),
        ),
        scaled(PLATE_UP, 2.0),
    ),
    "up": PLATE_UP,
    "extents": 5.0,
}
FINAL_SHOT_TARGET = added(STACK_CENTER, scaled(MOUNT_NORMAL, 0.18))
FINAL_SHOT = {
    "target": FINAL_SHOT_TARGET,
    "eye": added(
        added(
            added(FINAL_SHOT_TARGET, scaled(WIDTH_AXIS, 8.0)),
            scaled(MOUNT_NORMAL, 12.0),
        ),
        scaled(PLATE_UP, 4.0),
    ),
    "up": PLATE_UP,
    "extents": 5.0,
}
GLOBAL_SHOT = {
    "eye": (-149.75, 247.0, 337.0),
    "target": (-29.75, 12.0, 237.0),
    "up": (0.0, 0.0, 1.0),
    "extents": 82.0,
}
PREASSEMBLY_OVERVIEW_TARGET = added(
    STACK_CENTER, scaled(PREASSEMBLY_OFFSET, 0.48)
)
PREASSEMBLY_OVERVIEW_SHOT = {
    "target": PREASSEMBLY_OVERVIEW_TARGET,
    "eye": added(
        added(
            added(PREASSEMBLY_OVERVIEW_TARGET, scaled(WIDTH_AXIS, 17.0)),
            scaled(MOUNT_NORMAL, 20.0),
        ),
        scaled(PLATE_UP, 8.0),
    ),
    "up": PLATE_UP,
    "extents": 22.0,
}
MOUNT_SHOT_TARGET = added(STACK_CENTER, scaled(PREASSEMBLY_OFFSET, 0.42))
MOUNT_SHOT = {
    "target": MOUNT_SHOT_TARGET,
    "eye": added(
        added(
            added(MOUNT_SHOT_TARGET, scaled(WIDTH_AXIS, 10.0)),
            scaled(MOUNT_NORMAL, 15.0),
        ),
        scaled(PLATE_UP, 5.0),
    ),
    "up": PLATE_UP,
    "extents": 18.0,
}
BASE_FRONT_PAIR_SHOT = {
    "target": (-30.447009644681465, 25.0, 260.68489005808055),
    "eye": (-30.447009644681465, 43.0, 278.68489005808055),
    "up": (0.0, 0.0, 1.0),
    "extents": 13.0,
}
BASE_REAR_PAIR_SHOT = {
    "target": (-30.4471708301034, 26.2, 247.28502249344757),
    "eye": (-30.4471708301034, 44.2, 265.28502249344757),
    "up": (0.0, 0.0, 1.0),
    "extents": 14.0,
}
BASE_COMPLETE_SHOT = {
    "target": (-30.447009644681465, 20.5, 254.0),
    "eye": (-48.0, 49.0, 278.0),
    "up": (0.0, 0.0, 1.0),
    "extents": 24.0,
}


def shot_with_offset(shot, offset):
    return {
        "eye": added(shot["eye"], offset),
        "target": added(shot["target"], offset),
        "up": shot["up"],
        "extents": shot["extents"],
    }


def assembly_offset(frame):
    if frame < STACK_MOUNT_START:
        return PREASSEMBLY_OFFSET
    if frame <= STACK_MOUNT_END:
        return scaled(
            PREASSEMBLY_OFFSET,
            1.0 - phase(frame, STACK_MOUNT_START, STACK_MOUNT_END),
        )
    return (0.0, 0.0, 0.0)


def set_animation_camera(viewport, frame):
    if frame < 24:
        apply_camera(viewport, PREASSEMBLY_OVERVIEW_SHOT)
    elif frame < 36:
        blend_camera(
            viewport,
            PREASSEMBLY_OVERVIEW_SHOT,
            shot_with_offset(UNDERSIDE_SHOT, PREASSEMBLY_OFFSET),
            phase(frame, 24, 35),
        )
    elif frame < 108:
        apply_camera(viewport, shot_with_offset(UNDERSIDE_SHOT, PREASSEMBLY_OFFSET))
    elif frame < 132:
        blend_camera(
            viewport,
            shot_with_offset(UNDERSIDE_SHOT, PREASSEMBLY_OFFSET),
            shot_with_offset(TOPSIDE_SHOT, PREASSEMBLY_OFFSET),
            phase(frame, 108, 131),
        )
    elif frame < 204:
        apply_camera(viewport, shot_with_offset(TOPSIDE_SHOT, PREASSEMBLY_OFFSET))
    elif frame < 222:
        blend_camera(
            viewport,
            shot_with_offset(TOPSIDE_SHOT, PREASSEMBLY_OFFSET),
            shot_with_offset(UNDERSIDE_SHOT, PREASSEMBLY_OFFSET),
            phase(frame, 204, 221),
        )
    elif frame < REAR_SPACER_START:
        apply_camera(viewport, shot_with_offset(UNDERSIDE_SHOT, PREASSEMBLY_OFFSET))
    elif frame < 306:
        blend_camera(
            viewport,
            shot_with_offset(UNDERSIDE_SHOT, PREASSEMBLY_OFFSET),
            BASE_REAR_PAIR_SHOT,
            phase(frame, REAR_SPACER_START, 305),
        )
    elif frame < STACK_MOUNT_START:
        apply_camera(viewport, BASE_REAR_PAIR_SHOT)
    elif frame < 330:
        blend_camera(
            viewport,
            BASE_REAR_PAIR_SHOT,
            MOUNT_SHOT,
            phase(frame, STACK_MOUNT_START, 329),
        )
    elif frame < BASE_SCREW_STARTS[0]:
        blend_camera(
            viewport,
            MOUNT_SHOT,
            BASE_FRONT_PAIR_SHOT,
            phase(frame, 330, STACK_MOUNT_END),
        )
    elif frame < BASE_SCREW_STARTS[2] - 6:
        apply_camera(viewport, BASE_FRONT_PAIR_SHOT)
    elif frame < BASE_SCREW_STARTS[2]:
        blend_camera(
            viewport,
            BASE_FRONT_PAIR_SHOT,
            BASE_REAR_PAIR_SHOT,
            phase(frame, BASE_SCREW_STARTS[2] - 6, BASE_SCREW_STARTS[2] - 1),
        )
    elif frame < BASE_FINAL_CLOSE_START:
        apply_camera(viewport, BASE_REAR_PAIR_SHOT)
    elif frame < BASE_EXACT_FINAL_START:
        apply_camera(viewport, BASE_COMPLETE_SHOT)
    elif frame < GLOBAL_HOLD_START:
        blend_camera(
            viewport,
            BASE_COMPLETE_SHOT,
            GLOBAL_SHOT,
            phase(frame, BASE_EXACT_FINAL_START, GLOBAL_HOLD_START - 1),
        )
    else:
        apply_camera(viewport, GLOBAL_SHOT)


def world_body_copy(temporary, occurrence, body_index=0):
    body = temporary.copy(occurrence.component.bRepBodies.item(body_index))
    if not temporary.transform(body, occurrence.transform2):
        raise RuntimeError("Could not transform graphics body into assembly space")
    return body


def add_graphic(group, body, color):
    graphic = group.addBRepBody(body)
    if graphic is None:
        raise RuntimeError("Could not add a custom graphics body")
    graphic.color = color
    graphic.isSelectable = False
    return graphic


def bounding_boxes_overlap(first, second):
    return not (
        first.maxPoint.x < second.minPoint.x
        or first.minPoint.x > second.maxPoint.x
        or first.maxPoint.y < second.minPoint.y
        or first.minPoint.y > second.maxPoint.y
        or first.maxPoint.z < second.minPoint.z
        or first.minPoint.z > second.maxPoint.z
    )


def create_lite3_local_context_bodies(root, temporary, robot):
    clip_center = added(STACK_CENTER, scaled(PLATE_UP, -2.0))
    clip_box = adsk.core.OrientedBoundingBox3D.create(
        point(clip_center),
        vector(WIDTH_AXIS),
        vector(MOUNT_NORMAL),
        14.0,
        12.0,
        18.0,
    )
    clip_body = temporary.createBox(clip_box)
    if clip_body is None:
        raise RuntimeError("Could not create the Lite3 local-context clip")
    clip_bounds = clip_body.boundingBox
    robot_path = robot.fullPathName
    local_bodies = []
    for occurrence_index in range(root.allOccurrences.count):
        occurrence = root.allOccurrences.item(occurrence_index)
        if not occurrence.fullPathName.startswith(robot_path):
            continue
        for body_index in range(occurrence.component.bRepBodies.count):
            proxy_body = occurrence.bRepBodies.item(body_index)
            if not bounding_boxes_overlap(proxy_body.boundingBox, clip_bounds):
                continue
            body = temporary.copy(
                occurrence.component.bRepBodies.item(body_index)
            )
            if not temporary.transform(body, occurrence.transform2):
                raise RuntimeError("Could not place a Lite3 local-context body")
            clip_copy = temporary.copy(clip_body)
            if not temporary.booleanOperation(
                body,
                clip_copy,
                adsk.fusion.BooleanTypes.IntersectionBooleanType,
            ):
                continue
            if body.volume > 1.0e-9:
                local_bodies.append(body)
    if not local_bodies:
        raise RuntimeError("The Lite3 local-context clip produced no solid bodies")
    return local_bodies


def create_section_body(temporary, occurrence, center):
    section_box = adsk.core.OrientedBoundingBox3D.create(
        point(center),
        vector(MOUNT_NORMAL),
        vector(PLATE_UP),
        3.2,
        3.2,
        0.75,
    )
    clip = temporary.createBox(section_box)
    section = world_body_copy(temporary, occurrence)
    if clip is None or not temporary.booleanOperation(
        section,
        clip,
        adsk.fusion.BooleanTypes.IntersectionBooleanType,
    ):
        raise RuntimeError("Could not create a local section body")
    return section


def create_arrow_bodies(temporary):
    side_offset = scaled(PLATE_UP, -0.95)
    start = added(
        UNDERSIDE_POINT,
        added(side_offset, scaled(MOUNT_NORMAL, -1.15)),
    )
    cone_base = added(
        TOPSIDE_POINT,
        added(side_offset, scaled(MOUNT_NORMAL, 0.55)),
    )
    shaft_end = added(cone_base, scaled(MOUNT_NORMAL, -0.26))
    arrow_tip = added(cone_base, scaled(MOUNT_NORMAL, 0.26))
    shaft = temporary.createCylinderOrCone(point(start), 0.055, point(shaft_end), 0.055)
    cone = temporary.createCylinderOrCone(point(shaft_end), 0.16, point(arrow_tip), 0.0)
    if shaft is None or cone is None:
        raise RuntimeError("Could not create the bottom-up direction arrow")
    return shaft, cone


def axis_transform(angle, axial_offset):
    axis = vector(MOUNT_NORMAL)
    axis.normalize()
    matrix = adsk.core.Matrix3D.create()
    matrix.setToRotation(angle, axis, point(AXIS_POINT))
    values = list(matrix.asArray())
    values[3] += MOUNT_NORMAL[0] * axial_offset
    values[7] += MOUNT_NORMAL[1] * axial_offset
    values[11] += MOUNT_NORMAL[2] * axial_offset
    if not matrix.setWithArray(values):
        raise RuntimeError("Could not create an axis transform")
    return matrix


def translated_matrix(matrix, offset):
    values = list(matrix.asArray())
    values[3] += offset[0]
    values[7] += offset[1]
    values[11] += offset[2]
    result = adsk.core.Matrix3D.create()
    if not result.setWithArray(values):
        raise RuntimeError("Could not add the preassembly placement offset")
    return result


def translation_matrix(offset):
    matrix = adsk.core.Matrix3D.create()
    values = list(matrix.asArray())
    values[3], values[7], values[11] = offset
    if not matrix.setWithArray(values):
        raise RuntimeError("Could not create the preassembly translation")
    return matrix


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


def mat_mul(first, second):
    return tuple(
        tuple(
            sum(first[row][index] * second[index][column] for index in range(3))
            for column in range(3)
        )
        for row in range(3)
    )


def tool_transform(angle, bolt_offset, approach_offset):
    flip = rodrigues(WIDTH_AXIS, math.pi)
    spin = rodrigues(MOUNT_NORMAL, angle)
    rotation = mat_mul(spin, flip)
    translation = added(
        UNDERSIDE_POINT,
        scaled(MOUNT_NORMAL, bolt_offset - approach_offset),
    )
    values = [0.0] * 16
    for row in range(3):
        for column in range(3):
            values[row * 4 + column] = rotation[row][column]
    values[3], values[7], values[11] = translation
    values[15] = 1.0
    matrix = adsk.core.Matrix3D.create()
    if not matrix.setWithArray(values):
        raise RuntimeError("Could not create the underside tool transform")
    return matrix


def bolt_state(frame):
    if frame < 36:
        return BOLT_START_OFFSET_CM, 0.0
    if frame <= 89:
        amount = phase(frame, 36, 89)
        return (
            lerp(BOLT_START_OFFSET_CM, BOLT_PRETIGHT_OFFSET_CM, amount),
            lerp(0.0, 2.0 * math.pi, amount),
        )
    if frame < 234:
        return BOLT_PRETIGHT_OFFSET_CM, 2.0 * math.pi
    if frame <= 293:
        stroke_frame = frame - 234
        stroke = min(3, stroke_frame // 15)
        local = stroke_frame % 15
        turn_amount = phase(local, 0, 9) if local <= 9 else 1.0
        accumulated_quarters = stroke + turn_amount
        return (
            BOLT_PRETIGHT_OFFSET_CM
            + QUARTER_TURN_ADVANCE_CM * accumulated_quarters,
            2.0 * math.pi + (math.pi * 0.5) * accumulated_quarters,
        )
    return 0.0, 4.0 * math.pi


def nut_state(frame):
    if frame < 132:
        return NUT_START_OFFSET_CM, 0.0
    if frame <= 185:
        amount = phase(frame, 132, 185)
        return (
            lerp(NUT_START_OFFSET_CM, 0.0, amount),
            lerp(0.0, -12.0 * math.pi, amount),
        )
    return 0.0, -12.0 * math.pi


def tool_state(frame, bolt_offset):
    base_angle = math.radians(TOOL_STROKE_START_DEG)
    if frame < 222 or frame >= 294:
        return False, base_angle, 0.8
    if frame < 234:
        return True, base_angle, lerp(0.8, 0.0, phase(frame, 222, 233))
    stroke_frame = frame - 234
    stroke = min(3, stroke_frame // 15)
    local = stroke_frame % 15
    if local <= 9:
        amount = phase(local, 0, 9)
        return True, base_angle + amount * math.pi * 0.5, 0.0
    if local <= 12:
        return (
            True,
            base_angle + math.pi * 0.5,
            lerp(0.0, 0.35, phase(local, 10, 12)),
        )
    return False, base_angle, 0.35


def base_axis_transform(axis_point, angle, axial_offset):
    matrix = adsk.core.Matrix3D.create()
    matrix.setToRotation(
        angle,
        vector((0.0, -1.0, 0.0)),
        point(axis_point),
    )
    values = list(matrix.asArray())
    values[7] += axial_offset
    if not matrix.setWithArray(values):
        raise RuntimeError("Could not create a Lite3 base-screw transform")
    return matrix


def base_driver_transform(head_point, angle, approach_offset):
    matrix = adsk.core.Matrix3D.create()
    matrix.setToRotation(
        angle,
        vector((0.0, -1.0, 0.0)),
        point((0.0, 0.0, 0.0)),
    )
    values = list(matrix.asArray())
    values[3] += head_point[0]
    values[7] += head_point[1] + approach_offset
    values[11] += head_point[2]
    if not matrix.setWithArray(values):
        raise RuntimeError("Could not place the Lite3 base-screw L-key")
    return matrix


def create_base_driver_bodies(temporary):
    shaft = temporary.createCylinderOrCone(
        point((0.0, 0.0, 0.0)),
        0.08,
        point((0.0, 9.5, 0.0)),
        0.08,
    )
    handle = temporary.createCylinderOrCone(
        point((0.0, 9.5, 0.0)),
        0.08,
        point((1.0, 9.5, 0.0)),
        0.08,
    )
    if shaft is None or handle is None:
        raise RuntimeError("Could not create the Lite3 base-screw L-key")
    return shaft, handle


def rear_spacer_state(frame):
    if frame < REAR_SPACER_START:
        return False, 3.0
    if frame <= REAR_SPACER_END:
        return True, lerp(
            3.0,
            0.0,
            phase(frame, REAR_SPACER_START, REAR_SPACER_END),
        )
    return True, 0.0


def base_screw_state(frame, start):
    local_frame = frame - start
    if local_frame < 0:
        return False, BASE_SCREW_START_OFFSET_CM, 0.0, False, 0.0
    if local_frame <= 8:
        return (
            True,
            lerp(
                BASE_SCREW_START_OFFSET_CM,
                BASE_SCREW_HAND_SEAT_OFFSET_CM,
                phase(local_frame, 0, 8),
            ),
            0.0,
            False,
            BASE_DRIVER_APPROACH_OFFSET_CM,
        )
    if local_frame <= 14:
        return (
            True,
            BASE_SCREW_HAND_SEAT_OFFSET_CM,
            0.0,
            True,
            lerp(
                BASE_DRIVER_APPROACH_OFFSET_CM,
                0.0,
                phase(local_frame, 9, 14),
            ),
        )
    if local_frame <= 31:
        amount = phase(local_frame, 15, 31)
        return (
            True,
            lerp(BASE_SCREW_HAND_SEAT_OFFSET_CM, 0.0, amount),
            lerp(0.0, BASE_SCREW_TIGHTENING_TURNS * 2.0 * math.pi, amount),
            True,
            0.0,
        )
    if local_frame < BASE_SCREW_OPERATION_FRAMES:
        return (
            True,
            0.0,
            BASE_SCREW_TIGHTENING_TURNS * 2.0 * math.pi,
            True,
            lerp(
                0.0,
                BASE_DRIVER_APPROACH_OFFSET_CM,
                phase(local_frame, 32, BASE_SCREW_OPERATION_FRAMES - 1),
            ),
        )
    return (
        True,
        0.0,
        BASE_SCREW_TIGHTENING_TURNS * 2.0 * math.pi,
        False,
        BASE_DRIVER_APPROACH_OFFSET_CM,
    )


def create_graphics(
    root,
    temporary,
    robot,
    carrier,
    guard,
    bolt,
    nut,
    tool,
    front_base_screws,
    rear_base_spacers,
    rear_base_screws,
):
    group = root.customGraphicsGroups.add()
    group.id = "S410_REV_C2_SINGLE_AXIS_FASTENING_VIDEO"
    group.isSelectable = False

    colors = {
        "carrier_full": color_effect(205, 211, 224, 0.16),
        "guard_full": color_effect(170, 188, 213, 0.13),
        "carrier_section": color_effect(205, 211, 224, 0.42),
        "guard_section": color_effect(170, 188, 213, 0.32),
        "carrier_final": color_effect(205, 211, 224, 1.0),
        "guard_final": color_effect(170, 188, 213, 1.0),
        "bolt": color_effect(244, 122, 35, 1.0),
        "nut": color_effect(74, 190, 95, 1.0),
        "tool": color_effect(40, 150, 245, 1.0),
        "base_screw": color_effect(244, 122, 35, 1.0),
        "base_spacer": color_effect(246, 200, 55, 1.0),
        "base_driver": color_effect(40, 150, 245, 1.0),
        "arrow": color_effect(40, 150, 245, 0.92),
        "lite3_context": color_effect(188, 195, 210, 0.30),
    }

    graphics = {
        "carrier_full": [
            add_graphic(group, world_body_copy(temporary, carrier), colors["carrier_full"])
        ],
        "guard_full": [
            add_graphic(group, world_body_copy(temporary, guard), colors["guard_full"])
        ],
        "carrier_section": [
            add_graphic(
                group,
                create_section_body(temporary, carrier, STACK_CENTER),
                colors["carrier_section"],
            )
        ],
        "guard_section": [
            add_graphic(
                group,
                create_section_body(temporary, guard, STACK_CENTER),
                colors["guard_section"],
            )
        ],
        "carrier_final": [
            add_graphic(group, world_body_copy(temporary, carrier), colors["carrier_final"])
        ],
        "guard_final": [
            add_graphic(group, world_body_copy(temporary, guard), colors["guard_final"])
        ],
        "bolt": [
            add_graphic(group, world_body_copy(temporary, bolt), colors["bolt"])
        ],
        "nut": [
            add_graphic(group, world_body_copy(temporary, nut), colors["nut"])
        ],
        "tool": [],
        "front_base_screws": [],
        "rear_base_spacers": [],
        "rear_base_screws": [],
        "base_driver": [],
        "arrow": [],
        "lite3_context": [],
    }
    for context_body in create_lite3_local_context_bodies(
        root, temporary, robot
    ):
        graphics["lite3_context"].append(
            add_graphic(
                group,
                context_body,
                colors["lite3_context"],
            )
        )
    for body_index in range(tool.component.bRepBodies.count):
        graphics["tool"].append(
            add_graphic(
                group,
                temporary.copy(tool.component.bRepBodies.item(body_index)),
                colors["tool"],
            )
        )
    for body_index in range(front_base_screws.component.bRepBodies.count):
        graphics["front_base_screws"].append(
            add_graphic(
                group,
                world_body_copy(temporary, front_base_screws, body_index),
                colors["base_screw"],
            )
        )
    for body_index in range(rear_base_spacers.component.bRepBodies.count):
        graphics["rear_base_spacers"].append(
            add_graphic(
                group,
                world_body_copy(temporary, rear_base_spacers, body_index),
                colors["base_spacer"],
            )
        )
    for body_index in range(rear_base_screws.component.bRepBodies.count):
        graphics["rear_base_screws"].append(
            add_graphic(
                group,
                world_body_copy(temporary, rear_base_screws, body_index),
                colors["base_screw"],
            )
        )
    for driver_body in create_base_driver_bodies(temporary):
        graphics["base_driver"].append(
            add_graphic(group, driver_body, colors["base_driver"])
        )
    for arrow_body in create_arrow_bodies(temporary):
        graphics["arrow"].append(
            add_graphic(group, arrow_body, colors["arrow"])
        )
    return group, graphics


def set_graphic_visibility(items, visible):
    for item in items:
        item.isVisible = visible


def set_animation_state(graphics, frame):
    if frame >= BASE_EXACT_FINAL_START:
        for items in graphics.values():
            set_graphic_visibility(items, False)
        return

    before_base_fastening = frame < BASE_SCREW_STARTS[0]
    base_fastening_mode = BASE_SCREW_STARTS[0] <= frame < BASE_FINAL_CLOSE_START
    section_mode = frame < 24
    mounted_opaque_mode = 330 <= frame < BASE_SCREW_STARTS[0]
    set_graphic_visibility(graphics["carrier_section"], section_mode)
    set_graphic_visibility(graphics["guard_section"], section_mode)
    set_graphic_visibility(
        graphics["carrier_full"],
        base_fastening_mode
        or (
            before_base_fastening
            and not section_mode
            and not mounted_opaque_mode
        ),
    )
    set_graphic_visibility(
        graphics["guard_full"],
        before_base_fastening and not section_mode and not mounted_opaque_mode,
    )
    set_graphic_visibility(graphics["carrier_final"], mounted_opaque_mode)
    set_graphic_visibility(graphics["guard_final"], mounted_opaque_mode)
    set_graphic_visibility(
        graphics["lite3_context"],
        frame < 24 or REAR_SPACER_START <= frame < BASE_SCREW_STARTS[0],
    )
    set_graphic_visibility(graphics["arrow"], frame < 90)

    current_assembly_offset = assembly_offset(frame)
    current_assembly_matrix = translation_matrix(current_assembly_offset)
    for name in (
        "carrier_full",
        "guard_full",
        "carrier_section",
        "guard_section",
        "carrier_final",
        "guard_final",
        "arrow",
    ):
        for item in graphics[name]:
            item.transform = current_assembly_matrix

    bolt_offset, bolt_angle = bolt_state(frame)
    nut_offset, nut_angle = nut_state(frame)
    bolt_matrix = translated_matrix(
        axis_transform(bolt_angle, bolt_offset), current_assembly_offset
    )
    nut_matrix = translated_matrix(
        axis_transform(nut_angle, nut_offset), current_assembly_offset
    )
    for item in graphics["bolt"]:
        item.transform = bolt_matrix
        item.isVisible = before_base_fastening
    for item in graphics["nut"]:
        item.transform = nut_matrix
        item.isVisible = before_base_fastening

    tool_visible, tool_angle, tool_approach = tool_state(frame, bolt_offset)
    current_tool_matrix = translated_matrix(
        tool_transform(tool_angle, bolt_offset, tool_approach),
        current_assembly_offset,
    )
    for item in graphics["tool"]:
        item.transform = current_tool_matrix
        item.isVisible = tool_visible and before_base_fastening

    spacer_visible, spacer_offset = rear_spacer_state(frame)
    spacer_matrix = translation_matrix((0.0, spacer_offset, 0.0))
    for item in graphics["rear_base_spacers"]:
        item.transform = spacer_matrix
        item.isVisible = spacer_visible

    operations = (
        (
            graphics["front_base_screws"][0],
            FRONT_BASE_AXIS_POINTS[0],
            FRONT_BASE_HEAD_POINTS[0],
            BASE_SCREW_STARTS[0],
        ),
        (
            graphics["front_base_screws"][1],
            FRONT_BASE_AXIS_POINTS[1],
            FRONT_BASE_HEAD_POINTS[1],
            BASE_SCREW_STARTS[1],
        ),
        (
            graphics["rear_base_screws"][0],
            REAR_BASE_AXIS_POINTS[0],
            REAR_BASE_HEAD_POINTS[0],
            BASE_SCREW_STARTS[2],
        ),
        (
            graphics["rear_base_screws"][1],
            REAR_BASE_AXIS_POINTS[1],
            REAR_BASE_HEAD_POINTS[1],
            BASE_SCREW_STARTS[3],
        ),
    )
    active_driver = None
    for screw_graphic, axis_point, head_point, start in operations:
        (
            screw_visible,
            screw_offset,
            screw_angle,
            driver_visible,
            driver_approach,
        ) = base_screw_state(frame, start)
        screw_graphic.transform = base_axis_transform(
            axis_point,
            screw_angle,
            screw_offset,
        )
        screw_graphic.isVisible = screw_visible
        if driver_visible:
            active_driver = base_driver_transform(
                head_point,
                screw_angle,
                driver_approach,
            )
    for item in graphics["base_driver"]:
        item.isVisible = active_driver is not None
        if active_driver is not None:
            item.transform = active_driver


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    found = {}
    guard = None
    official_guard = None
    robot = occurrences.item(0)
    if "Lite3" not in robot.component.name:
        raise RuntimeError("Root occurrence 0 is not the Lite3 assembly")
    for index in range(occurrences.count):
        occurrence = occurrences.item(index)
        name = occurrence.component.name
        if name == CARRIER_NAME:
            found["carrier"] = occurrence
        elif name == BOLT_NAME:
            found["bolt"] = occurrence
        elif name == NUT_NAME:
            found["nut"] = occurrence
        elif name == TOOL_NAME:
            found["tool"] = occurrence
        elif name == FRONT_BASE_SCREWS_NAME:
            found["front_base_screws"] = occurrence
        elif name == REAR_BASE_SPACERS_NAME:
            found["rear_base_spacers"] = occurrence
        elif name == REAR_BASE_SCREWS_NAME:
            found["rear_base_screws"] = occurrence
        elif name == GUARD_ACCESS_CANDIDATE_NAME:
            guard = occurrence
        elif index == 3 and "S410" in name:
            official_guard = occurrence
    if guard is None:
        guard = official_guard
    expected = {
        "carrier",
        "bolt",
        "nut",
        "tool",
        "front_base_screws",
        "rear_base_spacers",
        "rear_base_screws",
    }
    if set(found) != expected or guard is None:
        raise RuntimeError("Corrected single-axis video scene is incomplete")

    original_visibility = [
        bool(occurrences.item(index).isLightBulbOn)
        for index in range(occurrences.count)
    ]
    viewport = application.activeViewport
    original_camera = camera_snapshot(viewport)
    temporary = adsk.fusion.TemporaryBRepManager.get()
    graphics_group = None
    rendered_frames = []
    error_text = None
    try:
        for index in range(occurrences.count):
            occurrences.item(index).isLightBulbOn = False
        graphics_group, graphics = create_graphics(
            root,
            temporary,
            robot,
            found["carrier"],
            guard,
            found["bolt"],
            found["nut"],
            found["tool"],
            found["front_base_screws"],
            found["rear_base_spacers"],
            found["rear_base_screws"],
        )
        frames = FRAME_LIST if FRAME_LIST is not None else range(FRAME_START, FRAME_END)
        for frame in frames:
            assembled_scene_mode = frame >= BASE_SCREW_STARTS[0]
            exact_final_mode = frame >= BASE_EXACT_FINAL_START
            for index, final_visible in enumerate(original_visibility):
                occurrence = occurrences.item(index)
                visible = final_visible if assembled_scene_mode else False
                if (
                    assembled_scene_mode
                    and not exact_final_mode
                    and occurrence.component.name
                    in {
                        FRONT_BASE_SCREWS_NAME,
                        REAR_BASE_SPACERS_NAME,
                        REAR_BASE_SCREWS_NAME,
                    }
                ):
                    visible = False
                if (
                    BASE_SCREW_STARTS[0] <= frame < BASE_FINAL_CLOSE_START
                    and occurrence.component.name == CARRIER_NAME
                ):
                    visible = False
                if (
                    BASE_SCREW_STARTS[0] <= frame < BASE_FINAL_CLOSE_START
                    and "D435I" in occurrence.component.name.upper()
                ):
                    visible = False
                occurrence.isLightBulbOn = visible
            set_animation_state(graphics, frame)
            set_animation_camera(viewport, frame)
            viewport.refresh()
            adsk.doEvents()
            output_path = os.path.join(OUTPUT_DIR, "frame_%04d.png" % frame)
            if not viewport.saveAsImageFile(output_path, FRAME_WIDTH, FRAME_HEIGHT):
                raise RuntimeError("Could not render " + output_path)
            rendered_frames.append(frame)
    except Exception:
        error_text = traceback.format_exc()
        raise
    finally:
        if graphics_group is not None and graphics_group.isValid:
            graphics_group.deleteMe()
        for index, visible in enumerate(original_visibility):
            occurrences.item(index).isLightBulbOn = visible
        restore_camera(viewport, original_camera)
        viewport.refresh()
        adsk.doEvents()

        report = {
            "frame_start": FRAME_START,
            "frame_end": FRAME_END,
            "frame_list": FRAME_LIST,
            "rendered_frames": rendered_frames,
            "rendered_count": len(rendered_frames),
            "frame_size": [FRAME_WIDTH, FRAME_HEIGHT],
            "output_dir": OUTPUT_DIR,
            "sequence": {
                "off_robot_preassembly_outboard_of_lite3": [0, 293],
                "preassembly_standoff_mm": PREASSEMBLY_STANDOFF_CM * 10.0,
                "bolt_bottom_up": [36, 89],
                "bolt_pre_tight_gap_mm": abs(BOLT_PRETIGHT_OFFSET_CM) * 10.0,
                "nut_top_down_six_turns": [132, 185],
                "short_l_key_approach_from_underside": [222, 233],
                "four_quarter_turn_bolt_tightening_strokes": [234, 293],
                "rear_locating_spacers_placed_before_stack": [
                    REAR_SPACER_START,
                    REAR_SPACER_END,
                ],
                "fastened_stack_lowered_onto_lite3": [
                    STACK_MOUNT_START,
                    STACK_MOUNT_END,
                ],
                "front_left_m3x8_base_screw": [348, 383],
                "front_right_m3x8_base_screw": [384, 419],
                "rear_left_m3x12_base_screw": [426, 461],
                "rear_right_m3x12_base_screw": [462, 497],
                "opaque_local_base_connection": [
                    BASE_FINAL_CLOSE_START,
                    BASE_EXACT_FINAL_START - 1,
                ],
                "exact_final_scene_and_global_pullback": [
                    BASE_EXACT_FINAL_START,
                    TOTAL_FRAME_COUNT - 1,
                ],
                "lite3_context_visible_during_overview_and_mount": True,
                "total_final_bolt_advance_mm": M5_PITCH_CM * 10.0,
                "base_screw_driver_visual_only": True,
                "base_screw_driver_type": "long_reach_hex_key",
                "base_screw_torque_claim": False,
                "guard_front_base_access_channels": {
                    "count": 2,
                    "diameter_mm": 7.0,
                    "full_depth": True,
                    "official_cad": False,
                    "component": GUARD_ACCESS_CANDIDATE_NAME,
                },
                "receiver_engagement_is_visual_candidate": True,
                "text_overlay": False,
            },
            "scene_restored": True,
            "error": error_text,
        }
        suffix = "preview" if FRAME_LIST is not None else "%04d_%04d" % (FRAME_START, FRAME_END)
        with open(
            os.path.join(OUTPUT_ROOT, "render_report_%s.json" % suffix),
            "w",
            encoding="utf-8",
        ) as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    print(json.dumps(report, ensure_ascii=False))
