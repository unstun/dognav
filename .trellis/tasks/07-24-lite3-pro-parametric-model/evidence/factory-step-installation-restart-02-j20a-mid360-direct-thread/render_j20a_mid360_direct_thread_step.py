"""Render restart step 02: MID360 directly threaded to bare J20A.

Only the J20A second-layer bracket, the official Livox MID360 BRep, and four
independent visual M3x8 screw candidates appear.  The sensor first approaches
its modeled mounting position.  The screws then approach from the underside of
J20A and rotate into the MID360 mounting receivers in a diagonal cross sequence.
No J17A, D435i, S410, robot, nut, or unrelated fastener is shown.
"""

import adsk.core
import adsk.fusion
import json
import math
import os


FRAME_START = globals().get("FRAME_START", 0)
FRAME_END = globals().get("FRAME_END", 312)
FRAME_LIST = globals().get("FRAME_LIST")
FRAME_WIDTH = globals().get("FRAME_WIDTH", 1280)
FRAME_HEIGHT = globals().get("FRAME_HEIGHT", 720)

OUTPUT_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-installation-restart-02-j20a-mid360-direct-thread/frames"
)

J20A_INDEX = 2
MID360_INDEX = 4
SCREW_INDICES = (11, 12, 13, 14)
VISIBLE_INDICES = (J20A_INDEX, MID360_INDEX, *SCREW_INDICES)

MOUNT_NORMAL = (0.0, 0.9659258262890683, 0.25881904510252074)
PLATE_UP = (0.0, -0.25881904510252074, 0.9659258262890683)
WIDTH_AXIS = (1.0, 0.0, 0.0)

SCREW_AXIS_POINTS = {
    11: (-32.24700964468146, 21.452842807920245, 258.6723716491626),
    12: (-28.647009644681464, 21.452842807920245, 258.6723716491626),
    13: (-28.647009644681464, 22.69517422441234, 254.03592768297506),
    14: (-32.24700964468146, 22.69517422441234, 254.03592768297506),
}

# Tighten the two diagonals in turn: upper-left -> lower-right -> upper-right
# -> lower-left.  Each screw remains present after it reaches its final pose.
SCREW_SEQUENCE = (
    (11, 80, 115),
    (13, 116, 151),
    (12, 152, 187),
    (14, 188, 223),
)

J20A_ONLY_TARGET = (-30.44700964468146, 17.7, 255.0)
ASSEMBLY_TARGET = (-30.44700964468146, 22.8, 256.4)


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def phase(frame, start, end):
    if frame <= start:
        return 0.0
    if frame >= end:
        return 1.0
    return smoothstep((frame - start) / float(end - start))


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


def apply_camera(viewport, target, direction, extents, up=PLATE_UP):
    direction = normalized(direction)
    eye = shifted(target, scaled(direction, 32.0))
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


def set_rotating_screw(
    occurrence,
    final_values,
    visible,
    axis_point,
    axial_offset,
    angle,
):
    final_rotation = tuple(
        tuple(final_values[row * 4 + column] for column in range(3))
        for row in range(3)
    )
    final_translation = (final_values[3], final_values[7], final_values[11])
    rotation = rodrigues(MOUNT_NORMAL, angle)
    rotated_orientation = mat_mul(rotation, final_rotation)
    relative_translation = tuple(
        final_translation[index] - axis_point[index] for index in range(3)
    )
    rotated_relative = mat_vec(rotation, relative_translation)
    translation = tuple(
        axis_point[index]
        + rotated_relative[index]
        + MOUNT_NORMAL[index] * axial_offset
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


def screw_state(frame, begin, end):
    if frame < begin:
        return False, -2.2, 0.0
    if frame <= end:
        amount = phase(frame, begin, end)
        return True, -2.2 * (1.0 - amount), 8.0 * math.pi * amount
    return True, 0.0, 8.0 * math.pi


def set_scene_state(occurrences, final_transforms, frame, opacity_records):
    for index in range(occurrences.count):
        occurrences.item(index).isLightBulbOn = False

    j20a = occurrences.item(J20A_INDEX)
    j20a.transform = matrix_from_values(final_transforms[J20A_INDEX])
    j20a.isLightBulbOn = True

    sensor_amount = phase(frame, 24, 71)
    sensor_offset = scaled(MOUNT_NORMAL, 5.5 * (1.0 - sensor_amount))
    set_offset_occurrence(
        occurrences.item(MID360_INDEX),
        final_transforms[MID360_INDEX],
        frame >= 24,
        sensor_offset,
    )

    for screw_index, begin, end in SCREW_SEQUENCE:
        visible, offset, angle = screw_state(frame, begin, end)
        set_rotating_screw(
            occurrences.item(screw_index),
            final_transforms[screw_index],
            visible,
            SCREW_AXIS_POINTS[screw_index],
            offset,
            angle,
        )

    for body, opacity in opacity_records:
        body.opacity = opacity
    if 80 <= frame <= 223:
        for body in component_bodies(j20a.component):
            body.opacity = 0.42
        for body in component_bodies(occurrences.item(MID360_INDEX).component):
            body.opacity = 0.28


def screw_camera(viewport, screw_index, width_sign):
    target = shifted(
        SCREW_AXIS_POINTS[screw_index],
        scaled(MOUNT_NORMAL, -0.75),
    )
    direction = shifted(
        scaled(MOUNT_NORMAL, -1.0),
        shifted(scaled(WIDTH_AXIS, width_sign * 0.72), scaled(PLATE_UP, 0.28)),
    )
    apply_camera(viewport, target, direction, 5.4)


def set_scene_camera(viewport, frame):
    if frame < 24:
        direction = shifted(
            MOUNT_NORMAL,
            shifted(scaled(WIDTH_AXIS, 0.72), scaled(PLATE_UP, 0.38)),
        )
        apply_camera(viewport, J20A_ONLY_TARGET, direction, 12.5)
    elif frame < 80:
        direction = shifted(
            MOUNT_NORMAL,
            shifted(scaled(WIDTH_AXIS, 0.78), scaled(PLATE_UP, 0.34)),
        )
        apply_camera(viewport, ASSEMBLY_TARGET, direction, 14.5)
    elif frame < 116:
        screw_camera(viewport, 11, -1.0)
    elif frame < 152:
        screw_camera(viewport, 13, 1.0)
    elif frame < 188:
        screw_camera(viewport, 12, 1.0)
    elif frame < 224:
        screw_camera(viewport, 14, -1.0)
    elif frame < 256:
        direction = shifted(
            scaled(MOUNT_NORMAL, -1.0),
            shifted(scaled(WIDTH_AXIS, 0.62), scaled(PLATE_UP, 0.22)),
        )
        apply_camera(viewport, ASSEMBLY_TARGET, direction, 13.5)
    else:
        direction = shifted(
            MOUNT_NORMAL,
            shifted(scaled(WIDTH_AXIS, 0.82), scaled(PLATE_UP, 0.46)),
        )
        apply_camera(viewport, ASSEMBLY_TARGET, direction, 15.0)


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences
    if occurrences.count != 34:
        raise RuntimeError(
            "Expected 34 root occurrences, found " + str(occurrences.count)
        )
    # Keep the J20A check ASCII-only because the Fusion MCP script transport
    # does not preserve non-ASCII string literals byte-for-byte.
    expected_names = {
        2: "1T21-J20A-",
        4: "MID-360_4_ASM",
        11: (
            "LITE3_FULLSTACK_MID360_M3x8_UNDERSIDE_SCREW_1_"
            "J20F11_TO_MIDB2_VISUAL_CANDIDATE"
        ),
        12: (
            "LITE3_FULLSTACK_MID360_M3x8_UNDERSIDE_SCREW_2_"
            "J20F12_TO_MIDB0_VISUAL_CANDIDATE"
        ),
        13: (
            "LITE3_FULLSTACK_MID360_M3x8_UNDERSIDE_SCREW_3_"
            "J20F13_TO_MIDB1_VISUAL_CANDIDATE"
        ),
        14: (
            "LITE3_FULLSTACK_MID360_M3x8_UNDERSIDE_SCREW_4_"
            "J20F14_TO_MIDB3_VISUAL_CANDIDATE"
        ),
    }
    for index, name in expected_names.items():
        actual_name = occurrences.item(index).component.name
        matches = actual_name.startswith(name) if index == 2 else actual_name == name
        if not matches:
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
    for index in (J20A_INDEX, MID360_INDEX):
        for body in component_bodies(occurrences.item(index).component):
            opacity_records.append((body, body.opacity))
    viewport = app.activeViewport
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

    max_transform_difference = 0.0
    visibility_mismatches = []
    for index in range(occurrences.count):
        actual = list(occurrences.item(index).transform.asArray())
        expected = final_transforms[index]
        max_transform_difference = max(
            max_transform_difference,
            max(abs(actual[i] - expected[i]) for i in range(16)),
        )
        if bool(occurrences.item(index).isLightBulbOn) != final_visibility[index]:
            visibility_mismatches.append(index)

    print(
        json.dumps(
            {
                "frames_rendered": rendered,
                "output_dir": OUTPUT_DIR,
                "visible_animation_components": list(VISIBLE_INDICES),
                "sequence": {
                    "mid360_approach_to_modeled_mount_position": [24, 71],
                    "cross_tightening_order": [11, 13, 12, 14],
                    "screw_intervals": {
                        str(index): [begin, end]
                        for index, begin, end in SCREW_SEQUENCE
                    },
                    "nuts": 0,
                },
                "restored": {
                    "max_transform_difference": max_transform_difference,
                    "visibility_mismatches": visibility_mismatches,
                    "pending_snapshot": bool(design.snapshots.hasPendingSnapshot),
                },
            }
        )
    )
