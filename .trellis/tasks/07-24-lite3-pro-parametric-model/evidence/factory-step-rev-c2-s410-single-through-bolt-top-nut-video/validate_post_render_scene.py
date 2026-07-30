"""Verify that the Fusion scene was restored after the complete video render."""

import adsk.core
import adsk.fusion
import json
import os


OUTPUT = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-rev-c2-s410-single-through-bolt-top-nut-video/"
    "post_render_scene_validation.json"
)
FULL_DEPTH_GUARD = (
    "S410_GUARD_FRONT_BASE_2X_M3_FULL_DEPTH_ACCESS_HOLES_7MM_"
    "VISUAL_PRINT_CANDIDATE_NOT_OFFICIAL_CAD"
)
PRELIMINARY_GUARD_PREFIX = (
    "S410_GUARD_FRONT_BASE_2X_M3_ACCESS_HOLES_7MM_"
)
REQUIRED_VISIBLE = {
    "BASE_TO_LITE3_FRONT_2X_M3X8_SOCKET_HEAD_SCREWS_REAL_BREP",
    "BASE_TO_LITE3_REAR_2X_OD8_ID3P5_LOCATING_SPACERS_REAL_BREP",
    "BASE_TO_LITE3_REAR_2X_M3X12_SOCKET_HEAD_SCREWS_REAL_BREP",
    "J17A_J20A_REV_C2_S410_SINGLE_THROUGH_HOLE_HEAD_ACCESS_PREVIEW_NOT_OFFICIAL_CAD",
    "S410_S1_M5X14_BOTTOM_UP_BOLT_HEAD_ACCESS_PREVIEW",
    "S410_S1_M5_TOP_HEX_NUT_HEAD_ACCESS_PREVIEW",
    FULL_DEPTH_GUARD,
}


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    visibility = {}
    for index in range(root.occurrences.count):
        occurrence = root.occurrences.item(index)
        visibility[occurrence.component.name] = {
            "index": index,
            "visible": bool(occurrence.isLightBulbOn),
        }

    required_visible = {
        name: visibility.get(name, {"index": None, "visible": False})
        for name in sorted(REQUIRED_VISIBLE)
    }
    official_guard_hidden = not root.occurrences.item(3).isLightBulbOn
    preliminary_hidden = all(
        not row["visible"]
        for name, row in visibility.items()
        if name.startswith(PRELIMINARY_GUARD_PREFIX)
    )
    d435_visible = any(
        row["visible"]
        for name, row in visibility.items()
        if "D435I_REAL_BREP" in name.upper()
    )
    checks = {
        "no_custom_graphics_groups": root.customGraphicsGroups.count == 0,
        "required_final_roots_visible": all(
            row["visible"] for row in required_visible.values()
        ),
        "official_guard_preserved_hidden": official_guard_hidden,
        "preliminary_guard_candidate_hidden": preliminary_hidden,
        "full_depth_guard_candidate_visible": visibility.get(
            FULL_DEPTH_GUARD,
            {"visible": False},
        )["visible"],
        "d435i_restored_visible": d435_visible,
    }
    report = {
        "document": application.activeDocument.name,
        "root_occurrence_count": root.occurrences.count,
        "custom_graphics_group_count": root.customGraphicsGroups.count,
        "required_visible": required_visible,
        "checks": checks,
        "passed": all(checks.values()),
        "document_modified_unsaved": bool(application.activeDocument.isModified),
    }
    with open(OUTPUT, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False))

