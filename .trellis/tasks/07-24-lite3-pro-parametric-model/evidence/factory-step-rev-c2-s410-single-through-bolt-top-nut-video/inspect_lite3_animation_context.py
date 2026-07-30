"""Inventory the active final scene before keeping Lite3 visible in the detail animation."""

import adsk.core
import adsk.fusion
import json
import os


globals().pop("run", None)


OUTPUT_PATH = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-rev-c2-s410-single-through-bolt-top-nut-video/"
    "lite3_animation_context_inventory.json"
)


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences
    robot = occurrences.item(0)
    robot_path = robot.fullPathName
    nested = []
    for index in range(root.allOccurrences.count):
        occurrence = root.allOccurrences.item(index)
        if not occurrence.fullPathName.startswith(robot_path):
            continue
        nested.append(
            {
                "full_path": occurrence.fullPathName,
                "component": occurrence.component.name,
                "direct_brep_bodies": occurrence.bRepBodies.count,
                "direct_mesh_bodies": occurrence.component.meshBodies.count,
                "is_visible": occurrence.isVisible,
            }
        )
    report = {
        "document": application.activeDocument.name,
        "root_occurrence_count": occurrences.count,
        "robot_root_index": 0,
        "robot_root_name": robot.name,
        "robot_component_name": robot.component.name,
        "robot_full_path": robot_path,
        "robot_direct_brep_bodies": robot.bRepBodies.count,
        "robot_child_occurrences": robot.childOccurrences.count,
        "robot_nested_occurrence_count": len(nested),
        "final_visible_root_occurrences": [
            {
                "index": index,
                "name": occurrences.item(index).name,
                "component": occurrences.item(index).component.name,
            }
            for index in range(occurrences.count)
            if occurrences.item(index).isLightBulbOn
        ],
        "robot_nested_occurrences": nested,
    }
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(
        json.dumps(
            {
                "robot_root_name": report["robot_root_name"],
                "robot_component_name": report["robot_component_name"],
                "robot_nested_occurrence_count": report[
                    "robot_nested_occurrence_count"
                ],
                "final_visible_root_occurrences": report[
                    "final_visible_root_occurrences"
                ],
                "report": OUTPUT_PATH,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
