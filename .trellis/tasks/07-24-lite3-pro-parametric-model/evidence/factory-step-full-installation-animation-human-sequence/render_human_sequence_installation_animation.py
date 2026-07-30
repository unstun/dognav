"""Render a human-executable Lite3 sensor-stack installation sequence.

The animation first builds the inaccessible bottom-fastener subassemblies away
from the robot, then places the locating spacers, transfers the completed
carrier onto Lite3, installs the exposed base screws, and adds D435i last.
It reuses the reviewed camera/transform helpers from the guided-cut renderer.
"""

import os


_REQUESTED_FRAME_START = globals().get("FRAME_START", 0)
_REQUESTED_FRAME_END = globals().get("FRAME_END", 600)
_REQUESTED_FRAME_LIST = globals().get("FRAME_LIST")
_REQUESTED_FRAME_WIDTH = globals().get("FRAME_WIDTH", 1280)
_REQUESTED_FRAME_HEIGHT = globals().get("FRAME_HEIGHT", 720)

_HELPER_SCRIPT = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-full-installation-animation-with-lite3-guided-cuts/"
    "render_guided_installation_animation.py"
)

# Load the already validated Fusion helpers without rendering the rejected
# sequence.  The helper's run() sees an empty frame list during bootstrap.
FRAME_START = 0
FRAME_END = 0
FRAME_LIST = []
FRAME_WIDTH = _REQUESTED_FRAME_WIDTH
FRAME_HEIGHT = _REQUESTED_FRAME_HEIGHT
exec(
    compile(
        open(_HELPER_SCRIPT, "r", encoding="utf-8").read(),
        _HELPER_SCRIPT,
        "exec",
    ),
    globals(),
    globals(),
)

FRAME_START = _REQUESTED_FRAME_START
FRAME_END = _REQUESTED_FRAME_END
FRAME_LIST = _REQUESTED_FRAME_LIST
FRAME_WIDTH = _REQUESTED_FRAME_WIDTH
FRAME_HEIGHT = _REQUESTED_FRAME_HEIGHT

OUTPUT_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-full-installation-animation-human-sequence/frames"
)

WORK_OFFSET = (80.0, 50.0, 0.0)
UPPER_WORK_OFFSET = (80.0, 58.0, 0.0)


def shifted(vector, offset):
    return tuple(vector[i] + offset[i] for i in range(3))


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

ROBOT_REAR_SPACERS_SHOT = BASE_REAR_PAIR_SHOT

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


def set_animation_camera(viewport, frame):
    if frame < 24:
        apply_shot(viewport, FULL_SHOT)
    elif frame <= 47:
        blend_shots(
            viewport,
            FULL_SHOT,
            WORK_MID360_SHOT,
            phase(frame, 24, 47),
        )
    elif frame < 84:
        apply_shot(viewport, WORK_MID360_SHOT)
    elif frame < 120:
        apply_shot(viewport, WORK_MID360_SCREWS_SHOT)
    elif frame < 144:
        apply_shot(viewport, WORK_MID360_SHOT)
    elif frame < 168:
        apply_shot(viewport, WORK_FRONT_BOLTS_SHOT)
    elif frame < 192:
        apply_shot(viewport, WORK_REAR_BOLTS_SHOT)
    elif frame < 228:
        apply_shot(viewport, WORK_J17_JOIN_SHOT)
    elif frame < 252:
        apply_shot(viewport, WORK_FRONT_BOLTS_SHOT)
    elif frame < 300:
        apply_shot(viewport, WORK_REAR_BOLTS_SHOT)
    elif frame < 324:
        apply_shot(viewport, WORK_J17_JOIN_SHOT)
    elif frame < 348:
        apply_shot(viewport, ROBOT_REAR_SPACERS_SHOT)
    elif frame < 372:
        apply_shot(viewport, TRANSFER_LATERAL_SHOT)
    elif frame < 396:
        apply_shot(viewport, TRANSFER_APPROACH_SHOT)
    elif frame < 420:
        apply_shot(viewport, BASE_FRONT_PAIR_SHOT)
    elif frame < 444:
        apply_shot(viewport, BASE_REAR_PAIR_SHOT)
    elif frame < 480:
        apply_shot(viewport, D435_MEDIUM_SHOT)
    elif frame < 504:
        apply_shot(viewport, D435_SCREWS_SHOT)
    elif frame < 528:
        apply_shot(viewport, FINAL_CLOSE_SHOT)
    elif frame <= 575:
        blend_shots(
            viewport,
            FINAL_CLOSE_SHOT,
            FULL_SHOT,
            phase(frame, 528, 575),
        )
    else:
        apply_shot(viewport, FULL_SHOT)


def work_to_robot_offset(frame):
    if frame < 348:
        return WORK_OFFSET
    if frame <= 371:
        lateral_amount = phase(frame, 348, 371)
        return (
            WORK_OFFSET[0] * (1.0 - lateral_amount),
            WORK_OFFSET[1],
            0.0,
        )
    if frame <= 395:
        approach_amount = phase(frame, 372, 395)
        return (0.0, WORK_OFFSET[1] * (1.0 - approach_amount), 0.0)
    return (0.0, 0.0, 0.0)


def upper_join_offset(frame):
    if frame < 192:
        return UPPER_WORK_OFFSET
    if frame <= 227:
        join_amount = phase(frame, 192, 227)
        return (
            WORK_OFFSET[0],
            WORK_OFFSET[1] + 8.0 * (1.0 - join_amount),
            WORK_OFFSET[2],
        )
    return work_to_robot_offset(frame)


def set_animation_state(occurrences, frame):
    set_occurrence(occurrences.item(0), True)
    for index in (3, 5, 6):
        set_occurrence(occurrences.item(index), False)

    # J20 is the first workbench part.  MID360 seats onto it while the entire
    # underside remains open to a human driver.
    set_occurrence(
        occurrences.item(2),
        frame >= 24,
        upper_join_offset(frame),
    )

    mid360_normal = (0.0, 0.9659258262890683, 0.25881904510252074)
    mid_amount = phase(frame, 48, 83)
    mid_offset = shifted(
        upper_join_offset(frame),
        scaled(mid360_normal, 6.0 * (1.0 - mid_amount)),
    )
    set_occurrence(occurrences.item(4), frame >= 48, mid_offset)

    mid_screw_amount = phase(frame, 84, 119)
    mid_screw_offset = shifted(
        upper_join_offset(frame),
        scaled(mid360_normal, -3.0 * (1.0 - mid_screw_amount)),
    )
    for index in (11, 12, 13, 14):
        set_occurrence(
            occurrences.item(index),
            frame >= 84,
            mid_screw_offset,
        )

    # J17 remains separate until all bottom-up through bolts can be inserted
    # from an unobstructed side away from Lite3.
    set_occurrence(
        occurrences.item(1),
        frame >= 144,
        work_to_robot_offset(frame),
    )

    front_bolt_amount = phase(frame, 144, 167)
    front_bolt_offset = shifted(
        work_to_robot_offset(frame),
        scaled((0.0, -4.0, 0.0), 1.0 - front_bolt_amount),
    )
    for index in (7, 8):
        set_occurrence(
            occurrences.item(index),
            frame >= 144,
            front_bolt_offset,
        )

    rear_bolt_amount = phase(frame, 168, 191)
    rear_bolt_offset = shifted(
        work_to_robot_offset(frame),
        scaled((0.0, -4.0, 0.0), 1.0 - rear_bolt_amount),
    )
    for index in (18, 19):
        set_occurrence(
            occurrences.item(index),
            frame >= 168,
            rear_bolt_offset,
        )

    # The J20/MID360 subassembly lowers over already protruding bolts.  Only
    # then do the accessible top-side nuts, washers, and locknuts arrive.
    front_nut_amount = phase(frame, 228, 251)
    front_nut_offset = shifted(
        work_to_robot_offset(frame),
        scaled((0.0, 3.0, 0.0), 1.0 - front_nut_amount),
    )
    for index in (9, 10):
        set_occurrence(
            occurrences.item(index),
            frame >= 228,
            front_nut_offset,
        )

    washer_amount = phase(frame, 252, 275)
    washer_offset = shifted(
        work_to_robot_offset(frame),
        scaled((0.0, 2.5, 0.0), 1.0 - washer_amount),
    )
    for index in (20, 21):
        set_occurrence(
            occurrences.item(index),
            frame >= 252,
            washer_offset,
        )

    locknut_amount = phase(frame, 276, 299)
    locknut_offset = shifted(
        work_to_robot_offset(frame),
        scaled((0.0, 3.0, 0.0), 1.0 - locknut_amount),
    )
    for index in (22, 23):
        set_occurrence(
            occurrences.item(index),
            frame >= 276,
            locknut_offset,
        )

    # Rear locating spacers must exist on Lite3 before the carrier descends.
    spacer_amount = phase(frame, 324, 347)
    set_occurrence(
        occurrences.item(25),
        frame >= 324,
        scaled((0.0, 3.0, 0.0), 1.0 - spacer_amount),
    )

    # Exposed base screws are installed only after the preassembled carrier
    # reaches the robot and the locating spacers are already seated.
    front_base_amount = phase(frame, 396, 419)
    set_occurrence(
        occurrences.item(24),
        frame >= 396,
        scaled((0.0, 4.0, 0.0), 1.0 - front_base_amount),
    )

    rear_base_amount = phase(frame, 420, 443)
    set_occurrence(
        occurrences.item(26),
        frame >= 420,
        scaled((0.0, 4.0, 0.0), 1.0 - rear_base_amount),
    )

    # D435i is last because both screw heads remain accessible from outside.
    camera_axis = (0.0, -0.34202014332566627, 0.9396926207859093)
    camera_amount = phase(frame, 444, 479)
    set_occurrence(
        occurrences.item(15),
        frame >= 444,
        scaled(camera_axis, 6.0 * (1.0 - camera_amount)),
    )

    camera_screw_amount = phase(frame, 480, 503)
    camera_screw_offset = scaled(
        camera_axis, 3.0 * (1.0 - camera_screw_amount)
    )
    for index in (16, 17):
        set_occurrence(
            occurrences.item(index),
            frame >= 480,
            camera_screw_offset,
        )

    for index in (1, 2, 4, 15):
        restore_component_opacity(occurrences.item(index).component)

    if 84 <= frame < 120:
        set_component_opacity(occurrences.item(4).component, 0.18)
    if 144 <= frame < 192:
        set_component_opacity(occurrences.item(1).component, 0.18)
    if 192 <= frame < 300:
        set_component_opacity(occurrences.item(2).component, 0.20)
    if 396 <= frame < 444:
        set_component_opacity(occurrences.item(1).component, 0.18)
    if 480 <= frame < 504:
        set_component_opacity(occurrences.item(15).component, 0.18)


run()
