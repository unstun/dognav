"""Render the human sequence with D435i installed on bare J17 first."""


D435_REQUESTED_FRAME_START = globals().get("FRAME_START", 0)
D435_REQUESTED_FRAME_END = globals().get("FRAME_END", 648)
D435_REQUESTED_FRAME_LIST = globals().get("FRAME_LIST")
D435_REQUESTED_FRAME_WIDTH = globals().get("FRAME_WIDTH", 1280)
D435_REQUESTED_FRAME_HEIGHT = globals().get("FRAME_HEIGHT", 720)

_HELPER_SCRIPT = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-full-installation-animation-human-sequence/"
    "render_human_sequence_installation_animation.py"
)

# Load all reviewed transform, camera, opacity, and rendering helpers without
# rendering either superseded sequence during bootstrap.
FRAME_START = 0
FRAME_END = 0
FRAME_LIST = []
FRAME_WIDTH = D435_REQUESTED_FRAME_WIDTH
FRAME_HEIGHT = D435_REQUESTED_FRAME_HEIGHT
exec(
    compile(
        open(_HELPER_SCRIPT, "r", encoding="utf-8").read(),
        _HELPER_SCRIPT,
        "exec",
    ),
    globals(),
    globals(),
)

FRAME_START = D435_REQUESTED_FRAME_START
FRAME_END = D435_REQUESTED_FRAME_END
FRAME_LIST = D435_REQUESTED_FRAME_LIST
FRAME_WIDTH = D435_REQUESTED_FRAME_WIDTH
FRAME_HEIGHT = D435_REQUESTED_FRAME_HEIGHT

OUTPUT_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-full-installation-animation-d435-first-human-sequence/"
    "frames"
)

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
    elif frame < 300:
        apply_shot(viewport, WORK_MID360_SHOT)
    elif frame < 336:
        apply_shot(viewport, WORK_J17_JOIN_SHOT)
    elif frame < 360:
        apply_shot(viewport, WORK_FRONT_BOLTS_SHOT)
    elif frame < 408:
        apply_shot(viewport, WORK_REAR_BOLTS_SHOT)
    elif frame < 432:
        apply_shot(viewport, WORK_J17_JOIN_SHOT)
    elif frame < 456:
        apply_shot(viewport, ROBOT_REAR_SPACERS_SHOT)
    elif frame < 480:
        apply_shot(viewport, TRANSFER_LATERAL_SHOT)
    elif frame < 504:
        apply_shot(viewport, TRANSFER_APPROACH_SHOT)
    elif frame < 528:
        apply_shot(viewport, BASE_FRONT_PAIR_SHOT)
    elif frame < 552:
        apply_shot(viewport, BASE_REAR_PAIR_SHOT)
    elif frame < 576:
        apply_shot(viewport, FINAL_CLOSE_SHOT)
    elif frame <= 623:
        blend_shots(
            viewport,
            FINAL_CLOSE_SHOT,
            FULL_SHOT,
            phase(frame, 576, 623),
        )
    else:
        apply_shot(viewport, FULL_SHOT)


def d435_first_work_to_robot_offset(frame):
    if frame < 456:
        return WORK_OFFSET
    if frame <= 479:
        lateral_amount = phase(frame, 456, 479)
        return (
            WORK_OFFSET[0] * (1.0 - lateral_amount),
            WORK_OFFSET[1],
            0.0,
        )
    if frame <= 503:
        approach_amount = phase(frame, 480, 503)
        return (0.0, WORK_OFFSET[1] * (1.0 - approach_amount), 0.0)
    return (0.0, 0.0, 0.0)


def d435_first_upper_offset(frame):
    if frame < 300:
        return UPPER_WORK_OFFSET
    if frame <= 335:
        join_amount = phase(frame, 300, 335)
        return (
            WORK_OFFSET[0],
            WORK_OFFSET[1] + 8.0 * (1.0 - join_amount),
            0.0,
        )
    return d435_first_work_to_robot_offset(frame)


def set_animation_state(occurrences, frame):
    set_occurrence(occurrences.item(0), True)
    for index in (3, 5, 6):
        set_occurrence(occurrences.item(index), False)

    # Bare J17 is the first workbench part.
    set_occurrence(
        occurrences.item(1),
        frame >= 24,
        d435_first_work_to_robot_offset(frame),
    )

    # D435i and both screws are installed while J20 and MID360 are absent, so
    # the camera-side driver corridor cannot cross those later parts.
    camera_axis = (0.0, -0.34202014332566627, 0.9396926207859093)
    d435_amount = phase(frame, 48, 83)
    d435_offset = shifted(
        d435_first_work_to_robot_offset(frame),
        scaled(camera_axis, 6.0 * (1.0 - d435_amount)),
    )
    set_occurrence(occurrences.item(15), frame >= 48, d435_offset)

    d435_screw_amount = phase(frame, 84, 107)
    d435_screw_offset = shifted(
        d435_first_work_to_robot_offset(frame),
        scaled(camera_axis, 3.0 * (1.0 - d435_screw_amount)),
    )
    for index in (16, 17):
        set_occurrence(
            occurrences.item(index),
            frame >= 84,
            d435_screw_offset,
        )

    # Bottom-up J17/J20 bolts are pre-inserted next, still before J20 exists at
    # the J17 interface.
    front_bolt_amount = phase(frame, 132, 155)
    front_bolt_offset = shifted(
        d435_first_work_to_robot_offset(frame),
        scaled((0.0, -4.0, 0.0), 1.0 - front_bolt_amount),
    )
    for index in (7, 8):
        set_occurrence(
            occurrences.item(index), frame >= 132, front_bolt_offset
        )

    rear_bolt_amount = phase(frame, 156, 179)
    rear_bolt_offset = shifted(
        d435_first_work_to_robot_offset(frame),
        scaled((0.0, -4.0, 0.0), 1.0 - rear_bolt_amount),
    )
    for index in (18, 19):
        set_occurrence(
            occurrences.item(index), frame >= 156, rear_bolt_offset
        )

    # Build the independent J20/MID360 subassembly after D435i is already
    # secured to J17.
    set_occurrence(
        occurrences.item(2),
        frame >= 180,
        d435_first_upper_offset(frame),
    )

    mid360_normal = (0.0, 0.9659258262890683, 0.25881904510252074)
    mid_amount = phase(frame, 204, 239)
    mid_offset = shifted(
        d435_first_upper_offset(frame),
        scaled(mid360_normal, 6.0 * (1.0 - mid_amount)),
    )
    set_occurrence(occurrences.item(4), frame >= 204, mid_offset)

    mid_screw_amount = phase(frame, 240, 275)
    mid_screw_offset = shifted(
        d435_first_upper_offset(frame),
        scaled(mid360_normal, -3.0 * (1.0 - mid_screw_amount)),
    )
    for index in (11, 12, 13, 14):
        set_occurrence(
            occurrences.item(index), frame >= 240, mid_screw_offset
        )

    # Lower the completed J20/MID360 subassembly over the already protruding
    # J17 bolts, with D435i remaining fixed on J17 throughout.
    front_nut_amount = phase(frame, 336, 359)
    front_nut_offset = shifted(
        d435_first_work_to_robot_offset(frame),
        scaled((0.0, 3.0, 0.0), 1.0 - front_nut_amount),
    )
    for index in (9, 10):
        set_occurrence(
            occurrences.item(index), frame >= 336, front_nut_offset
        )

    washer_amount = phase(frame, 360, 383)
    washer_offset = shifted(
        d435_first_work_to_robot_offset(frame),
        scaled((0.0, 2.5, 0.0), 1.0 - washer_amount),
    )
    for index in (20, 21):
        set_occurrence(
            occurrences.item(index), frame >= 360, washer_offset
        )

    locknut_amount = phase(frame, 384, 407)
    locknut_offset = shifted(
        d435_first_work_to_robot_offset(frame),
        scaled((0.0, 3.0, 0.0), 1.0 - locknut_amount),
    )
    for index in (22, 23):
        set_occurrence(
            occurrences.item(index), frame >= 384, locknut_offset
        )

    # Spacers still precede carrier arrival on Lite3.
    spacer_amount = phase(frame, 432, 455)
    set_occurrence(
        occurrences.item(25),
        frame >= 432,
        scaled((0.0, 3.0, 0.0), 1.0 - spacer_amount),
    )

    front_base_amount = phase(frame, 504, 527)
    set_occurrence(
        occurrences.item(24),
        frame >= 504,
        scaled((0.0, 4.0, 0.0), 1.0 - front_base_amount),
    )

    rear_base_amount = phase(frame, 528, 551)
    set_occurrence(
        occurrences.item(26),
        frame >= 528,
        scaled((0.0, 4.0, 0.0), 1.0 - rear_base_amount),
    )

    for index in (1, 2, 4, 15):
        restore_component_opacity(occurrences.item(index).component)

    if 84 <= frame < 108:
        set_component_opacity(occurrences.item(15).component, 0.18)
    if 132 <= frame < 180:
        set_component_opacity(occurrences.item(1).component, 0.18)
    if 240 <= frame < 276:
        set_component_opacity(occurrences.item(4).component, 0.18)
    if 300 <= frame < 408:
        set_component_opacity(occurrences.item(2).component, 0.20)
    if 504 <= frame < 552:
        set_component_opacity(occurrences.item(1).component, 0.18)


run()
