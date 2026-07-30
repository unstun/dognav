"""Render the reviewed Lite3 sensor-stack installation as PNG frames in Fusion.

The script is evaluated inside Fusion's Python runtime.  The caller may inject
FRAME_START and FRAME_END (end-exclusive) into the execution globals so the
render can be split into short, recoverable batches.
"""

import adsk.core
import adsk.fusion
import json
import math
import os


FRAME_START = globals().get("FRAME_START", 0)
FRAME_END = globals().get("FRAME_END", 360)
FRAME_WIDTH = globals().get("FRAME_WIDTH", 1280)
FRAME_HEIGHT = globals().get("FRAME_HEIGHT", 720)

OUTPUT_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-full-installation-animation-with-lite3-correct-base/frames"
)

ATTRIBUTE_GROUP = "codex_full_installation_animation"
FINAL_TRANSFORM_ATTRIBUTE = "final_transform"
FINAL_VISIBILITY_ATTRIBUTE = "final_visibility"

FULL_EYE = (-149.75, 247.0, 337.0)
FULL_TARGET = (-29.75, 12.0, 237.0)
FULL_EXTENTS = 82.0

CLOSE_EYE = (-47.0, 52.0, 269.0)
CLOSE_TARGET = (-30.447009644681465, 19.5, 255.5)
CLOSE_EXTENTS = 24.0


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def phase(frame, start, end):
    if frame <= start:
        return 0.0
    if frame >= end:
        return 1.0
    return smoothstep((frame - start) / float(end - start))


def lerp(a, b, amount):
    return a + (b - a) * amount


def lerp3(a, b, amount):
    return tuple(lerp(a[i], b[i], amount) for i in range(3))


def ensure_final_state_attributes(occurrence):
    transform_attr = occurrence.attributes.itemByName(
        ATTRIBUTE_GROUP, FINAL_TRANSFORM_ATTRIBUTE
    )
    if transform_attr is None:
        occurrence.attributes.add(
            ATTRIBUTE_GROUP,
            FINAL_TRANSFORM_ATTRIBUTE,
            json.dumps(list(occurrence.transform.asArray())),
        )

    visibility_attr = occurrence.attributes.itemByName(
        ATTRIBUTE_GROUP, FINAL_VISIBILITY_ATTRIBUTE
    )
    if visibility_attr is None:
        occurrence.attributes.add(
            ATTRIBUTE_GROUP,
            FINAL_VISIBILITY_ATTRIBUTE,
            "true" if occurrence.isLightBulbOn else "false",
        )


def final_transform_array(occurrence):
    attr = occurrence.attributes.itemByName(
        ATTRIBUTE_GROUP, FINAL_TRANSFORM_ATTRIBUTE
    )
    if attr is None:
        raise RuntimeError(
            "Missing animation final-transform attribute on "
            + occurrence.fullPathName
        )
    return json.loads(attr.value)


def set_occurrence(occurrence, visible, offset=(0.0, 0.0, 0.0)):
    values = final_transform_array(occurrence)
    values[3] += offset[0]
    values[7] += offset[1]
    values[11] += offset[2]
    matrix = adsk.core.Matrix3D.create()
    matrix.setWithArray(values)
    occurrence.transform = matrix
    occurrence.isLightBulbOn = visible


def scaled(vector, amount):
    return tuple(component * amount for component in vector)


def set_camera(viewport, eye, target, extents):
    camera = viewport.camera
    camera.isSmoothTransition = False
    camera.cameraType = adsk.core.CameraTypes.OrthographicCameraType
    camera.eye = adsk.core.Point3D.create(*eye)
    camera.target = adsk.core.Point3D.create(*target)
    camera.upVector = adsk.core.Vector3D.create(0.0, 0.0, 1.0)
    camera.viewExtents = extents
    viewport.camera = camera


def set_animation_camera(viewport, frame):
    if frame < 24:
        set_camera(viewport, FULL_EYE, FULL_TARGET, FULL_EXTENTS)
        return

    if frame <= 47:
        amount = phase(frame, 24, 47)
        set_camera(
            viewport,
            lerp3(FULL_EYE, CLOSE_EYE, amount),
            lerp3(FULL_TARGET, CLOSE_TARGET, amount),
            lerp(FULL_EXTENTS, CLOSE_EXTENTS, amount),
        )
        return

    if frame < 326:
        set_camera(viewport, CLOSE_EYE, CLOSE_TARGET, CLOSE_EXTENTS)
        return

    if frame <= 349:
        amount = phase(frame, 326, 349)
        set_camera(
            viewport,
            lerp3(CLOSE_EYE, FULL_EYE, amount),
            lerp3(CLOSE_TARGET, FULL_TARGET, amount),
            lerp(CLOSE_EXTENTS, FULL_EXTENTS, amount),
        )
        return

    set_camera(viewport, FULL_EYE, FULL_TARGET, FULL_EXTENTS)


def set_animation_state(occurrences, frame):
    # Lite3 is the fixed reference throughout the animation.
    set_occurrence(occurrences.item(0), True)

    # Rejected/proxy geometry and the unused guard remain hidden.
    for index in (3, 5, 6):
        set_occurrence(occurrences.item(index), False)

    # J17A/base descends onto the already reviewed four Lite3 mounting points.
    amount = phase(frame, 48, 77)
    set_occurrence(
        occurrences.item(1),
        frame >= 48,
        scaled((0.0, 10.0, 0.0), 1.0 - amount),
    )

    # Rear locating spacers seat first.
    amount = phase(frame, 78, 95)
    set_occurrence(
        occurrences.item(25),
        frame >= 78,
        scaled((0.0, 4.0, 0.0), 1.0 - amount),
    )

    # Four base-to-Lite3 screws then insert from above.
    amount = phase(frame, 96, 119)
    base_screw_offset = scaled((0.0, 5.0, 0.0), 1.0 - amount)
    for index in (24, 26):
        set_occurrence(
            occurrences.item(index), frame >= 96, base_screw_offset
        )

    # J20A/second bracket descends onto J17A.
    amount = phase(frame, 120, 149)
    set_occurrence(
        occurrences.item(2),
        frame >= 120,
        scaled((0.0, 8.0, 0.0), 1.0 - amount),
    )

    # Four lower bolts rise through the paired front and rear bracket holes.
    amount = phase(frame, 150, 173)
    lower_bolt_offset = scaled((0.0, -5.0, 0.0), 1.0 - amount)
    for index in (7, 8, 18, 19):
        set_occurrence(
            occurrences.item(index), frame >= 150, lower_bolt_offset
        )

    # Top nuts, washers, and locknuts descend to clamp both brackets.
    amount = phase(frame, 174, 197)
    upper_fastener_offset = scaled((0.0, 5.0, 0.0), 1.0 - amount)
    for index in (9, 10, 20, 21, 22, 23):
        set_occurrence(
            occurrences.item(index),
            frame >= 174,
            upper_fastener_offset,
        )

    # MID360 approaches along its tilted mount normal.
    amount = phase(frame, 198, 227)
    mid360_normal = (0.0, 0.9659258262890683, 0.25881904510252074)
    set_occurrence(
        occurrences.item(4),
        frame >= 198,
        scaled(mid360_normal, 8.0 * (1.0 - amount)),
    )

    # Four underside MID360 screws insert along the opposite mount normal.
    amount = phase(frame, 228, 251)
    mid360_screw_offset = scaled(mid360_normal, -4.0 * (1.0 - amount))
    for index in (11, 12, 13, 14):
        set_occurrence(
            occurrences.item(index),
            frame >= 228,
            mid360_screw_offset,
        )

    # D435i approaches along its own tilted optical/mount direction.
    amount = phase(frame, 252, 281)
    camera_axis = (0.0, -0.34202014332566627, 0.9396926207859093)
    set_occurrence(
        occurrences.item(15),
        frame >= 252,
        scaled(camera_axis, 8.0 * (1.0 - amount)),
    )

    # Two camera screws insert from the camera side into the J17A threads.
    amount = phase(frame, 282, 301)
    camera_screw_offset = scaled(camera_axis, 4.0 * (1.0 - amount))
    for index in (16, 17):
        set_occurrence(
            occurrences.item(index),
            frame >= 282,
            camera_screw_offset,
        )


def run():
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")

    root = design.rootComponent
    occurrences = root.occurrences
    if occurrences.count != 27:
        raise RuntimeError(
            "Expected 27 root occurrences, found " + str(occurrences.count)
        )

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for index in range(occurrences.count):
        ensure_final_state_attributes(occurrences.item(index))

    viewport = app.activeViewport
    for frame in range(FRAME_START, FRAME_END):
        set_animation_state(occurrences, frame)
        set_animation_camera(viewport, frame)
        viewport.refresh()
        adsk.doEvents()

        output_path = os.path.join(OUTPUT_DIR, "frame_%04d.png" % frame)
        if not viewport.saveAsImageFile(
            output_path, FRAME_WIDTH, FRAME_HEIGHT
        ):
            raise RuntimeError("Failed to render " + output_path)

    print(
        json.dumps(
            {
                "frame_start": FRAME_START,
                "frame_end": FRAME_END,
                "frames_rendered": FRAME_END - FRAME_START,
                "output_dir": OUTPUT_DIR,
            }
        )
    )


run()
