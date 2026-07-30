"""Render restart step 01: D435i directly threaded to bare J17A.

Only the J17A carrier, official D435i BRep, and two independent visual M3x5
screws appear.  Each screw approaches from the J17A side, passes through the
J17A 3.2 mm clearance hole, rotates, and enters the camera's own rear M3
thread.  No nut, J20A, MID360, S410, robot, or later fastener is shown.
"""

import adsk.core
import adsk.fusion
import json
import math
import os


FRAME_START = globals().get("FRAME_START", 0)
FRAME_END = globals().get("FRAME_END", 264)
FRAME_LIST = globals().get("FRAME_LIST")
FRAME_WIDTH = globals().get("FRAME_WIDTH", 1280)
FRAME_HEIGHT = globals().get("FRAME_HEIGHT", 720)

OUTPUT_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-installation-restart-01-j17a-d435i-direct-thread/frames"
)

J17A_INDEX = 1
D435I_INDEX = 15
SCREW_INDICES = (16, 17)
VISIBLE_INDICES = (J17A_INDEX, D435I_INDEX, *SCREW_INDICES)

CAMERA_AXIS = (0.0, -0.34202014332566627, 0.9396926207859093)
CAMERA_UP = (0.0, 0.9396926207859093, 0.34202014332566627)
WIDTH_AXIS = (1.0, 0.0, 0.0)

SCREW_AXIS_POINTS = {
    16: (-32.697009644681464, 21.835352488197586, 262.0531323590644),
    17: (-28.197009644681464, 21.835352488197586, 262.0531323590644),
}

J17A_ONLY_TARGET = (-30.447009644681465, 21.0, 256.8)
ASSEMBLY_TARGET = (-30.447009644681465, 21.4, 261.0)


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
    return tuple(first[i] + second[i] for i in range(3))


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


def apply_camera(viewport, target, direction, extents, up=CAMERA_UP):
    direction = normalized(direction)
    eye = shifted(target, scaled(direction, 28.0))
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
    rotation = rodrigues(CAMERA_AXIS, angle)
    rotated_orientation = mat_mul(rotation, final_rotation)
    relative_translation = tuple(
        final_translation[index] - axis_point[index] for index in range(3)
    )
    rotated_relative = mat_vec(rotation, relative_translation)
    translation = tuple(
        axis_point[index]
        + rotated_relative[index]
        + CAMERA_AXIS[index] * axial_offset
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
        return False, -2.0, 0.0
    if frame <= end:
        amount = phase(frame, begin, end)
        return True, -2.0 * (1.0 - amount), 8.0 * math.pi * amount
    return True, 0.0, 8.0 * math.pi


def set_scene_state(occurrences, final_transforms, frame, opacity_records):
    for index in range(occurrences.count):
        occurrences.item(index).isLightBulbOn = False

    j17a = occurrences.item(J17A_INDEX)
    j17a.transform = matrix_from_values(final_transforms[J17A_INDEX])
    j17a.isLightBulbOn = True

    camera_amount = phase(frame, 24, 71)
    camera_offset = scaled(CAMERA_AXIS, 4.5 * (1.0 - camera_amount))
    set_offset_occurrence(
        occurrences.item(D435I_INDEX),
        final_transforms[D435I_INDEX],
        frame >= 24,
        camera_offset,
    )

    first_visible, first_offset, first_angle = screw_state(frame, 80, 127)
    second_visible, second_offset, second_angle = screw_state(frame, 128, 175)
    set_rotating_screw(
        occurrences.item(16),
        final_transforms[16],
        first_visible,
        SCREW_AXIS_POINTS[16],
        first_offset,
        first_angle,
    )
    set_rotating_screw(
        occurrences.item(17),
        final_transforms[17],
        second_visible,
        SCREW_AXIS_POINTS[17],
        second_offset,
        second_angle,
    )

    for body, opacity in opacity_records:
        body.opacity = opacity
    if 80 <= frame <= 175:
        for body in component_bodies(j17a.component):
            body.opacity = 0.42
        for body in component_bodies(occurrences.item(D435I_INDEX).component):
            body.opacity = 0.30


def set_scene_camera(viewport, frame):
    if frame < 24:
        direction = (-0.65, 1.0, 0.60)
        apply_camera(
            viewport,
            J17A_ONLY_TARGET,
            direction,
            16.0,
            up=(0.0, 0.0, 1.0),
        )
    elif frame < 80:
        direction = shifted(
            CAMERA_AXIS,
            shifted(scaled(WIDTH_AXIS, 0.72), scaled(CAMERA_UP, 0.35)),
        )
        apply_camera(viewport, ASSEMBLY_TARGET, direction, 14.5)
    elif frame < 128:
        target = shifted(SCREW_AXIS_POINTS[16], scaled(CAMERA_AXIS, -0.75))
        direction = shifted(
            scaled(CAMERA_AXIS, -1.0),
            shifted(scaled(WIDTH_AXIS, -0.85), scaled(CAMERA_UP, 0.20)),
        )
        apply_camera(viewport, target, direction, 5.5)
    elif frame < 176:
        target = shifted(SCREW_AXIS_POINTS[17], scaled(CAMERA_AXIS, -0.75))
        direction = shifted(
            scaled(CAMERA_AXIS, -1.0),
            shifted(scaled(WIDTH_AXIS, 0.85), scaled(CAMERA_UP, 0.20)),
        )
        apply_camera(viewport, target, direction, 5.5)
    elif frame < 216:
        direction = shifted(
            scaled(CAMERA_AXIS, -0.85),
            shifted(scaled(WIDTH_AXIS, 0.75), scaled(CAMERA_UP, 0.20)),
        )
        apply_camera(viewport, ASSEMBLY_TARGET, direction, 13.0)
    else:
        direction = shifted(
            CAMERA_AXIS,
            shifted(scaled(WIDTH_AXIS, 0.80), scaled(CAMERA_UP, 0.45)),
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
    expected_names = {
        1: "J17A_ORIGINAL_MANUFACTURER_BREP_CORRECT_UPPER_65MM_PAIR",
        15: "LITE3_FULLSTACK_D435I_REAL_BREP_OFFICIAL_MANUFACTURER_CAD",
        16: (
            "LITE3_FULLSTACK_D435I_M3x5_DIRECT_SCREW_1_"
            "J17A_TO_CAMERA_THREAD_VISUAL_CANDIDATE"
        ),
        17: (
            "LITE3_FULLSTACK_D435I_M3x5_DIRECT_SCREW_2_"
            "J17A_TO_CAMERA_THREAD_VISUAL_CANDIDATE"
        ),
    }
    for index, name in expected_names.items():
        if occurrences.item(index).component.name != name:
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
    for index in (J17A_INDEX, D435I_INDEX):
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
                    "camera_approach": [24, 71],
                    "screw_1_direct_thread": [80, 127],
                    "screw_2_direct_thread": [128, 175],
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
