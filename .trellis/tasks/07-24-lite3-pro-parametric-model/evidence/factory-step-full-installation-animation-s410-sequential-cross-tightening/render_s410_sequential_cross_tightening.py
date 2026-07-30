"""Render S410 screws as individual human-operated fastening steps.

All four screws are first started one at a time, then tightened in the diagonal
order S1 -> S4 -> S2 -> S3. A short right-angle L-key rotates with the active
screw. The tool is hidden in the reviewed final assembly.
"""

import math


SEQ_REQUESTED_FRAME_START = globals().get("FRAME_START", 0)
SEQ_REQUESTED_FRAME_END = globals().get("FRAME_END", 828)
SEQ_REQUESTED_FRAME_LIST = globals().get("FRAME_LIST")
SEQ_REQUESTED_FRAME_WIDTH = globals().get("FRAME_WIDTH", 1280)
SEQ_REQUESTED_FRAME_HEIGHT = globals().get("FRAME_HEIGHT", 720)

PREVIOUS_RENDERER = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-full-installation-animation-complete-s410/"
    "render_complete_s410_installation_animation.py"
)

exec(
    compile(
        open(PREVIOUS_RENDERER, "r", encoding="utf-8").read(),
        PREVIOUS_RENDERER,
        "exec",
    ),
    globals(),
    globals(),
)

FRAME_START = SEQ_REQUESTED_FRAME_START
FRAME_END = SEQ_REQUESTED_FRAME_END
FRAME_LIST = SEQ_REQUESTED_FRAME_LIST
FRAME_WIDTH = SEQ_REQUESTED_FRAME_WIDTH
FRAME_HEIGHT = SEQ_REQUESTED_FRAME_HEIGHT

OUTPUT_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-full-installation-animation-s410-sequential-cross-tightening/"
    "frames"
)

SCREW_COMPONENT_NAME = "S410_TO_J20_M5X8_INDIVIDUAL_SCREW_VISUAL_CANDIDATE"
TOOL_COMPONENT_NAME = "S410_M5_SHORT_L_KEY_ANIMATION_TOOL"
SCREW_INDICES = (28, 29, 30, 31)
TOOL_INDEX = 33

SCREW_SEATS = {
    28: (-32.906859573287356, 21.37853880979711, 260.4951592299928),
    29: (-27.987159716075574, 21.37853880979711, 260.4951592299928),
    30: (-32.935037516961955, 23.537893759538793, 252.43633684598146),
    31: (-27.958981772400975, 23.537893759538793, 252.43633684598146),
}

# Start all screws diagonally, then tighten in the same cross pattern.
SCREW_SCHEDULES = {
    28: {"start": (312, 329), "tighten": (384, 401)},
    31: {"start": (330, 347), "tighten": (402, 419)},
    29: {"start": (348, 365), "tighten": (420, 437)},
    30: {"start": (366, 383), "tighten": (438, 455)},
}

# Collision-free 90-degree L-key strokes at every sampled insertion depth.
SCREW_ANGLE_RANGES_DEG = {
    28: (240.0, 330.0),
    31: (60.0, 150.0),
    29: (210.0, 300.0),
    30: (30.0, 120.0),
}

PREVIOUS_SET_ANIMATION_STATE = set_animation_state
PREVIOUS_SET_ANIMATION_CAMERA = set_animation_camera
PREVIOUS_UPPER_OFFSET = upper_offset


def mapped_previous_frame(frame):
    if frame < 312:
        return frame
    if frame < 456:
        return 347
    return frame - 108


def screw_step(frame, screw_index, schedule):
    start_begin, start_end = schedule["start"]
    tighten_begin, tighten_end = schedule["tighten"]
    angle_begin_deg, angle_end_deg = SCREW_ANGLE_RANGES_DEG[screw_index]
    angle_begin = math.radians(angle_begin_deg)
    angle_end = math.radians(angle_end_deg)
    if frame < start_begin:
        return False, 0.6, angle_begin
    if frame <= start_end:
        amount = phase(frame, start_begin, start_end)
        return (
            True,
            lerp(0.6, 0.3, amount),
            lerp(angle_begin, angle_end, amount),
        )
    if frame < tighten_begin:
        return True, 0.3, angle_end
    if frame <= tighten_end:
        amount = phase(frame, tighten_begin, tighten_end)
        return (
            True,
            0.3 * (1.0 - amount),
            lerp(angle_begin, angle_end, amount),
        )
    return True, 0.0, angle_end


def active_screw(frame):
    for screw_index, schedule in SCREW_SCHEDULES.items():
        for begin, end in (schedule["start"], schedule["tighten"]):
            if begin <= frame <= end:
                visible, insertion, angle = screw_step(
                    frame, screw_index, schedule
                )
                return screw_index, insertion, angle
    return None


def set_rotating_screw(
    occurrence,
    visible,
    assembly_offset,
    insertion_offset,
    angle,
):
    final_values = final_transform_array(occurrence)
    axis = adsk.core.Vector3D.create(*MID360_NORMAL)
    axis.normalize()
    matrix = adsk.core.Matrix3D.create()
    matrix.setToRotation(
        angle,
        axis,
        adsk.core.Point3D.create(0.0, 0.0, 0.0),
    )
    values = list(matrix.asArray())
    values[3] = (
        final_values[3]
        + assembly_offset[0]
        + MID360_NORMAL[0] * insertion_offset
    )
    values[7] = (
        final_values[7]
        + assembly_offset[1]
        + MID360_NORMAL[1] * insertion_offset
    )
    values[11] = (
        final_values[11]
        + assembly_offset[2]
        + MID360_NORMAL[2] * insertion_offset
    )
    matrix.setWithArray(values)
    occurrence.transform = matrix
    occurrence.isLightBulbOn = visible


def set_driver(occurrences, active, assembly_offset):
    tool = occurrences.item(TOOL_INDEX)
    if active is None:
        tool.isLightBulbOn = False
        return
    screw_index, insertion_offset, angle = active
    screw_final = final_transform_array(occurrences.item(screw_index))
    axis = adsk.core.Vector3D.create(*MID360_NORMAL)
    axis.normalize()
    matrix = adsk.core.Matrix3D.create()
    matrix.setToRotation(
        angle,
        axis,
        adsk.core.Point3D.create(0.0, 0.0, 0.0),
    )
    values = list(matrix.asArray())
    values[3] = (
        screw_final[3]
        + assembly_offset[0]
        + MID360_NORMAL[0] * insertion_offset
    )
    values[7] = (
        screw_final[7]
        + assembly_offset[1]
        + MID360_NORMAL[1] * insertion_offset
    )
    values[11] = (
        screw_final[11]
        + assembly_offset[2]
        + MID360_NORMAL[2] * insertion_offset
    )
    matrix.setWithArray(values)
    tool.transform = matrix
    tool.isLightBulbOn = True


def screw_camera_shot(screw_index):
    seat = SCREW_SEATS[screw_index]
    work_seat = shifted(seat, UPPER_WORK_OFFSET)
    target = shifted(work_seat, scaled(MID360_NORMAL, 1.2))
    return {
        "target": target,
        "offset": (-8.0, 14.0, 8.0),
        "extents": 8.0,
    }


SCREW_CAMERA_SHOTS = {
    screw_index: screw_camera_shot(screw_index)
    for screw_index in SCREW_INDICES
}


def set_animation_camera(viewport, frame):
    if frame < 312:
        PREVIOUS_SET_ANIMATION_CAMERA(viewport, frame)
        return
    active = active_screw(frame)
    if active is not None:
        apply_shot(viewport, SCREW_CAMERA_SHOTS[active[0]])
        return
    PREVIOUS_SET_ANIMATION_CAMERA(viewport, mapped_previous_frame(frame))


def set_animation_state(occurrences, frame):
    previous_frame = mapped_previous_frame(frame)
    PREVIOUS_SET_ANIMATION_STATE(occurrences, previous_frame)
    occurrences.item(27).isLightBulbOn = False

    assembly_offset = PREVIOUS_UPPER_OFFSET(previous_frame)
    for screw_index in SCREW_INDICES:
        visible, insertion_offset, angle = screw_step(
            frame, screw_index, SCREW_SCHEDULES[screw_index]
        )
        set_rotating_screw(
            occurrences.item(screw_index),
            visible,
            assembly_offset,
            insertion_offset,
            angle,
        )

    active = active_screw(frame)
    set_driver(occurrences, active, assembly_offset)

    for index in (1, 2, 3, 4, 15):
        restore_component_opacity(occurrences.item(index).component)
    if 84 <= frame < 108:
        set_component_opacity(occurrences.item(15).component, 0.18)
    if 132 <= frame < 180:
        set_component_opacity(occurrences.item(1).component, 0.18)
    if 240 <= frame < 276:
        set_component_opacity(occurrences.item(4).component, 0.18)
    if 312 <= frame < 456:
        set_component_opacity(occurrences.item(3).component, 0.28)
        set_component_opacity(occurrences.item(2).component, 0.42)
    if 480 <= frame < 588:
        set_component_opacity(occurrences.item(2).component, 0.20)
    if 684 <= frame < 732:
        set_component_opacity(occurrences.item(1).component, 0.18)


def run(context):
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
    for index in SCREW_INDICES:
        if occurrences.item(index).component.name != SCREW_COMPONENT_NAME:
            raise RuntimeError("Unexpected S410 screw at index " + str(index))
    if occurrences.item(TOOL_INDEX).component.name != TOOL_COMPONENT_NAME:
        raise RuntimeError("Unexpected S410 L-key at index 33")

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
                "sequence": {
                    "start_all": [28, 31, 29, 30],
                    "cross_tighten": [28, 31, 29, 30],
                    "tool_index": TOOL_INDEX,
                },
            }
        )
    )
