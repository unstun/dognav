"""Validate Lite3 base-spacer, base-screw, and short-driver animation paths."""

import adsk.core
import adsk.fusion
import json
import os


RENDERER = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-rev-c2-s410-single-through-bolt-top-nut-video/"
    "render_single_axis_fastening_video.py"
)
OUTPUT = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-rev-c2-s410-single-through-bolt-top-nut-video/"
    "lite3_base_fastener_animation_validation.json"
)
COLLISION_TOLERANCE_MM3 = 0.01


def transformed_copy(temporary, source, matrix):
    body = temporary.copy(source)
    if not temporary.transform(body, matrix):
        raise RuntimeError("Could not transform a validation body")
    return body


def intersection_volume_mm3(temporary, first, second):
    result = temporary.copy(first)
    tool = temporary.copy(second)
    if not temporary.booleanOperation(
        result,
        tool,
        adsk.fusion.BooleanTypes.IntersectionBooleanType,
    ):
        return 0.0
    return result.volume * 1000.0


def bounds_overlap(first, second):
    return not (
        first.maxPoint.x < second.minPoint.x
        or first.minPoint.x > second.maxPoint.x
        or first.maxPoint.y < second.minPoint.y
        or first.minPoint.y > second.maxPoint.y
        or first.maxPoint.z < second.minPoint.z
        or first.minPoint.z > second.maxPoint.z
    )


def validation_envelope(temporary):
    center = adsk.core.Point3D.create(-30.5, 21.5, 254.0)
    box = adsk.core.OrientedBoundingBox3D.create(
        center,
        adsk.core.Vector3D.create(1.0, 0.0, 0.0),
        adsk.core.Vector3D.create(0.0, 1.0, 0.0),
        16.0,
        5.5,
        19.0,
    )
    body = temporary.createBox(box)
    if body is None:
        raise RuntimeError("Could not create validation envelope")
    return body.boundingBox


def load_renderer():
    namespace = {
        "FRAME_LIST": [],
        "FRAME_START": 0,
        "FRAME_END": 0,
    }
    with open(RENDERER, "r", encoding="utf-8") as stream:
        source = stream.read()
    exec(compile(source, RENDERER, "exec"), namespace, namespace)
    return namespace


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    temporary = adsk.fusion.TemporaryBRepManager.get()
    helper = load_renderer()

    names = {
        helper["CARRIER_NAME"]: "carrier",
        helper["FRONT_BASE_SCREWS_NAME"]: "front_screws",
        helper["REAR_BASE_SPACERS_NAME"]: "rear_spacers",
        helper["REAR_BASE_SCREWS_NAME"]: "rear_screws",
    }
    found = {}
    for index in range(root.occurrences.count):
        occurrence = root.occurrences.item(index)
        key = names.get(occurrence.component.name)
        if key is not None:
            found[key] = occurrence
    if set(found) != set(names.values()):
        raise RuntimeError("The Lite3 base-fastener scene is incomplete")

    envelope = validation_envelope(temporary)
    excluded_names = {
        helper["FRONT_BASE_SCREWS_NAME"],
        helper["REAR_BASE_SPACERS_NAME"],
        helper["REAR_BASE_SCREWS_NAME"],
        helper["TOOL_NAME"],
    }
    robot_path = root.occurrences.item(0).fullPathName
    context = []
    for occurrence_index in range(root.allOccurrences.count):
        occurrence = root.allOccurrences.item(occurrence_index)
        component_name = occurrence.component.name
        if not occurrence.isVisible:
            continue
        if component_name in excluded_names or "D435I" in component_name.upper():
            continue
        for body_index in range(occurrence.component.bRepBodies.count):
            proxy = occurrence.bRepBodies.item(body_index)
            if not bounds_overlap(proxy.boundingBox, envelope):
                continue
            body = helper["world_body_copy"](
                temporary,
                occurrence,
                body_index,
            )
            context.append(
                {
                    "label": "%s#%d" % (occurrence.fullPathName, body_index),
                    "robot_body": occurrence.fullPathName.startswith(robot_path),
                    "body": body,
                }
            )
    if not context:
        raise RuntimeError("No validation context bodies were found")

    front_sources = [
        helper["world_body_copy"](temporary, found["front_screws"], index)
        for index in range(found["front_screws"].component.bRepBodies.count)
    ]
    rear_sources = [
        helper["world_body_copy"](temporary, found["rear_screws"], index)
        for index in range(found["rear_screws"].component.bRepBodies.count)
    ]
    spacer_sources = [
        helper["world_body_copy"](temporary, found["rear_spacers"], index)
        for index in range(found["rear_spacers"].component.bRepBodies.count)
    ]
    driver_sources = helper["create_base_driver_bodies"](temporary)

    operations = (
        (
            "front_left_m3x8",
            front_sources[0],
            helper["FRONT_BASE_AXIS_POINTS"][0],
            helper["FRONT_BASE_HEAD_POINTS"][0],
            helper["BASE_SCREW_STARTS"][0],
        ),
        (
            "front_right_m3x8",
            front_sources[1],
            helper["FRONT_BASE_AXIS_POINTS"][1],
            helper["FRONT_BASE_HEAD_POINTS"][1],
            helper["BASE_SCREW_STARTS"][1],
        ),
        (
            "rear_left_m3x12",
            rear_sources[0],
            helper["REAR_BASE_AXIS_POINTS"][0],
            helper["REAR_BASE_HEAD_POINTS"][0],
            helper["BASE_SCREW_STARTS"][2],
        ),
        (
            "rear_right_m3x12",
            rear_sources[1],
            helper["REAR_BASE_AXIS_POINTS"][1],
            helper["REAR_BASE_HEAD_POINTS"][1],
            helper["BASE_SCREW_STARTS"][3],
        ),
    )
    report = {
        "document": application.activeDocument.name,
        "context_body_count": len(context),
        "operations": {},
        "rear_spacers": [],
        "tolerance_mm3": COLLISION_TOLERANCE_MM3,
        "receiver_engagement_is_not_a_clearance_claim": True,
    }
    maximum_collision = 0.0
    for label, source, axis_point, head_point, start in operations:
        rows = []
        for local_frame in (0, 4, 8, 14, 20, 26, 31, 35):
            frame = start + local_frame
            (
                _screw_visible,
                screw_offset,
                screw_angle,
                driver_visible,
                driver_approach,
            ) = helper["base_screw_state"](frame, start)
            screw = transformed_copy(
                temporary,
                source,
                helper["base_axis_transform"](
                    axis_point,
                    screw_angle,
                    screw_offset,
                ),
            )
            screw_hits = []
            receiver_engagements = []
            driver_hits = []
            for candidate in context:
                if bounds_overlap(screw.boundingBox, candidate["body"].boundingBox):
                    volume = intersection_volume_mm3(
                        temporary,
                        screw,
                        candidate["body"],
                    )
                    maximum_collision = max(maximum_collision, volume)
                    if volume > COLLISION_TOLERANCE_MM3:
                        row = {
                            "body": candidate["label"],
                            "volume_mm3": volume,
                        }
                        if candidate["robot_body"]:
                            receiver_engagements.append(row)
                        else:
                            screw_hits.append(row)
            if driver_visible:
                driver_matrix = helper["base_driver_transform"](
                    head_point,
                    screw_angle,
                    driver_approach,
                )
                for driver_index, driver_source in enumerate(driver_sources):
                    driver = transformed_copy(
                        temporary,
                        driver_source,
                        driver_matrix,
                    )
                    for candidate in context:
                        if not bounds_overlap(
                            driver.boundingBox,
                            candidate["body"].boundingBox,
                        ):
                            continue
                        volume = intersection_volume_mm3(
                            temporary,
                            driver,
                            candidate["body"],
                        )
                        maximum_collision = max(maximum_collision, volume)
                        if volume > COLLISION_TOLERANCE_MM3:
                            driver_hits.append(
                                {
                                    "driver_body": driver_index,
                                    "body": candidate["label"],
                                    "volume_mm3": volume,
                                }
                            )
            rows.append(
                {
                    "frame": frame,
                    "screw_offset_mm": screw_offset * 10.0,
                    "driver_visible": driver_visible,
                    "screw_hits": screw_hits,
                    "receiver_engagements": receiver_engagements,
                    "driver_hits": driver_hits,
                }
            )
        report["operations"][label] = rows

    for frame in (helper["REAR_SPACER_START"], 305, helper["REAR_SPACER_END"]):
        _visible, offset = helper["rear_spacer_state"](frame)
        matrix = helper["translation_matrix"]((0.0, offset, 0.0))
        hits = []
        for spacer_index, source in enumerate(spacer_sources):
            spacer = transformed_copy(temporary, source, matrix)
            for candidate in context:
                if not candidate["robot_body"]:
                    continue
                if not bounds_overlap(spacer.boundingBox, candidate["body"].boundingBox):
                    continue
                volume = intersection_volume_mm3(
                    temporary,
                    spacer,
                    candidate["body"],
                )
                maximum_collision = max(maximum_collision, volume)
                if volume > COLLISION_TOLERANCE_MM3:
                    hits.append(
                        {
                            "spacer_body": spacer_index,
                            "body": candidate["label"],
                            "volume_mm3": volume,
                        }
                    )
        report["rear_spacers"].append(
            {"frame": frame, "offset_mm": offset * 10.0, "hits": hits}
        )

    all_rows = [
        row
        for operation_rows in report["operations"].values()
        for row in operation_rows
    ]
    report["maximum_positive_volume_collision_mm3"] = maximum_collision
    report["checks"] = {
        "screw_paths_clear": all(not row["screw_hits"] for row in all_rows),
        "driver_sweeps_clear": all(not row["driver_hits"] for row in all_rows),
        "rear_spacer_paths_clear": all(
            not row["hits"] for row in report["rear_spacers"]
        ),
    }
    report["passed"] = all(report["checks"].values())
    with open(OUTPUT, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False))
