"""Render a slow, focused S410 guard fastening demonstration on Rev B.

The MID360 is already mounted.  The S410 guard is lowered onto the one-piece
Rev B carrier, then four M5 screws are started and tightened in a diagonal
cross pattern.  No nuts are shown because the screws pass through the S410
clearance feet and engage the modeled J20A M5 receiver threads directly.
"""

import adsk.core
import adsk.fusion
import json
import math
import os
import traceback


FRAME_START = globals().get("FRAME_START", 0)
FRAME_END = globals().get("FRAME_END", 696)
FRAME_LIST = globals().get("FRAME_LIST")
FRAME_WIDTH = globals().get("FRAME_WIDTH", 1280)
FRAME_HEIGHT = globals().get("FRAME_HEIGHT", 720)

OUTPUT_ROOT = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-rev-b-s410-four-m5-slow-fixation-video"
)
OUTPUT_DIR = os.path.join(OUTPUT_ROOT, "frames")

EXPECTED_OCCURRENCE_COUNT = 36
REV_B_INDEX = 35
GUARD_INDEX = 3
MID360_INDEX = 4
SCREW_INDICES = (28, 29, 30, 31)
TOOL_INDEX = 33

REV_B_NAME = (
    "J17A_J20A_MONOLITHIC_REAR_WEB_PRINT_ADAPTATION_REV_B_NOT_OFFICIAL_CAD"
)
SCREW_COMPONENT_NAME = (
    "S410_TO_J20_M5X8_INDIVIDUAL_SCREW_VISUAL_CANDIDATE"
)
TOOL_COMPONENT_NAME = "S410_M5_SHORT_L_KEY_ANIMATION_TOOL"

MOUNT_NORMAL = (0.0, 0.9659258262890683, 0.25881904510252074)
PLATE_UP = (0.0, -0.25881904510252074, 0.9659258262890683)

SCREW_SEATS = {
    28: (-32.906859573287356, 21.37853880979711, 260.4951592299928),
    29: (-27.987159716075574, 21.37853880979711, 260.4951592299928),
    30: (-32.935037516961955, 23.537893759538793, 252.43633684598146),
    31: (-27.958981772400975, 23.537893759538793, 252.43633684598146),
}

# Every action lasts 54 frames (2.25 s at 24 fps).  All screws are started
# first, then tightened in the same cross pattern.
SCREW_SCHEDULES = {
    28: {"start": (168, 221), "tighten": (384, 437)},
    31: {"start": (222, 275), "tighten": (438, 491)},
    29: {"start": (276, 329), "tighten": (492, 545)},
    30: {"start": (330, 383), "tighten": (546, 599)},
}

# These 90-degree short-L-key strokes were previously checked at the sampled
# insertion depths.  The second tightening stroke continues from the first.
SCREW_ANGLE_RANGES_DEG = {
    28: (240.0, 330.0),
    31: (60.0, 150.0),
    29: (210.0, 300.0),
    30: (30.0, 120.0),
}

OVERVIEW_SHOT = {
    "target": (-30.447, 22.0, 256.5),
    "offset": (-18.0, 25.0, 16.0),
    "extents": 20.0,
}
FINAL_SHOT = {
    "target": (-30.447, 21.9, 256.5),
    "offset": (-14.0, 22.0, 13.0),
    "extents": 17.0,
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


def lerp3(first, second, amount):
    return tuple(lerp(first[i], second[i], amount) for i in range(3))


def scaled(vector, amount):
    return tuple(value * amount for value in vector)


def shifted(first, second):
    return tuple(first[i] + second[i] for i in range(3))


def shot_eye(shot):
    return shifted(shot["target"], shot["offset"])


def set_camera(viewport, eye, target, extents):
    camera = viewport.camera
    camera.isSmoothTransition = False
    camera.cameraType = adsk.core.CameraTypes.OrthographicCameraType
    camera.eye = adsk.core.Point3D.create(*eye)
    camera.target = adsk.core.Point3D.create(*target)
    camera.upVector = adsk.core.Vector3D.create(*PLATE_UP)
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


def screw_camera_shot(screw_index):
    seat = SCREW_SEATS[screw_index]
    side = -1.0 if seat[0] < -30.447 else 1.0
    target = shifted(seat, scaled(MOUNT_NORMAL, 0.75))
    return {
        "target": target,
        "offset": (side * 5.5, 12.5, 6.5),
        "extents": 6.4,
    }


SCREW_CAMERA_SHOTS = {
    index: screw_camera_shot(index) for index in SCREW_INDICES
}


def component_bodies(component):
    bodies = []
    seen = set()

    def walk(current):
        for body_index in range(current.bRepBodies.count):
            body = current.bRepBodies.item(body_index)
            token = body.entityToken
            if token not in seen:
                seen.add(token)
                bodies.append(body)
        for occurrence_index in range(current.occurrences.count):
            walk(current.occurrences.item(occurrence_index).component)

    walk(component)
    return bodies


def set_component_opacity(component, opacity):
    for body in component_bodies(component):
        body.opacity = opacity


def matrix_from_values(values):
    matrix = adsk.core.Matrix3D.create()
    matrix.setWithArray(values)
    return matrix


def set_offset_occurrence(occurrence, final_values, offset, visible=True):
    values = list(final_values)
    values[3] += offset[0]
    values[7] += offset[1]
    values[11] += offset[2]
    occurrence.transform = matrix_from_values(values)
    occurrence.isLightBulbOn = visible


def set_rotating_occurrence(
    occurrence,
    final_values,
    visible,
    insertion_offset,
    angle,
):
    axis = adsk.core.Vector3D.create(*MOUNT_NORMAL)
    axis.normalize()
    matrix = adsk.core.Matrix3D.create()
    matrix.setToRotation(
        angle,
        axis,
        adsk.core.Point3D.create(0.0, 0.0, 0.0),
    )
    values = list(matrix.asArray())
    values[3] = final_values[3] + MOUNT_NORMAL[0] * insertion_offset
    values[7] = final_values[7] + MOUNT_NORMAL[1] * insertion_offset
    values[11] = final_values[11] + MOUNT_NORMAL[2] * insertion_offset
    matrix.setWithArray(values)
    occurrence.transform = matrix
    occurrence.isLightBulbOn = visible


def screw_state(frame, screw_index):
    schedule = SCREW_SCHEDULES[screw_index]
    start_begin, start_end = schedule["start"]
    tighten_begin, tighten_end = schedule["tighten"]
    angle_begin_deg, angle_end_deg = SCREW_ANGLE_RANGES_DEG[screw_index]
    angle_begin = math.radians(angle_begin_deg)
    angle_end = math.radians(angle_end_deg)
    angle_delta = angle_end - angle_begin

    if frame < start_begin:
        return False, 1.8, angle_begin
    if frame <= start_end:
        amount = phase(frame, start_begin, start_end)
        return (
            True,
            lerp(1.8, 0.35, amount),
            lerp(angle_begin, angle_end, amount),
        )
    if frame < tighten_begin:
        return True, 0.35, angle_end
    if frame <= tighten_end:
        amount = phase(frame, tighten_begin, tighten_end)
        return (
            True,
            lerp(0.35, 0.0, amount),
            lerp(angle_end, angle_end + angle_delta, amount),
        )
    return True, 0.0, angle_end + angle_delta


def active_action(frame):
    for action_name in ("start", "tighten"):
        for screw_index in (28, 31, 29, 30):
            begin, end = SCREW_SCHEDULES[screw_index][action_name]
            if begin <= frame <= end:
                visible, insertion, angle = screw_state(frame, screw_index)
                return {
                    "name": action_name,
                    "screw_index": screw_index,
                    "insertion": insertion,
                    "angle": angle,
                }
    return None


def set_tool_state(occurrences, final_transforms, action):
    tool = occurrences.item(TOOL_INDEX)
    if action is None:
        tool.isLightBulbOn = False
        return
    screw_index = action["screw_index"]
    screw_final = final_transforms[screw_index]
    axis = adsk.core.Vector3D.create(*MOUNT_NORMAL)
    axis.normalize()
    matrix = adsk.core.Matrix3D.create()
    matrix.setToRotation(
        action["angle"],
        axis,
        adsk.core.Point3D.create(0.0, 0.0, 0.0),
    )
    values = list(matrix.asArray())
    values[3] = screw_final[3] + MOUNT_NORMAL[0] * action["insertion"]
    values[7] = screw_final[7] + MOUNT_NORMAL[1] * action["insertion"]
    values[11] = screw_final[11] + MOUNT_NORMAL[2] * action["insertion"]
    matrix.setWithArray(values)
    tool.transform = matrix
    tool.isLightBulbOn = True


def set_animation_state(
    occurrences,
    final_transforms,
    base_opacities,
    frame,
):
    for occurrence_index in range(occurrences.count):
        occurrences.item(occurrence_index).isLightBulbOn = False

    rev_b = occurrences.item(REV_B_INDEX)
    guard = occurrences.item(GUARD_INDEX)
    mid360 = occurrences.item(MID360_INDEX)
    rev_b.isLightBulbOn = True
    mid360.isLightBulbOn = True

    guard_amount = phase(frame, 48, 143)
    guard_offset = scaled(MOUNT_NORMAL, 6.0 * (1.0 - guard_amount))
    set_offset_occurrence(
        guard,
        final_transforms[GUARD_INDEX],
        guard_offset,
        True,
    )

    # Restore the three main components before applying the current cutaway.
    for body, opacity in base_opacities:
        body.opacity = opacity

    action = active_action(frame)
    if 160 <= frame < 600:
        set_component_opacity(rev_b.component, 0.42)
        set_component_opacity(guard.component, 0.30)
        set_component_opacity(mid360.component, 0.18)
    elif frame < 48:
        set_component_opacity(mid360.component, 0.45)

    for screw_index in SCREW_INDICES:
        visible, insertion, angle = screw_state(frame, screw_index)
        set_rotating_occurrence(
            occurrences.item(screw_index),
            final_transforms[screw_index],
            visible,
            insertion,
            angle,
        )

    set_tool_state(occurrences, final_transforms, action)


def set_animation_camera(viewport, frame):
    action = active_action(frame)
    if action is not None:
        apply_shot(viewport, SCREW_CAMERA_SHOTS[action["screw_index"]])
        return
    if frame < 48:
        apply_shot(viewport, OVERVIEW_SHOT)
    elif frame < 144:
        apply_shot(viewport, OVERVIEW_SHOT)
    elif frame < 168:
        blend_shots(
            viewport,
            OVERVIEW_SHOT,
            SCREW_CAMERA_SHOTS[28],
            phase(frame, 144, 167),
        )
    elif frame < 600:
        apply_shot(viewport, OVERVIEW_SHOT)
    elif frame < 624:
        blend_shots(
            viewport,
            SCREW_CAMERA_SHOTS[30],
            FINAL_SHOT,
            phase(frame, 600, 623),
        )
    else:
        apply_shot(viewport, FINAL_SHOT)


def validate_scene(occurrences):
    if occurrences.count != EXPECTED_OCCURRENCE_COUNT:
        raise RuntimeError(
            "Expected %d root occurrences, found %d"
            % (EXPECTED_OCCURRENCE_COUNT, occurrences.count)
        )
    if occurrences.item(REV_B_INDEX).component.name != REV_B_NAME:
        raise RuntimeError(
            "Unexpected Rev B component: "
            + occurrences.item(REV_B_INDEX).component.name
        )
    for screw_index in SCREW_INDICES:
        if (
            occurrences.item(screw_index).component.name
            != SCREW_COMPONENT_NAME
        ):
            raise RuntimeError(
                "Unexpected S410 screw at index " + str(screw_index)
            )
    if occurrences.item(TOOL_INDEX).component.name != TOOL_COMPONENT_NAME:
        raise RuntimeError("Unexpected S410 L-key at index 33")


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
    camera.eye = adsk.core.Point3D.create(*snapshot["eye"])
    camera.target = adsk.core.Point3D.create(*snapshot["target"])
    camera.upVector = adsk.core.Vector3D.create(*snapshot["up"])
    camera.viewExtents = snapshot["extents"]
    viewport.camera = camera


def run(context):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")

    root = design.rootComponent
    occurrences = root.occurrences
    validate_scene(occurrences)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    final_transforms = {
        index: list(occurrences.item(index).transform.asArray())
        for index in range(occurrences.count)
    }
    final_visibility = {
        index: occurrences.item(index).isLightBulbOn
        for index in range(occurrences.count)
    }
    opacity_components = (
        occurrences.item(REV_B_INDEX).component,
        occurrences.item(GUARD_INDEX).component,
        occurrences.item(MID360_INDEX).component,
    )
    base_opacities = []
    seen_tokens = set()
    for component in opacity_components:
        for body in component_bodies(component):
            if body.entityToken not in seen_tokens:
                seen_tokens.add(body.entityToken)
                base_opacities.append((body, body.opacity))

    viewport = app.activeViewport
    original_camera = camera_snapshot(viewport)
    frames = (
        FRAME_LIST
        if FRAME_LIST is not None
        else range(FRAME_START, FRAME_END)
    )
    rendered_frames = []
    error_text = None
    try:
        for frame in frames:
            set_animation_state(
                occurrences,
                final_transforms,
                base_opacities,
                frame,
            )
            set_animation_camera(viewport, frame)
            viewport.refresh()
            adsk.doEvents()
            output_path = os.path.join(
                OUTPUT_DIR,
                "frame_%04d.png" % frame,
            )
            if not viewport.saveAsImageFile(
                output_path,
                FRAME_WIDTH,
                FRAME_HEIGHT,
            ):
                raise RuntimeError("Failed to render " + output_path)
            rendered_frames.append(frame)
    except Exception:
        error_text = traceback.format_exc()
        raise
    finally:
        for index in range(occurrences.count):
            occurrence = occurrences.item(index)
            occurrence.transform = matrix_from_values(final_transforms[index])
            occurrence.isLightBulbOn = final_visibility[index]
        for body, opacity in base_opacities:
            body.opacity = opacity
        restore_camera(viewport, original_camera)
        viewport.refresh()
        adsk.doEvents()

        report = {
            "frame_start": FRAME_START,
            "frame_end": FRAME_END,
            "requested_frame_list": FRAME_LIST,
            "rendered_frames": rendered_frames,
            "rendered_count": len(rendered_frames),
            "frame_size": [FRAME_WIDTH, FRAME_HEIGHT],
            "output_dir": OUTPUT_DIR,
            "sequence": {
                "guard_landing": [48, 143],
                "start_all_cross_order": [28, 31, 29, 30],
                "tighten_cross_order": [28, 31, 29, 30],
                "direct_thread_into_rev_b": True,
                "nuts": False,
            },
            "scene_restored": True,
            "error": error_text,
        }
        suffix = (
            "preview"
            if FRAME_LIST is not None
            else "%04d_%04d" % (FRAME_START, FRAME_END)
        )
        report_path = os.path.join(
            OUTPUT_ROOT,
            "render_report_%s.json" % suffix,
        )
        with open(report_path, "w", encoding="utf-8") as report_file:
            json.dump(report, report_file, indent=2, sort_keys=True)

    print(json.dumps(report, sort_keys=True))

