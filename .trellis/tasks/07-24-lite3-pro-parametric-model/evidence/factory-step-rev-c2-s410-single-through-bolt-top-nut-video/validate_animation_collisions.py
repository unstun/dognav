"""Validate sampled bolt, nut, and L-key animation states for positive-volume collisions."""

import adsk.core
import adsk.fusion
import json
import os


globals().pop("run", None)


RENDERER = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-rev-c2-s410-single-through-bolt-top-nut-video/"
    "render_single_axis_fastening_video.py"
)
exec(
    compile(open(RENDERER, "r", encoding="utf-8").read(), RENDERER, "exec"),
    globals(),
    globals(),
)

REPORT_PATH = os.path.join(OUTPUT_ROOT, "animation_collision_validation.json")
VALIDATE_PERSISTENT_FINAL = globals().get("VALIDATE_PERSISTENT_FINAL", True)


def transformed_copy(temporary, body, matrix):
    result = temporary.copy(body)
    if not temporary.transform(result, matrix):
        raise RuntimeError("Could not transform validation body")
    return result


def world_copy(temporary, occurrence, body_index=0):
    return transformed_copy(
        temporary,
        occurrence.component.bRepBodies.item(body_index),
        occurrence.transform2,
    )


def intersection_volume_mm3(temporary, first, second):
    target = temporary.copy(first)
    tool = temporary.copy(second)
    if not temporary.booleanOperation(
        target,
        tool,
        adsk.fusion.BooleanTypes.IntersectionBooleanType,
    ):
        return 0.0
    return target.volume * 1000.0


def intersection_volume_against_bodies_mm3(temporary, moving_body, fixed_bodies):
    total = 0.0
    moving_bounds = moving_body.boundingBox
    for fixed_body in fixed_bodies:
        if not bounding_boxes_overlap(moving_bounds, fixed_body.boundingBox):
            continue
        total += intersection_volume_mm3(temporary, moving_body, fixed_body)
    return total


def persistent_interference_mm3(design, first, second):
    if not bounding_boxes_overlap(first.boundingBox, second.boundingBox):
        return 0.0
    entities = adsk.core.ObjectCollection.create()
    entities.add(first)
    entities.add(second)
    results = design.analyzeInterference(design.createInterferenceInput(entities))
    return sum(
        results.item(index).interferenceBody.volume * 1000.0
        for index in range(results.count)
    )


def nested_robot_proxy_bodies(root, robot):
    bodies = []
    robot_path = robot.fullPathName
    for occurrence_index in range(root.allOccurrences.count):
        occurrence = root.allOccurrences.item(occurrence_index)
        if not occurrence.fullPathName.startswith(robot_path):
            continue
        for body_index in range(occurrence.bRepBodies.count):
            bodies.append(occurrence.bRepBodies.item(body_index))
    return bodies


def create_lite3_collision_context_bodies(root, temporary, robot):
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
        raise RuntimeError("Could not create the Lite3 collision envelope")
    clip_bounds = clip_body.boundingBox
    bodies = []
    robot_path = robot.fullPathName
    for occurrence_index in range(root.allOccurrences.count):
        occurrence = root.allOccurrences.item(occurrence_index)
        if not occurrence.fullPathName.startswith(robot_path):
            continue
        for body_index in range(occurrence.component.bRepBodies.count):
            proxy_body = occurrence.bRepBodies.item(body_index)
            if not bounding_boxes_overlap(proxy_body.boundingBox, clip_bounds):
                continue
            bodies.append(world_copy(temporary, occurrence, body_index))
    if not bodies:
        raise RuntimeError("The Lite3 collision envelope contains no bodies")
    return bodies


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    occurrences = design.rootComponent.occurrences
    root = design.rootComponent
    os.makedirs(OUTPUT_ROOT, exist_ok=True)

    found = {}
    guard = None
    official_guard = None
    robot = None
    for index in range(occurrences.count):
        occurrence = occurrences.item(index)
        name = occurrence.component.name
        if index == 0 and "Lite3" in name:
            robot = occurrence
        if name == CARRIER_NAME:
            found["carrier"] = occurrence
        elif name == BOLT_NAME:
            found["bolt"] = occurrence
        elif name == NUT_NAME:
            found["nut"] = occurrence
        elif name == TOOL_NAME:
            found["tool"] = occurrence
        elif name == GUARD_ACCESS_CANDIDATE_NAME:
            guard = occurrence
        elif index == 3 and "S410" in name:
            official_guard = occurrence
    if guard is None:
        guard = official_guard
    if (
        set(found) != {"carrier", "bolt", "nut", "tool"}
        or guard is None
        or robot is None
    ):
        raise RuntimeError("Animation validation scene is incomplete")

    temporary = adsk.fusion.TemporaryBRepManager.get()
    carrier_world = world_copy(temporary, found["carrier"])
    guard_world = world_copy(temporary, guard)
    bolt_source = world_copy(temporary, found["bolt"])
    nut_source = world_copy(temporary, found["nut"])
    tool_sources = [
        temporary.copy(found["tool"].component.bRepBodies.item(body_index))
        for body_index in range(found["tool"].component.bRepBodies.count)
    ]
    lite3_mount_bodies = create_lite3_collision_context_bodies(
        root, temporary, robot
    )
    robot_proxy_bodies = nested_robot_proxy_bodies(root, robot)
    final_robot_interference_mm3 = {
        "carrier": 0.0,
        "guard": 0.0,
        "bolt": 0.0,
        "nut": 0.0,
    }
    final_robot_interference_hits = {
        "carrier": 0,
        "guard": 0,
        "bolt": 0,
        "nut": 0,
    }
    if VALIDATE_PERSISTENT_FINAL:
        for name, occurrence in (
            ("carrier", found["carrier"]),
            ("guard", guard),
            ("bolt", found["bolt"]),
            ("nut", found["nut"]),
        ):
            for source_body in occurrence.bRepBodies:
                for robot_body in robot_proxy_bodies:
                    volume = persistent_interference_mm3(
                        design, source_body, robot_body
                    )
                    final_robot_interference_mm3[name] += volume
                    if volume > 0.01:
                        final_robot_interference_hits[name] += 1

    sampled_frames = sorted(
        set(
            [0, 23, 36, 60, 89, 90, 131, 132, 160, 185, 186, 221]
            + list(range(222, 294, 3))
            + [293, 294, 305, 317, 318, 329, 340, 347]
        )
    )
    records = []
    max_collisions = {
        "bolt_vs_carrier": 0.0,
        "bolt_vs_guard": 0.0,
        "bolt_vs_lite3_context": 0.0,
        "nut_vs_carrier": 0.0,
        "nut_vs_guard": 0.0,
        "nut_vs_lite3_context": 0.0,
        "tool_vs_carrier": 0.0,
        "tool_vs_guard": 0.0,
        "tool_vs_lite3_context": 0.0,
        "carrier_vs_lite3_context": 0.0,
        "guard_vs_lite3_context": 0.0,
    }
    max_collision_frames = {key: None for key in max_collisions}
    tool_body_guard_maximums_mm3 = [0.0 for _ in tool_sources]
    tool_body_guard_maximum_frames = [None for _ in tool_sources]

    for frame in sampled_frames:
        bolt_offset, bolt_angle = bolt_state(frame)
        nut_offset, nut_angle = nut_state(frame)
        current_assembly_offset = assembly_offset(frame)
        current_assembly_matrix = translation_matrix(current_assembly_offset)
        carrier_body = transformed_copy(
            temporary, carrier_world, current_assembly_matrix
        )
        guard_body = transformed_copy(
            temporary, guard_world, current_assembly_matrix
        )
        bolt_body = transformed_copy(
            temporary,
            bolt_source,
            translated_matrix(
                axis_transform(bolt_angle, bolt_offset),
                current_assembly_offset,
            ),
        )
        nut_body = transformed_copy(
            temporary,
            nut_source,
            translated_matrix(
                axis_transform(nut_angle, nut_offset),
                current_assembly_offset,
            ),
        )
        carrier_lite3_collision = 0.0
        guard_lite3_collision = 0.0
        if frame < STACK_MOUNT_END:
            carrier_lite3_collision = (
                intersection_volume_against_bodies_mm3(
                    temporary, carrier_body, lite3_mount_bodies
                )
            )
            guard_lite3_collision = (
                intersection_volume_against_bodies_mm3(
                    temporary, guard_body, lite3_mount_bodies
                )
            )
        bolt_lite3_collision = 0.0
        nut_lite3_collision = 0.0
        if frame < STACK_MOUNT_START:
            bolt_lite3_collision = intersection_volume_against_bodies_mm3(
                temporary, bolt_body, lite3_mount_bodies
            )
            nut_lite3_collision = intersection_volume_against_bodies_mm3(
                temporary, nut_body, lite3_mount_bodies
            )
        values = {
            "bolt_vs_carrier": intersection_volume_mm3(
                temporary, bolt_body, carrier_body
            ),
            "bolt_vs_guard": intersection_volume_mm3(
                temporary, bolt_body, guard_body
            ),
            "bolt_vs_lite3_context": bolt_lite3_collision,
            "nut_vs_carrier": intersection_volume_mm3(
                temporary, nut_body, carrier_body
            ),
            "nut_vs_guard": intersection_volume_mm3(
                temporary, nut_body, guard_body
            ),
            "nut_vs_lite3_context": nut_lite3_collision,
            "tool_vs_carrier": 0.0,
            "tool_vs_guard": 0.0,
            "tool_vs_lite3_context": 0.0,
            "carrier_vs_lite3_context": carrier_lite3_collision,
            "guard_vs_lite3_context": guard_lite3_collision,
        }
        tool_visible, tool_angle, tool_approach = tool_state(frame, bolt_offset)
        if tool_visible:
            current_tool_transform = translated_matrix(
                tool_transform(tool_angle, bolt_offset, tool_approach),
                current_assembly_offset,
            )
            for tool_index, tool_source in enumerate(tool_sources):
                tool_body = transformed_copy(
                    temporary,
                    tool_source,
                    current_tool_transform,
                )
                values["tool_vs_carrier"] += intersection_volume_mm3(
                    temporary, tool_body, carrier_body
                )
                guard_collision = intersection_volume_mm3(
                    temporary, tool_body, guard_body
                )
                values["tool_vs_guard"] += guard_collision
                if guard_collision > tool_body_guard_maximums_mm3[tool_index]:
                    tool_body_guard_maximums_mm3[tool_index] = guard_collision
                    tool_body_guard_maximum_frames[tool_index] = frame
                values["tool_vs_lite3_context"] += (
                    intersection_volume_against_bodies_mm3(
                        temporary, tool_body, lite3_mount_bodies
                    )
                )

        for key, value in values.items():
            if value > max_collisions[key]:
                max_collisions[key] = value
                max_collision_frames[key] = frame
        records.append(
            {
                "frame": frame,
                "bolt_offset_mm": bolt_offset * 10.0,
                "nut_offset_mm": nut_offset * 10.0,
                "tool_visible": tool_visible,
                "preassembly_standoff_mm": projected(
                    current_assembly_offset, MOUNT_NORMAL
                )
                * 10.0,
                "collisions_mm3": values,
            }
        )

    tolerance_mm3 = 0.01
    checks = {
        "bolt_path_clear": max_collisions["bolt_vs_carrier"] <= tolerance_mm3
        and max_collisions["bolt_vs_guard"] <= tolerance_mm3
        and max_collisions["bolt_vs_lite3_context"] <= tolerance_mm3,
        "nut_path_clear": max_collisions["nut_vs_carrier"] <= tolerance_mm3
        and max_collisions["nut_vs_guard"] <= tolerance_mm3
        and max_collisions["nut_vs_lite3_context"] <= tolerance_mm3,
        "tool_path_clear": max_collisions["tool_vs_carrier"] <= tolerance_mm3
        and max_collisions["tool_vs_guard"] <= tolerance_mm3
        and max_collisions["tool_vs_lite3_context"] <= tolerance_mm3,
        "lite3_context_path_clear": all(
            max_collisions[key] <= tolerance_mm3
            for key in (
                "bolt_vs_lite3_context",
                "nut_vs_lite3_context",
                "tool_vs_lite3_context",
                "carrier_vs_lite3_context",
                "guard_vs_lite3_context",
            )
        ),
        "mounting_path_clear": max_collisions["carrier_vs_lite3_context"]
        <= tolerance_mm3
        and max_collisions["guard_vs_lite3_context"] <= tolerance_mm3
        and VALIDATE_PERSISTENT_FINAL
        and all(
            value <= tolerance_mm3
            for value in final_robot_interference_mm3.values()
        ),
        "bolt_final_offset_zero": abs(bolt_state(STACK_MOUNT_END)[0]) <= 1.0e-12,
        "nut_final_offset_zero": abs(nut_state(STACK_MOUNT_END)[0]) <= 1.0e-12,
        "four_regrip_strokes": all(
            not tool_state(frame, bolt_state(frame)[0])[0]
            for frame in (247, 262, 277, 292)
        ),
    }
    report = {
        "stage": "experiment_and_analysis",
        "status": "passed" if all(checks.values()) else "failed",
        "sampled_frame_count": len(sampled_frames),
        "lite3_context_body_count": len(lite3_mount_bodies),
        "sampled_frames": sampled_frames,
        "checks": checks,
        "maximum_collision_volumes_mm3": max_collisions,
        "maximum_collision_frames": max_collision_frames,
        "tool_body_guard_maximums_mm3": tool_body_guard_maximums_mm3,
        "tool_body_guard_maximum_frames": tool_body_guard_maximum_frames,
        "final_robot_interference_mm3": final_robot_interference_mm3,
        "final_robot_interference_hits": final_robot_interference_hits,
        "robot_proxy_body_count": len(robot_proxy_bodies),
        "persistent_final_checked": VALIDATE_PERSISTENT_FINAL,
        "collision_tolerance_mm3": tolerance_mm3,
        "records": records,
        "claim_boundary": (
            "Sampled CAD positive-volume collision validation only; tool ergonomics, "
            "torque, print tolerance, strength, and real-hardware safety remain unvalidated."
        ),
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "checks": checks,
                "maximum_collision_volumes_mm3": max_collisions,
                "maximum_collision_frames": max_collision_frames,
                "report": REPORT_PATH,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
