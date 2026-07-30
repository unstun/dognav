"""Render the complete Lite3 installation sequence including S410.

D435i is installed on bare J17 first. MID360 is then fastened to J20 away
from the robot, the official S410 guard is lowered over it, and four visual
M5 screws enter the coincident S410/J20 axes before the upper subassembly is
joined to J17. The final carrier transfer remains lateral-clearance first,
then normal approach, so it does not sweep through the robot body.
"""

import adsk.core
import adsk.fusion
import json
import os

globals().pop("run", None)


FRAME_START = globals().get("FRAME_START", 0)
FRAME_END = globals().get("FRAME_END", 720)
FRAME_LIST = globals().get("FRAME_LIST")
FRAME_WIDTH = globals().get("FRAME_WIDTH", 1280)
FRAME_HEIGHT = globals().get("FRAME_HEIGHT", 720)

OUTPUT_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-full-installation-animation-complete-s410/frames"
)

TRANSFORM_ATTRIBUTE_GROUP = "codex_full_installation_animation"
FINAL_TRANSFORM_ATTRIBUTE = "final_transform"
FINAL_VISIBILITY_ATTRIBUTE = "final_visibility"
OPACITY_ATTRIBUTE_GROUP = "codex_guided_installation_animation"
FINAL_OPACITY_ATTRIBUTE = "final_opacity"
EXPECTED_GUARD_FASTENER_NAME = (
    "S410_TO_J20_4X_M5X8_SOCKET_HEAD_SCREWS_VISUAL_CANDIDATE"
)

WORK_OFFSET = (80.0, 50.0, 0.0)
UPPER_WORK_OFFSET = (80.0, 58.0, 0.0)
MID360_NORMAL = (0.0, 0.9659258262890683, 0.25881904510252074)
CAMERA_AXIS = (0.0, -0.34202014332566627, 0.9396926207859093)

FULL_SHOT = {
    "eye": (-149.75, 247.0, 337.0),
    "target": (-29.75, 12.0, 237.0),
    "extents": 82.0,
}
WORK_J17_D435_SHOT = {
    "target": (49.553, 72.0, 259.5),
    "offset": (-18.0, 18.0, 14.0),
    "extents": 18.0,
}
WORK_D435_SCREWS_SHOT = {
    "target": (49.553, 71.95, 261.89),
    "offset": (0.0, 28.0, 10.0),
    "extents": 7.0,
}
WORK_MID360_SHOT = {
    "target": (49.553, 80.5, 256.5),
    "offset": (-18.0, 20.0, 14.0),
    "extents": 18.0,
}
WORK_MID360_SCREWS_SHOT = {
    "target": (49.553, 79.9, 256.25),
    "offset": (0.0, 18.0, 18.0),
    "extents": 10.0,
}
WORK_S410_SHOT = {
    "target": (49.553, 83.0, 257.4),
    "offset": (-18.0, 24.0, 16.0),
    "extents": 20.0,
}
WORK_S410_SCREWS_SHOT = {
    "target": (49.553, 80.2, 256.4),
    "offset": (0.0, 24.0, 18.0),
    "extents": 10.5,
}
WORK_J17_JOIN_SHOT = {
    "target": (49.553, 75.5, 255.5),
    "offset": (-18.0, 17.0, 14.0),
    "extents": 23.0,
}
WORK_FRONT_BOLTS_SHOT = {
    "target": (49.553, 71.1, 259.735),
    "offset": (0.0, 18.0, 12.0),
    "extents": 7.0,
}
WORK_REAR_BOLTS_SHOT = {
    "target": (49.553, 73.0, 251.891),
    "offset": (0.0, 18.0, 12.0),
    "extents": 8.0,
}
ROBOT_REAR_SPACERS_SHOT = {
    "target": (-30.4467, 20.67, 247.285),
    "offset": (0.0, 18.0, 18.0),
    "extents": 10.0,
}
TRANSFER_LATERAL_SHOT = {
    "target": (8.0, 55.0, 250.0),
    "offset": (-42.0, 70.0, 38.0),
    "extents": 92.0,
}
TRANSFER_APPROACH_SHOT = {
    "target": (-30.0, 43.0, 255.0),
    "offset": (-24.0, 58.0, 24.0),
    "extents": 58.0,
}
BASE_FRONT_PAIR_SHOT = {
    "target": (-30.4465, 20.17, 260.685),
    "offset": (0.0, 18.0, 18.0),
    "extents": 9.0,
}
BASE_REAR_PAIR_SHOT = {
    "target": (-30.4467, 20.67, 247.285),
    "offset": (0.0, 18.0, 18.0),
    "extents": 10.0,
}
FINAL_CLOSE_SHOT = {
    "eye": (-47.0, 52.0, 269.0),
    "target": (-30.447009644681465, 20.5, 256.5),
    "extents": 26.0,
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


def lerp(a, b, amount):
    return a + (b - a) * amount


def lerp3(a, b, amount):
    return tuple(lerp(a[i], b[i], amount) for i in range(3))


def scaled(vector, amount):
    return tuple(component * amount for component in vector)


def shifted(first, second):
    return tuple(first[i] + second[i] for i in range(3))


def shot_eye(shot):
    if "eye" in shot:
        return shot["eye"]
    return tuple(shot["target"][i] + shot["offset"][i] for i in range(3))


def set_camera(viewport, eye, target, extents):
    camera = viewport.camera
    camera.isSmoothTransition = False
    camera.cameraType = adsk.core.CameraTypes.OrthographicCameraType
    camera.eye = adsk.core.Point3D.create(*eye)
    camera.target = adsk.core.Point3D.create(*target)
    camera.upVector = adsk.core.Vector3D.create(0.0, 0.0, 1.0)
    camera.viewExtents = extents
    viewport.camera = camera


def apply_shot(viewport, shot):
    set_camera(viewport, shot_eye(shot), shot["target"], shot["extents"])


def blend_shots(viewport, first, second, amount):
    set_camera(
        viewport,
        lerp3(shot_eye(first), shot_eye(second), amount),
        lerp3(first["target"], second["target"], amount),
        lerp(first["extents"], second["extents"], amount),
    )


def ensure_final_state_attributes(occurrence):
    transform_attr = occurrence.attributes.itemByName(
        TRANSFORM_ATTRIBUTE_GROUP, FINAL_TRANSFORM_ATTRIBUTE
    )
    if transform_attr is None:
        occurrence.attributes.add(
            TRANSFORM_ATTRIBUTE_GROUP,
            FINAL_TRANSFORM_ATTRIBUTE,
            json.dumps(list(occurrence.transform.asArray())),
        )
    visibility_attr = occurrence.attributes.itemByName(
        TRANSFORM_ATTRIBUTE_GROUP, FINAL_VISIBILITY_ATTRIBUTE
    )
    if visibility_attr is None:
        occurrence.attributes.add(
            TRANSFORM_ATTRIBUTE_GROUP,
            FINAL_VISIBILITY_ATTRIBUTE,
            "true" if occurrence.isLightBulbOn else "false",
        )


def final_transform_array(occurrence):
    attribute = occurrence.attributes.itemByName(
        TRANSFORM_ATTRIBUTE_GROUP, FINAL_TRANSFORM_ATTRIBUTE
    )
    if attribute is None:
        raise RuntimeError("Missing final transform on " + occurrence.name)
    return json.loads(attribute.value)


def set_occurrence(occurrence, visible, offset=(0.0, 0.0, 0.0)):
    values = final_transform_array(occurrence)
    values[3] += offset[0]
    values[7] += offset[1]
    values[11] += offset[2]
    matrix = adsk.core.Matrix3D.create()
    matrix.setWithArray(values)
    occurrence.transform = matrix
    occurrence.isLightBulbOn = visible


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


def ensure_final_body_opacity(component):
    for body in component_bodies(component):
        attribute = body.attributes.itemByName(
            OPACITY_ATTRIBUTE_GROUP, FINAL_OPACITY_ATTRIBUTE
        )
        if attribute is None:
            body.attributes.add(
                OPACITY_ATTRIBUTE_GROUP,
                FINAL_OPACITY_ATTRIBUTE,
                repr(body.opacity),
            )


def restore_component_opacity(component):
    for body in component_bodies(component):
        attribute = body.attributes.itemByName(
            OPACITY_ATTRIBUTE_GROUP, FINAL_OPACITY_ATTRIBUTE
        )
        body.opacity = float(attribute.value) if attribute else 1.0


def set_component_opacity(component, opacity):
    for body in component_bodies(component):
        body.opacity = opacity


def work_to_robot_offset(frame):
    if frame < 528:
        return WORK_OFFSET
    if frame <= 551:
        amount = phase(frame, 528, 551)
        return (WORK_OFFSET[0] * (1.0 - amount), WORK_OFFSET[1], 0.0)
    if frame <= 575:
        amount = phase(frame, 552, 575)
        return (0.0, WORK_OFFSET[1] * (1.0 - amount), 0.0)
    return (0.0, 0.0, 0.0)


def upper_offset(frame):
    if frame < 372:
        return UPPER_WORK_OFFSET
    if frame <= 407:
        amount = phase(frame, 372, 407)
        return (
            WORK_OFFSET[0],
            WORK_OFFSET[1] + 8.0 * (1.0 - amount),
            0.0,
        )
    return work_to_robot_offset(frame)


def set_animation_camera(viewport, frame):
    if frame < 24:
        apply_shot(viewport, FULL_SHOT)
    elif frame <= 47:
        blend_shots(
            viewport,
            FULL_SHOT,
            WORK_J17_D435_SHOT,
            phase(frame, 24, 47),
        )
    elif frame < 84:
        apply_shot(viewport, WORK_J17_D435_SHOT)
    elif frame < 108:
        apply_shot(viewport, WORK_D435_SCREWS_SHOT)
    elif frame < 132:
        apply_shot(viewport, WORK_J17_D435_SHOT)
    elif frame < 156:
        apply_shot(viewport, WORK_FRONT_BOLTS_SHOT)
    elif frame < 180:
        apply_shot(viewport, WORK_REAR_BOLTS_SHOT)
    elif frame < 240:
        apply_shot(viewport, WORK_MID360_SHOT)
    elif frame < 276:
        apply_shot(viewport, WORK_MID360_SCREWS_SHOT)
    elif frame < 312:
        apply_shot(viewport, WORK_S410_SHOT)
    elif frame < 348:
        apply_shot(viewport, WORK_S410_SCREWS_SHOT)
    elif frame < 372:
        apply_shot(viewport, WORK_S410_SHOT)
    elif frame < 408:
        apply_shot(viewport, WORK_J17_JOIN_SHOT)
    elif frame < 432:
        apply_shot(viewport, WORK_FRONT_BOLTS_SHOT)
    elif frame < 480:
        apply_shot(viewport, WORK_REAR_BOLTS_SHOT)
    elif frame < 504:
        apply_shot(viewport, WORK_J17_JOIN_SHOT)
    elif frame < 528:
        apply_shot(viewport, ROBOT_REAR_SPACERS_SHOT)
    elif frame < 552:
        apply_shot(viewport, TRANSFER_LATERAL_SHOT)
    elif frame < 576:
        apply_shot(viewport, TRANSFER_APPROACH_SHOT)
    elif frame < 600:
        apply_shot(viewport, BASE_FRONT_PAIR_SHOT)
    elif frame < 624:
        apply_shot(viewport, BASE_REAR_PAIR_SHOT)
    elif frame < 648:
        apply_shot(viewport, FINAL_CLOSE_SHOT)
    elif frame <= 695:
        blend_shots(
            viewport,
            FINAL_CLOSE_SHOT,
            FULL_SHOT,
            phase(frame, 648, 695),
        )
    else:
        apply_shot(viewport, FULL_SHOT)


def set_animation_state(occurrences, frame):
    set_occurrence(occurrences.item(0), True)
    for index in (5, 6):
        set_occurrence(occurrences.item(index), False)

    set_occurrence(
        occurrences.item(1), frame >= 24, work_to_robot_offset(frame)
    )

    d435_amount = phase(frame, 48, 83)
    set_occurrence(
        occurrences.item(15),
        frame >= 48,
        shifted(
            work_to_robot_offset(frame),
            scaled(CAMERA_AXIS, 6.0 * (1.0 - d435_amount)),
        ),
    )
    d435_screw_amount = phase(frame, 84, 107)
    d435_screw_offset = shifted(
        work_to_robot_offset(frame),
        scaled(CAMERA_AXIS, 3.0 * (1.0 - d435_screw_amount)),
    )
    for index in (16, 17):
        set_occurrence(
            occurrences.item(index), frame >= 84, d435_screw_offset
        )

    front_bolt_amount = phase(frame, 132, 155)
    front_bolt_offset = shifted(
        work_to_robot_offset(frame),
        scaled((0.0, -4.0, 0.0), 1.0 - front_bolt_amount),
    )
    for index in (7, 8):
        set_occurrence(
            occurrences.item(index), frame >= 132, front_bolt_offset
        )

    rear_bolt_amount = phase(frame, 156, 179)
    rear_bolt_offset = shifted(
        work_to_robot_offset(frame),
        scaled((0.0, -4.0, 0.0), 1.0 - rear_bolt_amount),
    )
    for index in (18, 19):
        set_occurrence(
            occurrences.item(index), frame >= 156, rear_bolt_offset
        )

    set_occurrence(
        occurrences.item(2), frame >= 180, upper_offset(frame)
    )

    mid_amount = phase(frame, 204, 239)
    set_occurrence(
        occurrences.item(4),
        frame >= 204,
        shifted(
            upper_offset(frame),
            scaled(MID360_NORMAL, 6.0 * (1.0 - mid_amount)),
        ),
    )
    mid_screw_amount = phase(frame, 240, 275)
    mid_screw_offset = shifted(
        upper_offset(frame),
        scaled(MID360_NORMAL, -3.0 * (1.0 - mid_screw_amount)),
    )
    for index in (11, 12, 13, 14):
        set_occurrence(
            occurrences.item(index), frame >= 240, mid_screw_offset
        )

    guard_amount = phase(frame, 276, 311)
    set_occurrence(
        occurrences.item(3),
        frame >= 276,
        shifted(
            upper_offset(frame),
            scaled(MID360_NORMAL, 8.0 * (1.0 - guard_amount)),
        ),
    )
    guard_screw_amount = phase(frame, 312, 347)
    set_occurrence(
        occurrences.item(27),
        frame >= 312,
        shifted(
            upper_offset(frame),
            scaled(MID360_NORMAL, 3.0 * (1.0 - guard_screw_amount)),
        ),
    )

    front_nut_amount = phase(frame, 408, 431)
    front_nut_offset = shifted(
        work_to_robot_offset(frame),
        scaled((0.0, 3.0, 0.0), 1.0 - front_nut_amount),
    )
    for index in (9, 10):
        set_occurrence(
            occurrences.item(index), frame >= 408, front_nut_offset
        )

    washer_amount = phase(frame, 432, 455)
    washer_offset = shifted(
        work_to_robot_offset(frame),
        scaled((0.0, 2.5, 0.0), 1.0 - washer_amount),
    )
    for index in (20, 21):
        set_occurrence(
            occurrences.item(index), frame >= 432, washer_offset
        )

    locknut_amount = phase(frame, 456, 479)
    locknut_offset = shifted(
        work_to_robot_offset(frame),
        scaled((0.0, 3.0, 0.0), 1.0 - locknut_amount),
    )
    for index in (22, 23):
        set_occurrence(
            occurrences.item(index), frame >= 456, locknut_offset
        )

    spacer_amount = phase(frame, 504, 527)
    set_occurrence(
        occurrences.item(25),
        frame >= 504,
        scaled((0.0, 3.0, 0.0), 1.0 - spacer_amount),
    )

    front_base_amount = phase(frame, 576, 599)
    set_occurrence(
        occurrences.item(24),
        frame >= 576,
        scaled((0.0, 4.0, 0.0), 1.0 - front_base_amount),
    )
    rear_base_amount = phase(frame, 600, 623)
    set_occurrence(
        occurrences.item(26),
        frame >= 600,
        scaled((0.0, 4.0, 0.0), 1.0 - rear_base_amount),
    )

    for index in (1, 2, 3, 4, 15):
        restore_component_opacity(occurrences.item(index).component)
    if 84 <= frame < 108:
        set_component_opacity(occurrences.item(15).component, 0.18)
    if 132 <= frame < 180:
        set_component_opacity(occurrences.item(1).component, 0.18)
    if 240 <= frame < 276:
        set_component_opacity(occurrences.item(4).component, 0.18)
    if 312 <= frame < 348:
        set_component_opacity(occurrences.item(3).component, 0.18)
    if 372 <= frame < 480:
        set_component_opacity(occurrences.item(2).component, 0.20)
    if 576 <= frame < 624:
        set_component_opacity(occurrences.item(1).component, 0.18)


def restore_final_scene(occurrences, viewport):
    for index in range(occurrences.count):
        occurrence = occurrences.item(index)
        matrix = adsk.core.Matrix3D.create()
        matrix.setWithArray(final_transform_array(occurrence))
        occurrence.transform = matrix
        visibility = occurrence.attributes.itemByName(
            TRANSFORM_ATTRIBUTE_GROUP, FINAL_VISIBILITY_ATTRIBUTE
        )
        occurrence.isLightBulbOn = visibility.value == "true"
    for index in (1, 2, 3, 4, 15):
        restore_component_opacity(occurrences.item(index).component)
    apply_shot(viewport, FULL_SHOT)
    viewport.refresh()
    adsk.doEvents()


def run(context):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences
    if occurrences.count != 28:
        raise RuntimeError(
            "Expected 28 root occurrences, found " + str(occurrences.count)
        )
    if occurrences.item(27).component.name != EXPECTED_GUARD_FASTENER_NAME:
        raise RuntimeError("Occurrence 27 is not the S410 fastener group")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for index in range(occurrences.count):
        ensure_final_state_attributes(occurrences.item(index))
    for index in (1, 2, 3, 4, 15):
        ensure_final_body_opacity(occurrences.item(index).component)

    viewport = app.activeViewport
    frames = (
        FRAME_LIST
        if FRAME_LIST is not None
        else range(FRAME_START, FRAME_END)
    )
    rendered_count = 0
    try:
        for frame in frames:
            set_animation_state(occurrences, frame)
            set_animation_camera(viewport, frame)
            viewport.refresh()
            adsk.doEvents()
            output_path = os.path.join(
                OUTPUT_DIR, "frame_%04d.png" % frame
            )
            if not viewport.saveAsImageFile(
                output_path, FRAME_WIDTH, FRAME_HEIGHT
            ):
                raise RuntimeError("Failed to render " + output_path)
            rendered_count += 1
    finally:
        restore_final_scene(occurrences, viewport)

    print(
        json.dumps(
            {
                "frame_start": FRAME_START,
                "frame_end": FRAME_END,
                "frames_rendered": rendered_count,
                "output_dir": OUTPUT_DIR,
            }
        )
    )
