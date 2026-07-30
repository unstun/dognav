"""Identify the exact Lite3 nested bodies hit by the animated fastener/tool."""

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

REPORT_PATH = os.path.join(OUTPUT_ROOT, "lite3_path_collision_diagnosis.json")
TOLERANCE_MM3 = 0.01


def transformed_copy(temporary, body, matrix):
    result = temporary.copy(body)
    if not temporary.transform(result, matrix):
        raise RuntimeError("Could not transform diagnostic body")
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


def collisions_for_body(root, temporary, robot, moving_body):
    collisions = []
    moving_bounds = moving_body.boundingBox
    robot_path = robot.fullPathName
    for occurrence_index in range(root.allOccurrences.count):
        occurrence = root.allOccurrences.item(occurrence_index)
        if not occurrence.fullPathName.startswith(robot_path):
            continue
        for body_index in range(occurrence.component.bRepBodies.count):
            proxy_body = occurrence.bRepBodies.item(body_index)
            if not bounding_boxes_overlap(moving_bounds, proxy_body.boundingBox):
                continue
            fixed_body = world_copy(temporary, occurrence, body_index)
            volume = intersection_volume_mm3(
                temporary, moving_body, fixed_body
            )
            if volume <= TOLERANCE_MM3:
                continue
            collisions.append(
                {
                    "volume_mm3": volume,
                    "occurrence_index": occurrence_index,
                    "full_path": occurrence.fullPathName,
                    "component": occurrence.component.name,
                    "body_index": body_index,
                    "body_name": occurrence.component.bRepBodies.item(
                        body_index
                    ).name,
                }
            )
    return sorted(
        collisions, key=lambda item: item["volume_mm3"], reverse=True
    )


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences
    robot = occurrences.item(0)
    found = {}
    for index in range(occurrences.count):
        occurrence = occurrences.item(index)
        if occurrence.component.name == BOLT_NAME:
            found["bolt"] = occurrence
        elif occurrence.component.name == TOOL_NAME:
            found["tool"] = occurrence
    if "Lite3" not in robot.component.name or set(found) != {"bolt", "tool"}:
        raise RuntimeError("Lite3 collision diagnosis scene is incomplete")

    temporary = adsk.fusion.TemporaryBRepManager.get()
    bolt_source = world_copy(temporary, found["bolt"])
    states = []
    for frame in (36, 48, 60, 72, 89, 234, 249, 264, 279, 288):
        bolt_offset, bolt_angle = bolt_state(frame)
        bolt_body = transformed_copy(
            temporary, bolt_source, axis_transform(bolt_angle, bolt_offset)
        )
        bolt_hits = collisions_for_body(
            root, temporary, robot, bolt_body
        )

        tool_visible, tool_angle, tool_approach = tool_state(
            frame, bolt_offset
        )
        tool_hits = []
        if tool_visible:
            current_tool_transform = tool_transform(
                tool_angle, bolt_offset, tool_approach
            )
            for body_index in range(found["tool"].component.bRepBodies.count):
                tool_body = transformed_copy(
                    temporary,
                    found["tool"].component.bRepBodies.item(body_index),
                    current_tool_transform,
                )
                for hit in collisions_for_body(
                    root, temporary, robot, tool_body
                ):
                    hit["tool_body_index"] = body_index
                    tool_hits.append(hit)
            tool_hits.sort(
                key=lambda item: item["volume_mm3"], reverse=True
            )

        states.append(
            {
                "frame": frame,
                "bolt_offset_mm": bolt_offset * 10.0,
                "tool_visible": tool_visible,
                "bolt_hits": bolt_hits,
                "tool_hits": tool_hits,
            }
        )

    report = {
        "stage": "experiment_and_analysis",
        "status": "diagnosed",
        "collision_tolerance_mm3": TOLERANCE_MM3,
        "states": states,
        "claim_boundary": (
            "Names the Lite3 CAD bodies intersected by sampled animation states; "
            "it does not validate hand access or real-hardware safety."
        ),
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "states": [
                    {
                        "frame": item["frame"],
                        "bolt_hit_count": len(item["bolt_hits"]),
                        "tool_hit_count": len(item["tool_hits"]),
                        "top_bolt_hit": (
                            item["bolt_hits"][0]
                            if item["bolt_hits"]
                            else None
                        ),
                        "top_tool_hit": (
                            item["tool_hits"][0]
                            if item["tool_hits"]
                            else None
                        ),
                    }
                    for item in states
                ],
                "report": REPORT_PATH,
            },
            ensure_ascii=False,
            indent=2,
        )
    )

