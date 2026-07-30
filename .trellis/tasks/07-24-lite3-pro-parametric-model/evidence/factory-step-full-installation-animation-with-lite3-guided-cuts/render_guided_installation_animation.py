"""Render a guided, action-focused Lite3 installation animation in Fusion.

Every installation operation owns a dedicated camera shot.  Hidden fastener
paths use temporary ghosted source bodies; geometry and final transforms are
never changed.  FRAME_START and FRAME_END are injected by the batch caller.
"""

import adsk.core
import adsk.fusion
import json
import os


FRAME_START = globals().get("FRAME_START", 0)
FRAME_END = globals().get("FRAME_END", 528)
FRAME_LIST = globals().get("FRAME_LIST")
FRAME_WIDTH = globals().get("FRAME_WIDTH", 1280)
FRAME_HEIGHT = globals().get("FRAME_HEIGHT", 720)

OUTPUT_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-full-installation-animation-with-lite3-guided-cuts/frames"
)

TRANSFORM_ATTRIBUTE_GROUP = "codex_full_installation_animation"
FINAL_TRANSFORM_ATTRIBUTE = "final_transform"
FINAL_VISIBILITY_ATTRIBUTE = "final_visibility"

OPACITY_ATTRIBUTE_GROUP = "codex_guided_installation_animation"
FINAL_OPACITY_ATTRIBUTE = "final_opacity"


FULL_SHOT = {
    "eye": (-149.75, 247.0, 337.0),
    "target": (-29.75, 12.0, 237.0),
    "extents": 82.0,
}

BASE_MEDIUM_SHOT = {
    "target": (-30.447009644681465, 20.5, 255.0),
    "offset": (-18.0, 12.0, 14.0),
    "extents": 24.0,
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

J20_MEDIUM_SHOT = {
    "target": (-30.447009644681465, 21.7, 256.0),
    "offset": (-18.0, 12.0, 14.0),
    "extents": 20.0,
}

BRACKET_FRONT_FASTENERS_SHOT = {
    "target": (-30.447, 21.1, 259.735),
    "offset": (0.0, 18.0, 12.0),
    "extents": 7.0,
}

BRACKET_REAR_FASTENERS_SHOT = {
    "target": (-30.447, 23.0, 251.891),
    "offset": (0.0, 18.0, 12.0),
    "extents": 8.0,
}

MID360_MEDIUM_SHOT = {
    "target": (-30.447, 23.5, 256.7),
    "offset": (-18.0, 20.0, 13.0),
    "extents": 18.0,
}

MID360_FRONT_SCREWS_SHOT = {
    "target": (-30.447, 21.4, 258.57),
    "offset": (0.0, 18.0, 18.0),
    "extents": 7.5,
}

MID360_REAR_SCREWS_SHOT = {
    "target": (-30.447, 22.5, 253.94),
    "offset": (0.0, 18.0, 18.0),
    "extents": 7.5,
}

D435_MEDIUM_SHOT = {
    "target": (-30.447, 22.0, 262.5),
    "offset": (-16.0, 24.0, 12.0),
    "extents": 15.0,
}

D435_SCREWS_SHOT = {
    "target": (-30.447, 21.95, 261.89),
    "offset": (0.0, 28.0, 10.0),
    "extents": 7.0,
}

FINAL_CLOSE_SHOT = {
    "eye": (-47.0, 52.0, 269.0),
    "target": (-30.447009644681465, 19.5, 255.5),
    "extents": 24.0,
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


def shot_eye(shot):
    if "eye" in shot:
        return shot["eye"]
    return tuple(
        shot["target"][i] + shot["offset"][i] for i in range(3)
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
    attr = occurrence.attributes.itemByName(
        TRANSFORM_ATTRIBUTE_GROUP, FINAL_TRANSFORM_ATTRIBUTE
    )
    if attr is None:
        raise RuntimeError(
            "Missing final transform on " + occurrence.fullPathName
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


def component_bodies(component):
    bodies = []
    seen_tokens = set()

    def walk(current_component):
        for body_index in range(current_component.bRepBodies.count):
            body = current_component.bRepBodies.item(body_index)
            token = body.entityToken
            if token not in seen_tokens:
                seen_tokens.add(token)
                bodies.append(body)
        for occurrence_index in range(current_component.occurrences.count):
            walk(current_component.occurrences.item(occurrence_index).component)

    walk(component)
    return bodies


def ensure_final_body_opacity(component):
    for body in component_bodies(component):
        attr = body.attributes.itemByName(
            OPACITY_ATTRIBUTE_GROUP, FINAL_OPACITY_ATTRIBUTE
        )
        if attr is None:
            body.attributes.add(
                OPACITY_ATTRIBUTE_GROUP,
                FINAL_OPACITY_ATTRIBUTE,
                repr(body.opacity),
            )


def restore_component_opacity(component):
    for body in component_bodies(component):
        attr = body.attributes.itemByName(
            OPACITY_ATTRIBUTE_GROUP, FINAL_OPACITY_ATTRIBUTE
        )
        body.opacity = float(attr.value) if attr is not None else 1.0


def set_component_opacity(component, opacity):
    for body in component_bodies(component):
        body.opacity = opacity


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
    set_camera(
        viewport,
        shot_eye(shot),
        shot["target"],
        shot["extents"],
    )


def blend_shots(viewport, first, second, amount):
    set_camera(
        viewport,
        lerp3(shot_eye(first), shot_eye(second), amount),
        lerp3(first["target"], second["target"], amount),
        lerp(first["extents"], second["extents"], amount),
    )


def set_animation_camera(viewport, frame):
    if frame < 24:
        apply_shot(viewport, FULL_SHOT)
    elif frame <= 47:
        blend_shots(
            viewport,
            FULL_SHOT,
            BASE_MEDIUM_SHOT,
            phase(frame, 24, 47),
        )
    elif frame < 96:
        apply_shot(viewport, BASE_MEDIUM_SHOT)
    elif frame < 120:
        apply_shot(viewport, BASE_REAR_PAIR_SHOT)
    elif frame < 144:
        apply_shot(viewport, BASE_FRONT_PAIR_SHOT)
    elif frame < 168:
        apply_shot(viewport, BASE_REAR_PAIR_SHOT)
    elif frame < 192:
        apply_shot(viewport, J20_MEDIUM_SHOT)
    elif frame < 240:
        apply_shot(viewport, BRACKET_FRONT_FASTENERS_SHOT)
    elif frame < 312:
        apply_shot(viewport, BRACKET_REAR_FASTENERS_SHOT)
    elif frame < 348:
        apply_shot(viewport, MID360_MEDIUM_SHOT)
    elif frame < 372:
        apply_shot(viewport, MID360_FRONT_SCREWS_SHOT)
    elif frame < 396:
        apply_shot(viewport, MID360_REAR_SCREWS_SHOT)
    elif frame < 432:
        apply_shot(viewport, D435_MEDIUM_SHOT)
    elif frame < 456:
        apply_shot(viewport, D435_SCREWS_SHOT)
    elif frame < 480:
        apply_shot(viewport, FINAL_CLOSE_SHOT)
    elif frame <= 503:
        blend_shots(
            viewport,
            FINAL_CLOSE_SHOT,
            FULL_SHOT,
            phase(frame, 480, 503),
        )
    else:
        apply_shot(viewport, FULL_SHOT)


def set_animation_state(occurrences, frame):
    set_occurrence(occurrences.item(0), True)

    for index in (3, 5, 6):
        set_occurrence(occurrences.item(index), False)

    amount = phase(frame, 48, 83)
    set_occurrence(
        occurrences.item(1),
        frame >= 48,
        scaled((0.0, 8.0, 0.0), 1.0 - amount),
    )

    amount = phase(frame, 96, 119)
    set_occurrence(
        occurrences.item(25),
        frame >= 96,
        scaled((0.0, 3.0, 0.0), 1.0 - amount),
    )

    amount = phase(frame, 120, 143)
    set_occurrence(
        occurrences.item(24),
        frame >= 120,
        scaled((0.0, 4.0, 0.0), 1.0 - amount),
    )

    amount = phase(frame, 144, 167)
    set_occurrence(
        occurrences.item(26),
        frame >= 144,
        scaled((0.0, 4.0, 0.0), 1.0 - amount),
    )

    amount = phase(frame, 168, 191)
    set_occurrence(
        occurrences.item(2),
        frame >= 168,
        scaled((0.0, 6.0, 0.0), 1.0 - amount),
    )

    amount = phase(frame, 192, 215)
    front_bolt_offset = scaled((0.0, -4.0, 0.0), 1.0 - amount)
    for index in (7, 8):
        set_occurrence(
            occurrences.item(index), frame >= 192, front_bolt_offset
        )

    amount = phase(frame, 216, 239)
    front_nut_offset = scaled((0.0, 3.0, 0.0), 1.0 - amount)
    for index in (9, 10):
        set_occurrence(
            occurrences.item(index), frame >= 216, front_nut_offset
        )

    amount = phase(frame, 240, 263)
    rear_bolt_offset = scaled((0.0, -4.0, 0.0), 1.0 - amount)
    for index in (18, 19):
        set_occurrence(
            occurrences.item(index), frame >= 240, rear_bolt_offset
        )

    amount = phase(frame, 264, 287)
    rear_washer_offset = scaled((0.0, 2.5, 0.0), 1.0 - amount)
    for index in (20, 21):
        set_occurrence(
            occurrences.item(index), frame >= 264, rear_washer_offset
        )

    amount = phase(frame, 288, 311)
    rear_locknut_offset = scaled((0.0, 3.0, 0.0), 1.0 - amount)
    for index in (22, 23):
        set_occurrence(
            occurrences.item(index), frame >= 288, rear_locknut_offset
        )

    mid360_normal = (0.0, 0.9659258262890683, 0.25881904510252074)
    amount = phase(frame, 312, 347)
    set_occurrence(
        occurrences.item(4),
        frame >= 312,
        scaled(mid360_normal, 6.0 * (1.0 - amount)),
    )

    amount = phase(frame, 348, 371)
    mid360_front_offset = scaled(mid360_normal, -3.0 * (1.0 - amount))
    for index in (11, 12):
        set_occurrence(
            occurrences.item(index),
            frame >= 348,
            mid360_front_offset,
        )

    amount = phase(frame, 372, 395)
    mid360_rear_offset = scaled(mid360_normal, -3.0 * (1.0 - amount))
    for index in (13, 14):
        set_occurrence(
            occurrences.item(index),
            frame >= 372,
            mid360_rear_offset,
        )

    camera_axis = (0.0, -0.34202014332566627, 0.9396926207859093)
    amount = phase(frame, 396, 431)
    set_occurrence(
        occurrences.item(15),
        frame >= 396,
        scaled(camera_axis, 6.0 * (1.0 - amount)),
    )

    amount = phase(frame, 432, 455)
    camera_screw_offset = scaled(camera_axis, 3.0 * (1.0 - amount))
    for index in (16, 17):
        set_occurrence(
            occurrences.item(index),
            frame >= 432,
            camera_screw_offset,
        )

    for index in (1, 2, 4, 15):
        restore_component_opacity(occurrences.item(index).component)

    if 96 <= frame < 168:
        set_component_opacity(occurrences.item(1).component, 0.18)
    if 192 <= frame < 312:
        set_component_opacity(occurrences.item(2).component, 0.20)
    if 348 <= frame < 396:
        set_component_opacity(occurrences.item(4).component, 0.18)
    if 432 <= frame < 456:
        set_component_opacity(occurrences.item(15).component, 0.18)


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
    for index in (1, 2, 4, 15):
        ensure_final_body_opacity(occurrences.item(index).component)

    viewport = app.activeViewport
    frames = FRAME_LIST if FRAME_LIST is not None else range(
        FRAME_START, FRAME_END
    )
    rendered_count = 0
    for frame in frames:
        set_animation_state(occurrences, frame)
        set_animation_camera(viewport, frame)
        viewport.refresh()
        adsk.doEvents()

        output_path = os.path.join(OUTPUT_DIR, "frame_%04d.png" % frame)
        if not viewport.saveAsImageFile(
            output_path, FRAME_WIDTH, FRAME_HEIGHT
        ):
            raise RuntimeError("Failed to render " + output_path)
        rendered_count += 1

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


run()
